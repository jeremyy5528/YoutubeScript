""" grobid script to convert PDFs to XML files. """
from grobid_client.grobid_client import GrobidClient
import os
import json
import re
from sentence_transformers import SentenceTransformer, util
import logging
from xml.dom.minidom import parseString
from xml.etree.ElementTree import ElementTree, fromstring
# Create a custom logger
logger = logging.getLogger(__name__)

# Set level of logger
logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('file.log')
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.ERROR)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

def check_pdf_quality(output_path, target):
    paper_info = target
    file_path = f"{output_path}/{paper_info.save_title}.pdf"
    def delete_corrupted_files(file_path):
        """
        Deletes corrupted PDF files from the specified directory.
    
        Args:
            directory_path (str, optional): The path to the directory containing the PDF files. Defaults to "/data/parser_need/academic/pdf".
        """
    
        def delete_files_smaller_than_nkb(file_path, n=3):
            """Delete files smaller than n kilobytes in the specified directory.
    
            Args:
                directory_path (str): The path to the directory. Defaults to "/data/parser_need/academic/pdf".
                n (int): The size threshold in kilobytes. Defaults to 3.
            """
            file = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            # If the file size is smaller than n kilobytes, delete the file
            if file.endswith(".pdf") and file_size < n * 1024:
                os.remove(file_path)
    
        def delete_eof_files(file_path):
            """
            Deletes corrupted PDF files from the specified directory.
    
            Args:
                directory_path (str, optional): The path to the directory containing the PDF files.
            """
    
            def check_pdf_eof(file_path):
                """
                Check if a PDF file ends with the %%EOF marker.
    
                Args:
                    file_path (str): The path to the PDF file.
    
                Returns:
                    bool: True if the PDF file ends with the %%EOF marker, False otherwise.
                """
    
                try:
                    with open(file_path, "rb") as file:
                        file.seek(-5, os.SEEK_END)  # Move to the last 5 bytes of the file
                        end = file.read().decode("utf-8", errors="ignore")  # Read the last few bytes
                        return "EOF" in end  # Check if it contains the %%EOF marker
                except Exception as e:
                    logger.info(f"Error checking file {file_path}: {e}")
                    return False
            if not check_pdf_eof(file_path):
                os.remove(file_path)
    
        delete_files_smaller_than_nkb(file_path=file_path, n=3)
        delete_eof_files(file_path=file_path)
        return
    delete_corrupted_files(file_path)

def parse_pdf_to_xml(
    service = "processHeaderDocument",
    config_path="/RAG_workflow/parser/grobid/config.json",
    pdf_file="/data/parser_need/academic/pdf"
    ):
    """Main function to convert PDFs to XML."""
    logger.info(f'Entering function: parse_pdf_to_xml')
    client = GrobidClient(config_path=config_path)
    pdf_file_path,status,xml_tei_output = client.process_pdf(service = service,
                    pdf_file = pdf_file,
                    generateIDs = True,
                    consolidate_header = True,
                    consolidate_citations = True,
                    include_raw_citations = True,
                    include_raw_affiliations = True,
                    tei_coordinates = True,
                    segment_sentences = True)
    if status == 200:
        return  fromstring(xml_tei_output)
    if status != 200:
        logger.error(f'parse failed, status code: {status}')

def determine_article_type(title, metadata):
    """return article type from metadata

    Args:
        title (_type_): _description_
        metadata (_type_): _description_

    Returns:
        _type_: _description_
    """
    save_title = re.sub(r'[\\/*?:"<>|]', "", title)
    output_name = f"output/{save_title}.pdf"
    matching_rows = metadata[metadata["file_title"] == output_name]
    if matching_rows["subtype"].str.contains("re").any():
        return "review article"
    else:
        return "other"

