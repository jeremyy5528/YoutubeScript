import unicodedata
from docx import Document
from tqdm import tqdm
import json
import os
import tempfile
import subprocess
import argparse
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from io import StringIO
import ollama
import sys
import chardet
import re
import requests
import glob
from STT_module import audio_language, faster_whisper_transcribe_vtt
from TTS_module import generate_audio_openvoice
from vtt_to_doc import vtt_to_file
from logger import logger
from auxiliary_function import chunk_string_by_words
import webvtt

def clean_vtt(filepath: str) -> str:
    """Clean up the content of a subtitle file (vtt) to a string

    Args:
        filepath (str): path to vtt file

    Returns:
        str: clean content
    """
    # Read the VTT file
    captions = webvtt.read(filepath)

    # Extract the text from each caption
    lines = [caption.text for caption in captions]

    # Join the lines into a single string
    content = " ".join(lines)

    # Remove duplicate spaces
    pattern = r"\s+"
    content = re.sub(pattern, r" ", content)

    # Add space after punctuation marks if it doesn't exist
    pattern = r"([\.!?])(\w)"
    content = re.sub(pattern, r"\1 \2", content)

    return content


def playlist_urls(url):
    """Get a list of video URLs from a YouTube playlist.

    Args:
        url (str): The URL of the YouTube playlist.

    Returns:
        list: A list of video URLs from the playlist.
    """
    if "playlist?list=" not in url:
        urls = url
        return urls  # Single video
    response = requests.get(url)  # Get the webpage source code
    if response.status_code != 200:
        logger.info("Request failed")
        return
    urls = []
    response = requests.get(url)
    # Store the HTML content in a variable
    html_content = response.text

    # Use regular expressions to find all JSON objects
    json_objects = re.findall(r"\{.*?\}", html_content)
    # For each JSON object
    for json_object in json_objects:
        # Try to parse the JSON
        try:
            data = json.loads(json_object)
        except json.JSONDecodeError:
            continue

        # If the JSON contains a 'videoIds' key
        if "videoIds" in data:
            # Append the video URL to the list
            urls.append("https://www.youtube.com/watch?v=" + data["videoIds"][0])
    return urls


def parse_xml(url):
    """
    Parses an XML file from the given URL and extracts the href values from the entry elements.

    Args:
        url (str): The URL of the XML file.

    Returns:
        list: A list of href values extracted from the entry elements in the XML file.
    """
    response = requests.get(url)
    xml_file = StringIO(response.text)

    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = {"default": "http://www.w3.org/2005/Atom"}
    entries = root.findall("default:entry", ns)

    hrefs = []
    for entry in entries:
        link = entry.find("default:link", ns)
        if link is not None:
            href = link.get("href")
            hrefs.append(href)

    return hrefs


