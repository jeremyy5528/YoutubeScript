# digital_book_TTS
from TTS_module import generate_audio_openvoice
import ebooklib
from ebooklib import epub
# read epub
from bs4 import BeautifulSoup
from pydub import AudioSegment

def read_epub(path):
    """
    Read the contents of an EPUB file and return a list of texts.

    Args:
        path (str): The path to the EPUB file.

    Returns:
        list: A list of texts extracted from the EPUB file.

    """
    book = epub.read_epub(path)
    i=0
    texts = []  # 創建一個列表來收集所有文件的內容
    chapter_name =[]
    chapter_title =[]
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            i+=1
            content = item.get_content().decode('utf-8')  # 使用 UTF-8 來解碼
            soup = BeautifulSoup(content, 'html.parser')  # 使用 BeautifulSoup 來解析 HTML 內容
            # 找到所有的段落
            paragraphs = soup.find_all('p')
            if paragraphs is not None:
                # 過濾掉含有標題的段落
                for p in paragraphs:
                    print( p.get('class'))
                content_paragraphs = [p for p in paragraphs if not p.get('class') in [['cn'], ['ct']]]
                # 取得純文字內容
                content = ' '.join([p.get_text() for p in content_paragraphs])
                
                texts.append(content)
                if i == 0:
                    print(content)
            # 獲取章節名稱和標題
                chapter_name_tag = soup.find('p', class_='cn')
                chapter_title_tag = soup.find('p', class_='ct')
                
                if chapter_name_tag is not None:
                    chapter_name.append(chapter_name_tag.get_text())
                if chapter_title_tag is not None:
                    chapter_title.append(chapter_title_tag.get_text())
    
    print(len(chapter_name))
    print(len(chapter_title))
    print(len(texts))
    return chapter_name,chapter_title,texts  

def epub_TTS(file_path, output_dir, filename):
    """
    Process an EPUB file and generate audio files for each element in the text.
    
    Args:
        file_path (str): The path to the EPUB file.
        output_dir (str): The directory where the generated audio files will be saved.
        filename (str): The base filename for the generated audio files.
    """
    text = read_epub(file_path)
    # print(text)
    i = 0
    for element in text:
        i += 1
    #     generate_audio_openvoice(element, output_dir=output_dir, pure_filename=f"{filename}_{i}", language='en', speaker='default', mimic_tone_reference=False)

    # # merge generated audio
    # audio_files = [f"{output_dir}/{filename}_{i}.wav" for i in range(1, len(text) + 1)]
    # combined_audio = AudioSegment.empty()

    # for audio_file in audio_files:
    #     segment = AudioSegment.from_wav(audio_file)
    #     combined_audio += segment

    # output_file = f"{output_dir}/{filename}.wav"
    # combined_audio.export(output_file, format="wav")


if __name__ == "__main__":
    file_path = r"D:\TTS_audiobook\Malcolm Gladwell - The Tipping Point_ How Little Things Can Make a Big Difference-Little, Brown and Company (2000).epub"
    output_dir = r"D:\TTS_audiobook"
    filename = "Malcolm Gladwell - The Tipping Point_ How Little Things Can Make a Big Difference-Little, Brown and Company (2000)"
    epub_TTS(file_path, output_dir, filename)