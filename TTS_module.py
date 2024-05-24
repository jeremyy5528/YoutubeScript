import os
import torch
import openvoice.se_extractor as se_extractor
from openvoice.api import BaseSpeakerTTS, ToneColorConverter
import TTS
import glob
from tqdm import tqdm
from langdetect import detect
from pydub import AudioSegment
from auxiliary_function import chunk_string_by_words
from logger import logger
def detect_language(response_text,args):
    language = args.language
    detected_language = detect(response_text)
    if (detected_language == "en") & (args.language == "zh"):
        language = "en"
    if (
        (detected_language == "zh-cn")
        | (detected_language == "zh-cn")
        | (detected_language == "zh")
    ) & (args.language == "en"):
        language = "zh"
    return language

def generate_audio_openvoice(text, output_dir, pure_filename, args,speaker='default',mimic_tone_reference = False):
    language = detect_language(text,args)
    # Run the base speaker tts for each speaker in the list
    if language == 'en':
        language_full = 'English'
        language_code = 'EN'
    if language == 'zh':
        language_full = 'Chinese'
        language_code = 'ZH'

    # obtain tone color embedding
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ckpt_base = os.path.join(script_dir, 'Openvoice', 'checkpoints', 'base_speakers', language_code)
    base_speaker_config = os.path.join(ckpt_base, 'config.json')
    base_speaker_checkpoint = os.path.join(ckpt_base, 'checkpoint.pth')
    base_speaker_tts = BaseSpeakerTTS(base_speaker_config, device=device)
    base_speaker_tts.load_ckpt(base_speaker_checkpoint)
    src_path = os.path.join(output_dir, f'{pure_filename}.wav')
    base_speaker_tts.tts(text, src_path, speaker=speaker, language=language_full, speed=1.0)
    if mimic_tone_reference == False:
        reference_speaker = os.path.join(script_dir, 'Openvoice', 'resources', 'ZH_MIRU.mp3')  # This is the voice you want to clone
    else:
        reference_speaker = mimic_tone_reference  # This is the voice you want to clone
        ckpt_converter = os.path.join(script_dir, 'Openvoice', 'checkpoints', 'converter')
        tone_color_config = os.path.join(ckpt_converter, 'config.json')
        tone_color_checkpoint = os.path.join(ckpt_converter, 'checkpoint.pth')
        tone_color_converter = ToneColorConverter(tone_color_config, device=device)
        tone_color_converter.load_ckpt(tone_color_checkpoint)

        source_se = torch.load(os.path.join(ckpt_base, f'{language}_default_se.pth')).to(device)
        target_se, audio_name = se_extractor.get_se(reference_speaker, tone_color_converter, target_dir='processed',
                                                    vad=True)
        save_path = os.path.join(output_dir, f'{pure_filename}_{speaker}.wav')

        # Run the tone color converter
        encode_message = "@MyShell"
        tone_color_converter.convert(
            audio_src_path=src_path,
            src_se=source_se,
            tgt_se=target_se,
            output_path=save_path,
            message=encode_message)


def generate_audio_coqui(response_text, post_audio_output_dir, pure_filename, args):
    def merge_audio_files(files):
        combined = AudioSegment.empty()
        for file in files:
            combined += AudioSegment.from_wav(file)
        return combined
    # Get device
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    language = args.language 
    # List available 🐸TTS model
    language = detect_language(response_text,args)
    # Init TTS
    logger.info(f"TTS generating")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    # Run TTS
    post_audio_dir = (
        f"{os.path.join(post_audio_output_dir, pure_filename)}.wav"
    )
    # Split the response_text into chunks of 50 characters
    chunks = chunk_string_by_words(response_text, 50)

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