def parse_grobid_xml_to_json(xml_content,article_type,service):
    """parse_grobid_fulltext_xml_to_json

    Args:
        xml_content (_type_): _description_

    Returns:
        _type_: _description_
    """
    def extract_text(node):
        try:
            return "".join(node.itertext()).strip()
        except AttributeError:
            logging.error("'NoneType' error encountered when processing node: %s", node)
            return ""
    def classify_title(article_type, title):
        """classify title to a fix class
        Args:
            article_type (_type_):
            title (_type_): _description_

        Returns:
            _type_: _description_
        """
        # 提取文本的方法
        if article_type == "review article":
            return "H1"
        
        model = SentenceTransformer('paraphrase-MiniLM-L6-v2', device='cuda')
        # 使用 glob.glob 获取所有匹配的文件
        title_embedding = model.encode(title, convert_to_tensor=True)
        # 定義參考標題
        reference_titles = [
            "Introduction",
            "Material",
            "Methods",
            "Material and Method",
            "Results",
            "Discussion",
            "Results and Discussion",
            "Conclusion",
        ]

        # 計算參考標題的embeddings
        reference_embeddings = model.encode(reference_titles, convert_to_tensor=True)
        # 計算與參考標題的cosine相似度
        similarities = [
            util.pytorch_cos_sim(title_embedding, ref_emb).item()
            for ref_emb in reference_embeddings
        ]

        # 檢查是否有任何相似度超過某個閾值，例如0.7，以確定是否為H1
        if any(sim > 0.7 for sim in similarities):
            return "H1"
        else:
            return "H2"
    def extract_paragraph_without_ref(element):
        result = ""
        for child in element:
            if child.tag != "{http://www.tei-c.org/ns/1.0}ref":
                result += (child.text or "")
        return result
    tree = ElementTree(xml_content)
    # 使用xml.etree.ElementTree解析XML
    root = tree.getroot()
    # 定義命名空間
    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    if service == 'processFulltextDocument':
        divs = root.findall(".//tei:body/tei:div", namespaces=namespaces)
        sections = []
        current_h1 = ""
        for div in divs:
            head = extract_text(div.find("tei:head", namespaces=namespaces))
            paragraphs = []
            for p in div.findall("tei:p", namespaces=namespaces):
                paragraphs.append(extract_paragraph_without_ref(p))

            # 如果是主标题
            if classify_title(article_type, head) == "H1":
                current_h1 = head
                sections.append(
                    {"H1": current_h1, "H2": "", "paragraphs": paragraphs}  # 设置为空
                )
            else:  # 如果是子标题
                sections.append({"H1": current_h1, "H2": head, "paragraphs": paragraphs})

                
            # 建立JSON数据结构
            data = {
                "sections": sections
            }
    
    if service == 'processHeaderDocument':
        
        abstract = extract_text(root.find(".//tei:abstract", namespaces=namespaces))
        keywords = [
            extract_text(kw)
            for kw in root.findall(".//tei:keywords", namespaces=namespaces)
        ]
        
        # 建立JSON数据结构
        data = {
            "abstract": abstract,
            "keywords": keywords,
        }

    return data
    
def determine_article_type(title):
    """return article type from metadata

    Args:
        title (str): Title of the article

    Returns:
        str: Type of the article
    """
    
    if ":" in title:
        return "review article"
    if "review" in title:
        return "review article"
    if "survey" in title:
        return "review article"
    if "meta analysis" in title:
        return "review article"
    if "overview" in title:
        return "review article"
    else:
        return "article"
    
def service_pdf(config_path,pdf_file,article_type,service):
    xml_content = parse_pdf_to_xml(service,config_path,pdf_file)
    logger.debug(f'Entering function: parse_pdf')
    json_content = parse_grobid_xml_to_json(xml_content,article_type,service)  
    return json_content

def get_title(config_path,pdf_file):
    # Parse the XML content to an ElementTree object
    service = "processHeaderDocument"
    xml_content = parse_pdf_to_xml(service,config_path,pdf_file)
    tree = ElementTree(xml_content)
    # Define the namespace
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    # Find the title element
    title_elem = tree.find('.//tei:title', ns)
    # Get the title text
    title = title_elem.text if title_elem is not None else None
    return str(title)

def parse_pdf(pdf_file):
    config_path = "C:\RAG\grobid_client_python\config.json"
    title = get_title(config_path,pdf_file)
    article_type = determine_article_type(title)
    abstract_data = service_pdf(config_path,pdf_file,article_type,service = "processHeaderDocument")
    fulltext_data = service_pdf(config_path,pdf_file,article_type,service = "processFulltextDocument")
    title = {"title" : title}
    parsed_data = {**title, **abstract_data,**fulltext_data}
    return parsed_data

