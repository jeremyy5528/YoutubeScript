import PyPDF2
import openvoice.se_extractor as se_extractor
from openvoice.api import BaseSpeakerTTS, ToneColorConverter
import os 
import torch 
def read_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page_num in range(len(reader.pages)):
            if page_num <= 22:
                continue
            if page_num <=25:
                page = reader.pages[page_num]
                text += page.extract_text()
            if page_num ==25:
                return text

        return text
    
text = read_pdf("D:/TTS_audiobook/Sally Ann Frank - The Startup Protocol_ A Guide for Digital Health Startups to Bypass Pitfalls and Adopt Strategies That Work-Productivity Press (2024).pdf")
# text ='Sally Ann Frank'

def generate_audio_openvoice(text, output_dir, pure_filename, speaker='default', mimic_tone_reference=False):
    """
    Generate audio using OpenVoice TTS.

    Args:
        text (str): The input text to be synthesized into speech.
        output_dir (str): The directory where the generated audio file will be saved.
        pure_filename (str): The filename of the generated audio file (without extension).
        speaker (str, optional): The speaker to use for synthesis. Defaults to 'default'.
        mimic_tone_reference (bool or str, optional): If False, use the default reference speaker for tone mimicry.
            If a string, use the provided audio file as the reference speaker. Defaults to False.

    Returns:
        None
    """
    
    # Run the base speaker tts for each speaker in the list
    language_full = 'English'
    language_code = 'EN'
    language = 'en'
    
    # obtain tone color embedding
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ckpt_base = os.path.join(script_dir, 'resources', 'checkpoints', 'base_speakers', language_code)
    base_speaker_config = os.path.join(ckpt_base, 'config.json')
    base_speaker_checkpoint = os.path.join(ckpt_base, 'checkpoint.pth')
    base_speaker_tts = BaseSpeakerTTS(base_speaker_config, device=device)
    base_speaker_tts.load_ckpt(base_speaker_checkpoint)
    src_path = os.path.join(output_dir, f'{pure_filename}.wav')
    base_speaker_tts.tts(text, src_path, speaker=speaker, language=language_full, speed=1.0)
    
    if mimic_tone_reference == False:
        reference_speaker = os.path.join(script_dir, 'resources', 'ZH_MIRU.mp3')  # This is the voice you want to clone
    else:
        reference_speaker = mimic_tone_reference  # This is the voice you want to clone
        ckpt_converter = os.path.join(script_dir, 'resources', 'checkpoints', 'converter')
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
