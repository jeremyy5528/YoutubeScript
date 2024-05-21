from docx import Document
from tqdm import tqdm
import json
import os
import subprocess
import argparse
import torch
from urllib.parse import urlparse
from TTS.api import TTS
from langdetect import detect
import xml.etree.ElementTree as ET
from io import StringIO
import ollama
import sys
import whisper
import re
import logging
from logging.handlers import RotatingFileHandler
import requests
import glob
from pydub import AudioSegment
from vtt_to_doc import vtt_to_file


def clean_vtt(filepath: str) -> str:
    """Clean up the content of a subtitle file (vtt) to a string

    Args:
        filepath (str): path to vtt file

    Returns:
        str: clean content
    """
    # read file content
    with open(filepath, "r", encoding="utf-8") as fp:
        content = fp.read()

    # remove header & empty lines
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    lines = lines[1:] if lines[0].upper() == "WEBVTT" else lines

    # remove indexes
    lines = [lines[i] for i in range(len(lines)) if not lines[i].isdigit()]

    # remove timestamps
    pattern = r"^\d{2}:\d{2}.\d{3}.*\d{2}:\d{2}.\d{3}$"
    lines = [lines[i] for i in range(len(lines)) if not re.match(pattern, lines[i])]

    content = " ".join(lines)
    # remove duplicate spaces
    pattern = r"\s+"
    content = re.sub(pattern, r" ", content)
    # add space after punctuation marks if it doesn't exist
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


def get_video_lang(logger, args, link, filename_without_extension):
    download_video_cmd = f'yt-dlp {link} -o "{args.audiopath}/%(title)s.%(ext)s" --download-sections "*01:00-01:30" --extract-audio --audio-format mp3 --no-keep-video'
    subprocess.run(download_video_cmd, shell=True)
    sample_audio_path = os.path.join(
        args.audiopath, f"{filename_without_extension}.mp3"
    )
    logger.info(f"sample audio is stored:{sample_audio_path}")
    audio = whisper.load_audio(sample_audio_path)
    audio = whisper.pad_or_trim(audio)
    model = whisper.load_model("base")
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # detect the spoken language
    _, probs = model.detect_language(mel)
    logger.debug(f"Detected language: {max(probs, key=probs.get)}")
    video_language = max(probs, key=probs.get)
    os.remove(sample_audio_path)
    return video_language


def chunk_string_by_words(s, chunk_size):
    words = s.split()
    chunks = [
        " ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)
    ]
    return chunks


