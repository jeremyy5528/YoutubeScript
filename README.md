# installation
1. install python >= 3.9 <3.12 (TTS required) and docker
https://www.python.org/downloads/release/python-31010/
https://www.docker.com/get-started/

under windows paltform run the install.bat
it will run the following commands
pip3 install -r requirements.txt
winget install ffmpeg
docker compose up
docker exec ollama ollama pull llama3:8b
docker exec ollama ollama pull ycchen/breeze-7b-instruct-v1_0

2. use following commands to install packages in requirements.txt
pip3 install -r requirements.txt

3. install FFmpeg
linux:
sudo apt install ffmpeg

windows:
winget install ffmpeg

macos:
brew install ffmpeg

4. install ollama(LLM) and ttrss automatically through docker compose
docker compose up
docker exec ollama ollama pull llama3:8b
docker exec ollama ollama pull ycchen/breeze-7b-instruct-v1_0

# optional (suubscribe rss)

1. get rss subscribe link 

can easily get the subscribe link by rsshub radar chrome extension

https://chromewebstore.google.com/detail/rsshub-radar/kefjpfngnndepjbopdmoebkipbgkggaa

the subscribe link format:(e.g. nature vedio: https://www.youtube.com/@NatureVideoChannel)
https://www.youtube.com/feeds/videos.xml?channel_id=UC9bYDXoFxWC2DQatWI366UA

2. subcribe some youtube channel through ttrss

the GUI interface of ttrss: http://localhost:181/
 
user：admin 
password：password

or

user：admin 
password：ttrss

(can set the user and password through compose file or change it in GUI after login)

You can find the subscribe button by clicking on the top-right menu button.

documentations for ttrss: https://ttrss.henry.wang/zh/#%E9%80%9A%E8%BF%87-docker-%E9%83%A8%E7%BD%B2

3. get the rss feed link from ttrss through orange rss icon.
the format is like : http://localhost:181/public.php?op=rss&id=-3&is_cat=0&q=&key=2wje2q662703f6266c7


# Project Analysis and Future To-Dos for Video Summarization Script

## Function Definition

**Function Description**
This script automates the entire process of extracting, cleaning, and summarizing textual information from YouTube videos or ttrss RSS feeds. The final output includes summarized text in document format and optionally synthesized speech audio files.

**Main Functions**
1. **Argument Parsing**:
   - Uses `argparse` to parse command-line arguments to control the script's behavior.
   - Supported parameters include YouTube or ttrss link, language, model name, output directory, etc.

2. **Download and Subtitle Generation**:
   - Uses `yt-dlp` to download videos or extract audio.
   - Generates subtitles using Whisper.
   - Cleans subtitle files by removing timestamps and other non-content elements.

3. **Content Summarization**:
   - Splits subtitle text into chunks and sends them to a large language model (LLM) for summarization.
   - Combines and refines the summarized text.

4. **Document and Audio Generation**:
   - Creates `.docx` files containing summarized text.
   - Optionally generates TTS audio files from the summarized text.

## Future To-Dos

1. **Code Improvement and Optimization**:
   - **Modularization**: Separate main functions into independent modules or classes to improve code maintainability and reusability.
   - **Error Handling**: Enhance error handling mechanisms to better manage failures in downloading, subtitle generation, etc.

2. **Feature Expansion**:
   - **Multilingual Support**: Add support for more languages, especially in the TTS generation and LLM summarization parts.
   - **Multi-Platform Support**: Ensure the script runs seamlessly on different operating systems (e.g., Windows, MacOS, Linux).

3. **Performance Optimization**:
   - **Parallel Processing**: Introduce multi-threading or multi-processing to speed up video downloading, subtitle generation, and summarization.
   - **Caching Mechanism**: Add caching to avoid reprocessing the same video or audio files.

4. **Testing and Documentation**:
   - **Unit Testing**: Add unit tests for each major function to ensure code reliability and maintainability.
   - **Usage Documentation**: Write detailed usage instructions and API documentation to help users and developers understand and use the script.


## Detailed Function List

1. **Argument Parsing**:
   - Parse command-line arguments.
   - Supported arguments: link, prompt, language, Whisper model size, model name, timestamp content, output directory, picture embed, TTS creation.

2. **Download and Subtitle Generation**:
   - Handle YouTube videos and ttrss links.
   - Download videos and extract audio.
   - Generate subtitles using Whisper.
   - Clean subtitle files.

3. **Content Summarization**:
   - Split subtitle text into chunks.
   - Summarize content using LLM.
   - Combine and refine summarized text.

4. **Document and Audio Generation**:
   - Create `.docx` files.
   - Optionally generate TTS audio files.


# usage 
the script support a cli-interface:

('--link', type=str, help='The link to the youtube video,or a ttrss link')

('--prompt', type=str, default="summary the following content", help='template to llm, in en or zh')

('--language', type=str, default= "en", help='language of output')

('--whisper_model_size', type=str, default='medium', help='model to use for whisper')

('--model_name', type=str, default="auto", help='llm model,in ollama format:https://ollama.com/library')

('--timestamp_content', type=str, default="False", help='use content contains timestamp in LLM inference')

('--output_dir', type=str,default= script_dir, help='output directory')

('--pic_embed', type=str, default='True', help="True or False, decide whether to embid scrrenshot in docx file")

('--TTS_create', type=str, default='True', help="True or False, decide whether to perform TTS")


## process single youtube video
python3  /mnt/d/youtubescript/yt_transcript.py --link "https://www.youtube.com/watch?v=0RtcsA5MQPs" --temp "give me three key points in the context" --language en

## process youtube video in playlist
python3  /mnt/d/youtubescript/yt_transcript.py --link "https://www.youtube.com/playlist?list=PLOAQYZPRn2V5RA1URMVkHFQYgLrkuXST9" --timestamp_content True --temp "give me three key points in the context and the timestamp" --language en --output_dir /mnt/d/youtubescript/Vivian_pop_sharing

## process each video record in ttrss link
python3  /mnt/d/youtubescript/yt_transcript.py --link "http://localhost:181/public.php?op=rss&id=-3&is_cat=0&q=&key=2wje2q662703f6266c7" --temp "從內容中萃取出一個商業機會" --language zh