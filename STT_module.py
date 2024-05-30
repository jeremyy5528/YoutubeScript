from datetime import timedelta
from webvtt import WebVTT, Caption
from faster_whisper import WhisperModel
import os
from tqdm import tqdm
def audio_language(audio_path):
    os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Run on GPU with FP16
    model = WhisperModel('base', device="cuda", compute_type="float16")

    segments, info = model.transcribe(audio_path, beam_size=5)
    return(info.language)
    
def faster_whisper_transcribe_vtt(audio_path,model_size,output_path):
    os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Run on GPU with FP16
    model = WhisperModel(model_size, device="cuda", compute_type="float16")

    segments, info = model.transcribe(audio_path, beam_size=5)

# Create a new WebVTT object
    vtt = WebVTT()

# Loop through the segments and create captions
    for segment in tqdm(segments):
    # Convert start and end times to 'HH:MM:SS.MMM' format
        start_time = str(timedelta(seconds=segment.start))
        end_time = str(timedelta(seconds=segment.end))

    # Ensure the timestamps have millisecond precision
        if '.' not in start_time:
            start_time += '.000'
        if '.' not in end_time:
            end_time += '.000'

    # Create a new caption
        caption = Caption(
        start=start_time,
        end=end_time,
        text=segment.text
    )
    # Add the caption to the WebVTT object
        vtt.captions.append(caption)

# Save the WebVTT object to a .vtt file
    vtt.save(output_path)