def summary_video_from_link(clean_vtt, logger, args, link, get_video_lang):
    def chunk_string_by_words(string, length):
        # Calculate the percentage of spaces
        space_percentage = string.count(" ") / len(string)

        # Calculate the uniformity of spaces
        space_positions = [i for i, char in enumerate(string) if char == " "]
        space_differences = [
            j - i for i, j in zip(space_positions[:-1], space_positions[1:])
        ]
        uniformity = (
            max(space_differences) - min(space_differences) if space_differences else 0
        )

        # If more than 5% of the characters are spaces and the spaces are relatively uniform, split by words
        if space_percentage > 0.05 and uniformity <= length:
            words = string.split()
            chunks = [
                " ".join(words[i : i + length]) for i in range(0, len(words), length)
            ]
        else:
            chunks = [string[i : i + length] for i in range(0, len(string), length)]

        return chunks
    
    def find_video_file(directory, filename_without_extension):
        """
        Finds the video file in the specified directory with the specified filename (without extension).
    
        Args:
            directory (str): The directory where the files are located.
            filename_without_extension (str): The filename without extension.
    
        Returns:
            str: The filename with extension of the video file, or None if no video file is found.
        """
        # Define the video file extensions
        video_extensions = [".webm", ".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"]
    
        
        # Search for the video file
        all_files = glob.glob(os.path.join(directory, f"*{filename_without_extension}*"))
        
        for file in all_files:
            filename, extension = os.path.splitext(file)
            if extension in video_extensions and not re.search(r'\.f\d{3}', filename):
                # Return the video file found
                return glob.glob(os.path.join(directory, os.path.basename(file)))[0]
            

    logger.info(f"processing {link}")
    get_dl_audio_path_cmd = f'yt-dlp {link} --get-filename -o "{args.audiopath}%(title)s.%(ext)s" -S "+size,+br" --extract-audio --audio-format mp3 --no-keep-video --quiet'
    filename = (
        subprocess.check_output(get_dl_audio_path_cmd, shell=True)
        .decode("utf-8")
        .strip()
    )
    filename_without_extension = os.path.splitext(os.path.basename(filename).strip())[0]
    logger.info(f"video name:{filename_without_extension}")
    video_language = get_video_lang(logger, args, link, filename_without_extension)
    logger.info(f"video language:{video_language}")

    download_video_cmd = f'yt-dlp {link} -o "{args.audiopath}%(title)s.%(ext)s" --extract-audio --audio-format mp3 --keep-video  --write-subs  --sub-format vtt --sub-langs {video_language}'
    subprocess.run(download_video_cmd, shell=True)
    video_path = find_video_file(directory = args.audiopath , filename_without_extension=filename_without_extension)
  
    # Move subtitle_file to the text file ,if subtitle_file is exist
    vtt_file = f"{args.audiopath}{filename_without_extension}.{video_language}.vtt"
    if os.path.exists(vtt_file):
        os.rename(
            vtt_file, f"{args.text_output_dir}{filename_without_extension}.vtt"
        )

    vtt_file = f"{args.text_output_dir}{filename_without_extension}.vtt"
    if not os.path.exists(vtt_file):
        # Run whisper
        whisper_cmd = f'whisper "{args.audiopath}{filename_without_extension}.mp3" --model {args.whisper_model_size} --output_format vtt --output_dir {args.text_output_dir} --verbose False'
        subprocess.run(whisper_cmd, shell=True)

    
    logger.info(f"subtitle is stored:{filename_without_extension}")
    # llm
    vtt_to_file(vtt_file=vtt_file,output_file=f"{args.integrate_text_output_dir}{filename_without_extension}.docx",link = link,video_path = video_path,format = 'docx')
    if args.timestamp_content == "True":
        with open(vtt_file, "r", encoding="utf-8") as fp:
            file_content = fp.read()
    if args.timestamp_content == "False":
        file_content = clean_vtt(vtt_file)
    if args.model_name == "auto":
        if args.language == "zh":
            model_name = "ycchen/breeze-7b-instruct-v1_0"
        if args.language == "en":
            model_name = "llama3:8b"
    else:
        model_name = args.model_name

    chunks = chunk_string(file_content, 7000)
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
        responses.append(response.json()["response"])

    combined_responses = "\n-------------- \n".join(responses)

    body = {
        "model": model_name,
        "prompt": f"用以下語言執行任務:{args.language}. 請重新組織所有要點組成一篇組織嚴謹、文筆流暢的文章: {combined_responses} .用以下語言執行任務: {args.language}.  請重新組織所有要點組成一篇組織嚴謹、文筆流暢的文章",
        "system": f"請重新組織所有要點組成一篇組織嚴謹、文筆流暢的文章，用以下語言執行任務:{args.language}. ",
        "stream": False,
    }
    # body = {
    #     "model": model_name,
    #     "prompt": f"用以下語言執行任務:{args.language}. {args.prompt} 任務: {combined_responses} .用以下語言執行任務: {args.language}. {args.prompt} ",
    #     "system": f"{args.prompt} 用以下語言執行任務:{args.language}. ",
    #     "stream": False,
    # }

    integrate_response = requests.post("http://localhost:11434/api/generate", json=body)
    integrate_response_text = integrate_response.json()["response"]
    response_text = integrate_response_text + "\n =========== \n" + combined_responses
    post_text_dir = os.path.join(
        args.post_text_output_dir, f"{filename_without_extension}.txt"
    )
    # Write the response to text folder
    with open(post_text_dir, "w", encoding="utf-8") as f:
        f.write(response_text)

    integrate_text_format(filename_without_extension, args, vtt_file, post_text_dir)
    logger.info(f"LLM response character count: {len(response_text)}")
    logger.info(f"LLM response is stored: {post_text_dir}")

    # Get device
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # List available 🐸TTS models
    language = args.language
    detected_language = detect(response_text)
    if (detected_language == "en") & (language == "zh"):
        language = "en"
    if (
        (detected_language == "zh-cn")
        | (detected_language == "zh-cn")
        | (detected_language == "zh")
    ) & (language == "en"):
        language = "zh"

    # Init TTS
    logger.info(f"TTS generating")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    # Run TTS
    post_audio_dir = (
        f"{os.path.join(args.post_audio_output_dir, filename_without_extension)}.wav"
    )
    # Split the response_text into chunks of 80 characters
    chunks = chunk_string_by_words(response_text, 80)

    # Generate the audio files
    for i, chunk in enumerate(tqdm(chunks)):
        tts.tts_to_file(
            chunk,
            file_path=f"{post_audio_dir}_temp_{i}.wav",
            speaker="Tammie Ema",
            language=f"{language}",
        )

    # Get the list of all generated audio files
    files = sorted(glob.glob(f"{post_audio_dir}_temp_*.wav"))

    # Merge all the audio files
    combined = merge_audio_files(files)

    # Save the combined audio to a file
    combined.export(post_audio_dir, format="wav")

    # Delete the temporary files
    for file in files:
        os.remove(file)
    logger.info(f"TTS output language is: {language}")
    logger.info(f"TTS output is stored: {post_audio_dir}")