def is_localhost(url):
    """Check if the given URL is a localhost URL.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is a localhost URL, False otherwise.
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc.startswith("localhost:")


def summary_video_from_link(
    clean_vtt,
    logger,
    args,
    link,
    post_audio_output_dir,
    integrate_text_output_dir,
    text_output_dir,
    audiopath,
):
    """
    Summarizes a video from a given link.

    Args:
        clean_vtt (function): A function to clean the VTT file.
        logger: The logger object for logging messages.
        args: The command-line arguments.
        link (str): The link to the video.
        post_audio_output_dir (str): The directory to store the generated audio.
        integrate_text_output_dir (str): The directory to store the integrated text output.
        text_output_dir (str): The directory to store the text output.
        audiopath (str): The path to the audio files.

    Returns:
        None
    """

    def find_video_file(directory, pure_filename):
        """
        Finds the video file in the specified directory with the specified filename (without extension).

        Args:
            directory (str): The directory where the files are located.
            pure_filename (str): The filename without extension.

        Returns:
            str: The filename with extension of the video file, or None if no video file is found.
        """
        # Define the video file extensions
        video_extensions = [
            ".webm",
            ".mp4",
            ".avi",
            ".mov",
            ".mkv",
            ".flv",
            ".wmv",
            ".m4a",
        ]

        # Search for the video file
        all_files = glob.glob(os.path.join(directory, f"*{pure_filename}*"))

        for file in all_files:
            filename, extension = os.path.splitext(file)
            if extension in video_extensions and not re.search(r"\.f\d{3}", filename):
                # Return the video file found
                return glob.glob(os.path.join(directory, os.path.basename(file)))[0]
        logger.error("did not donwload video yet")

    def download_subtitle_file(
        audiopath, pure_filename, video_language, text_output_dir
    ):
        vtt_file = os.path.join(audiopath, f"{pure_filename}.{video_language}.vtt")
        if os.path.exists(vtt_file):
            if not os.path.exists(os.path.join(text_output_dir, f"{pure_filename}.vtt")):
                os.rename(
                    vtt_file,
                    os.path.join(text_output_dir, f"{pure_filename}.vtt"),
                )

        vtt_file = os.path.join(text_output_dir, f"{pure_filename}.vtt")
        if not os.path.exists(vtt_file):
            faster_whisper_transcribe_vtt(
                f"{os.path.join(audiopath, pure_filename)}.mp3",
                args.whisper_model_size,
                vtt_file,
            )

        logger.info(f"subtitle is stored:{vtt_file}")

    def get_audio_filename(link):
        # Create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as temp_dir:
            get_dl_audio_path_cmd = f'yt-dlp {link} -o "{temp_dir}/%(title)s.%(ext)s" -S "+size,+br" --extract-audio --audio-format mp3 --no-keep-video --quiet'
            # Run the command without specifying the encoding
            subprocess.run(
                get_dl_audio_path_cmd, shell=True, universal_newlines=True
            )
            file = os.listdir(temp_dir)
            # Get the filename without extension
            pure_filename = os.path.splitext(os.path.basename(file[0]))[0]
        # Normalize the filename
        # pure_filename = unicodedata.normalize("NFKD", pure_filename)
        return pure_filename

    def get_video_lang(link, pure_filename):
        with tempfile.TemporaryDirectory() as temp_dir:
            download_video_cmd = f'yt-dlp {link} -o "{temp_dir}/%(title)s.%(ext)s" -S "+size,+br" --download-sections "*01:00-01:30" --extract-audio --audio-format mp3 --no-keep-video'
            subprocess.run(download_video_cmd, shell=True)
            sample_audio_path = os.path.join(temp_dir, f"{pure_filename}.mp3")
            video_language = audio_language(sample_audio_path)
        return video_language

    logger.info(f"processing {link}")
    pure_filename = get_audio_filename(link)
    logger.info(f"video name:{pure_filename}")
    video_language = get_video_lang(link, pure_filename)
    logger.info(f"video language:{video_language}")
    if args.pic_embed == "True":
        res_option = ''
    if args.pic_embed == "False":
        res_option = '-S "+size,+br"'

    download_video_cmd = f'yt-dlp {link} -o "{audiopath}/%(title)s.%(ext)s" {res_option} --extract-audio --audio-format mp3 --keep-video --write-subs  --sub-format vtt --sub-langs {video_language}'
    subprocess.run(download_video_cmd, shell=True)

    download_subtitle_file(audiopath, pure_filename, video_language, text_output_dir)
    # llm
    vtt_file = os.path.join(text_output_dir, f"{pure_filename}.vtt")

    video_path = find_video_file(directory=audiopath, pure_filename=pure_filename)
    vtt_to_file(
        vtt_file=vtt_file,
        output_file=os.path.join(integrate_text_output_dir, f"{pure_filename}.docx"),
        link=link,
        video_path=video_path,
        format="docx",
        pic_embed=args.pic_embed,
    )

    if args.timestamp_content == "True":
        with open(vtt_file, "r", encoding="utf-8") as fp:
            file_content = fp.read()
    if args.timestamp_content == "False":
        file_content = clean_vtt(vtt_file)

    chunks = chunk_string_by_words(file_content, 6000)
    response_text = llm_summary(
        args, link, integrate_text_output_dir, pure_filename, chunks
    )
    if args.TTS_create == "True":
        generate_audio_openvoice(
            response_text, post_audio_output_dir,pure_filename, args.language
        )
        # generate_audio_coqui(response_text, post_audio_output_dir,pure_filename, args.language)


def llm_summary(args, link, integrate_text_output_dir, pure_filename, chunks):
    def integrate_text_format(
        video_title, link, args, integrate_text_output_dir, llm_content
    ):
        integrate_text = (
            video_title
            + "\n("
            + link
            + ")\n"
            + "#" * 16
            + "\n"
            + "prompt:"
            + args.prompt
            + "\n"
            + llm_content
            + "\n"
            + "#" * 16
            + "\n"
        )
        file_name = os.path.join(integrate_text_output_dir, f"{video_title}.docx")

        doc = Document(file_name)

        new_para = doc.paragraphs[0].insert_paragraph_before(integrate_text)
        # 保存文件
        doc.save(file_name)
        return None

    if args.model_name == "auto":
        if args.language == "zh":
            model_name = "ycchen/breeze-7b-instruct-v1_0"
        if args.language == "en":
            model_name = "llama3"
    else:
        model_name = args.model_name
    responses = []

    logger.info(f"LLM summarizing")
    for chunk in tqdm(chunks):
        body = {
            "model": model_name,
            "prompt": f"用以下語言執行任務:{args.language}. {args.prompt} 任務: {chunk} .用以下語言執行任務: {args.language}. {args.prompt} ",
            "system": f"{args.prompt} 用以下語言執行任務:{args.language}. ",
            "stream": False,
        }
        response = requests.post("http://localhost:11434/api/generate", json=body)
        if response.status_code == 200:
            json_response = response.json()
            if 'response' in json_response:
                responses.append(json_response["response"])
            else:
                logger.error(f"Key 'response' not found in the returned JSON object: {json_response}")
        else:
            logger.error(f"Request failed with status code {response.status_code}: {response.text}")    
        combined_responses = "\n-------------- \n".join(responses)

    body = {
        "model": model_name,
        "prompt": f"用以下語言執行任務:{args.language}. 請重新組織所有要點組成一篇組織嚴謹、文筆流暢的文章: {combined_responses} .用以下語言執行任務: {args.language}.  請重新組織所有要點組成一篇組織嚴謹、文筆流暢的文章",
        "system": f"請重新組織所有要點組成一篇組織嚴謹、文筆流暢的文章，用以下語言執行任務:{args.language}. ",
        "stream": False,
    }
    responses = []
    integrate_response = requests.post("http://localhost:11434/api/generate", json=body)
    if integrate_response.status_code == 200:
        json_response = integrate_response.json()
        if 'response' in json_response:
            responses.append(json_response["response"])
        else:
            logger.error(f"Key 'response' not found in the returned JSON object: {json_response}")
    else:
        logger.error(f"Request failed with status code {integrate_response.status_code}: {integrate_response.text}")    
    integrate_response_text = integrate_response.json()["response"]
    if args.llm_format == 'summary':
        response_text = integrate_response_text
    if args.llm_format == 'detail':
        response_text = combined_responses
    if args.llm_format == 'both':
        response_text = integrate_response_text + "\n =========== \n" + combined_responses

    integrate_text_format(
        pure_filename, link, args, integrate_text_output_dir, response_text
    )
    logger.info(f"LLM response character count: {len(response_text)}")
    return response_text


def parse_arguments():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(
        description="Download youtube video, convert it to text and inference by llm"
    )

    ## yt download parameters
    parser.add_argument(
        "--link",
        type=str,
        default="",
        help="The link to the youtube video,or a ttrss link",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="summary the following content",
        help="template to llm, in en or zh",
    )
    parser.add_argument("--language", type=str, default="en", help="language of output")
    parser.add_argument(
        "--whisper_model_size",
        type=str,
        default="medium",
        help="model to use for whisper",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="auto",
        help="llm model,in ollama format:https://ollama.com/library",
    )
    parser.add_argument(
        "--timestamp_content",
        type=str,
        default="False",
        help="use timestamp in LLM inference",
    )
    parser.add_argument(
        "--output_dir", type=str, default=script_dir, help="output directory"
    )
    parser.add_argument(
        "--pic_embed", type=str, default="True", help="output directory"
    )
    parser.add_argument(
        "--TTS_create", type=str, default="True", help="TTS create"
    )
    parser.add_argument(
        "--llm_format", type=str, default="detail", help="LLM output format"
    )

    return parser.parse_args()


def initialize_directories(args, logger):
    os.makedirs(args.output_dir, exist_ok=True)
    os.chdir(args.output_dir)
    logger.info(f"current directory:{os.getcwd()}")
    audiopath = os.path.join(args.output_dir, "audio")
    text_output_dir = os.path.join(args.output_dir, "text")
    integrate_text_output_dir = os.path.join(args.output_dir, "integrate_text")
    post_audio_output_dir = os.path.join(args.output_dir, "audio_llm_processed")
    # Create directories if they don't exist
    os.makedirs(audiopath, exist_ok=True)
    os.makedirs(text_output_dir, exist_ok=True)
    os.makedirs(post_audio_output_dir, exist_ok=True)
    os.makedirs(integrate_text_output_dir, exist_ok=True)
    return audiopath, text_output_dir, integrate_text_output_dir, post_audio_output_dir


def main(args=parse_arguments()):

    logger.info(f"parameters:" + str(args))

    audiopath, text_output_dir, integrate_text_output_dir, post_audio_output_dir = (
        initialize_directories(args, logger)
    )

    if args.link == "":
        logger.info("at least one youtube or ttrss link is required")
        sys.exit()
    raw_links = [args.link]
    links = []

    if is_localhost(args.link):
        logger.info("The link starts with 'localhost: may be a ttrss link'")
        raw_links = parse_xml(f"{args.link}")
    for link in raw_links:
        element_link = playlist_urls(link)
        if isinstance(element_link, str):
            links.append(element_link)
        elif isinstance(element_link, list):
            links.extend(element_link)

    if args.model_name != "auto":
        logger.info(f"pulling model: {args.model_name}")
        ollama.pull(args.model_name)

    for link in links:
        # try:
        summary_video_from_link(
            clean_vtt,
            logger,
            args,
            link,
            post_audio_output_dir,
            integrate_text_output_dir,
            text_output_dir,
            audiopath,
        )
        # except Exception as e:
        #     logger.error(f"link process error: {e}")


if __name__ == "__main__":
    main()