def chunk_string(string, length):
    return [string[i : i + length] for i in range(0, len(string), length)]


def merge_audio_files(files):
    combined = AudioSegment.empty()
    for file in files:
        combined += AudioSegment.from_wav(file)
    return combined


def integrate_text_format(video_title, args, vtt_file, llm_summary):
    # 打開第一個文件並讀取其內容
    with open(vtt_file, "r", encoding="utf-8") as file:
        vtt_file = file.read()

    # 打開第二個文件並讀取其內容
    with open(llm_summary, "r", encoding="utf-8") as file:
        llm_summary = file.read()

    # 將兩個文件的內容合併
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
        + llm_summary
        + "\n"
        + "#" * 16
        + "\n"
    )
    file_name = f"{args.integrate_text_output_dir}{video_title}.docx"
    
    doc = Document(file_name)

    # 在第一个段落之前插入一个新的段落
    new_para = doc.paragraphs[0].insert_paragraph_before(integrate_text)
    # 保存文件
    doc.save(file_name)

# Set up argument parser

script_dir = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 創建一個handler對象來將日誌信息寫入文件
file_handler = RotatingFileHandler(
    f"{script_dir}/logfile.log", maxBytes=10**6, backupCount=2
)
file_handler.setLevel(logging.INFO)

# 創建一個handler對象來將日誌信息輸出到命令行
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# 創建一個formatter對象來設定日誌信息的格式
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# 將handler添加到logger中
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

parser = argparse.ArgumentParser(
    description="Download youtube video, convert it to text and inference by llm"
)
## yt download parameters
parser.add_argument(
    "--link", type=str, default="", help="The link to the youtube video,or a ttrss link"
)
parser.add_argument(
    "--prompt",
    type=str,
    default="summary the following content",
    help="template to llm, in en or zh",
)
parser.add_argument("--language", type=str, default="en", help="language of output")
parser.add_argument(
    "--whisper_model_size", type=str, default="medium", help="model to use for whisper"
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
    "--audiopath",
    type=str,
    default="./audio/",
    help="The path to the audio file to save to",
)
parser.add_argument(
    "--text_output_dir",
    type=str,
    default="./text/",
    help="The path to the text file to save to",
)
parser.add_argument(
    "--integrate_text_output_dir",
    default="./integrate_text/",
    type=str,
    help="integrate_text_output_dir",
)
parser.add_argument(
    "--post_text_output_dir",
    default="./text_llm_processed/",
    type=str,
    help="post_text_output_dir",
)
parser.add_argument(
    "--post_audio_output_dir",
    default="./audio_llm_processed/",
    type=str,
    help="post_audio_output_dir",
)
args = parser.parse_args()
logger.info(f"parameters:" + str(args))
os.makedirs(args.output_dir, exist_ok=True)
os.chdir(args.output_dir)

if args.link == "":
    logger.info("at least one youtube or ttrss link is required")
    sys.exit()

if args.model_name != "auto":
    logger.info(f"pulling model: {args.model_name}")
    ollama.pull(args.model_name)

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

# Create directories if they don't exist
os.makedirs(args.audiopath, exist_ok=True)
os.makedirs(args.text_output_dir, exist_ok=True)
os.makedirs(args.post_text_output_dir, exist_ok=True)
os.makedirs(args.post_audio_output_dir, exist_ok=True)
os.makedirs(args.integrate_text_output_dir, exist_ok=True)


def process_link(link):
    summary_video_from_link(clean_vtt, logger, args, link, get_video_lang)


for link in links:
    process_link(link)
