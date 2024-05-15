import re
from docx import Document
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black,blue
import webvtt
from docx.shared import RGBColor
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
import docx
from datetime import datetime, timedelta


def timecode_to_seconds(timecode):
    parts = timecode.split(':')
    parts = [float(part) for part in parts]
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    elif len(parts) == 1:
        hours = 0
        minutes = 0
        seconds = parts[0]
    else:
        raise ValueError("Invalid timecode format")
    return int(hours * 3600 + minutes * 60 + seconds)

def create_youtube_hyperlink(caption, video_id, format):
    start, end, text = caption.start, caption.end, caption.text
    total_seconds = timecode_to_seconds(start)
    if format == 'word':
        # For Word, we return the URL and text separately to create a hyperlink later
        return text, f'https://www.youtube.com/watch?v={video_id}&t={total_seconds}s' ,start,end

def add_hyperlink(run, url, text):
    """
    Add a hyperlink to a run.
    """
    # Clear the text in the original run
    run.text = ''

    r_id = run.part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    hyperlink = parse_xml(r'<w:hyperlink xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" r:id="%s" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" />' % r_id)
    new_run = docx.oxml.shared.OxmlElement('w:r')
    run_text = docx.oxml.shared.OxmlElement('w:t')
    run_text.text = text
    new_run.append(run_text)
    hyperlink.append(new_run)
    run._r.append(hyperlink)
    return hyperlink

def write_word_file(content, output_file, minutes_per_paragraph=0.5):
    doc = Document()
    para = doc.add_paragraph()  # Create a paragraph outside the loop
    start_time = parse_time(content[0][2])  # Parse the start time
    for text, url, start, end in content:
        current_time = parse_time(start)  # Parse the current start time
        if (current_time - start_time) >= timedelta(minutes=minutes_per_paragraph):
            para.add_run('\n')  # Insert a paragraph break
            para.add_run(f'({start} - {end}) \n')  
            para.add_run('\n\n')  # Insert a paragraph break
            start_time = current_time
        run = para.add_run(text + ' ')
        add_hyperlink(run, url, text)
    doc.save(output_file)
    print(f'Word file {output_file} created successfully')

def parse_time(time_str):
    # Handle two types of time formats: "HH:MM:SS.sss" and "MM:SS.sss"
    if len(time_str.split(':')) == 3:
        return datetime.strptime(time_str, "%H:%M:%S.%f")
    else:
        return datetime.strptime(time_str, "%M:%S.%f")
def generate_content(vtt_file, video_id, format):
    # Read the VTT file
    captions = webvtt.read(vtt_file)

    content = []
    for caption in captions:
        
        hyperlink = create_youtube_hyperlink(caption,video_id, format)
        content.append(hyperlink)  # Store the text and hyperlink as a tuple
    return content

def vtt_to_file(vtt_file, output_file, video_id, format):
    # Generate the content
    content = generate_content(vtt_file, video_id, format)

    # Write the content to the output file
    if format == 'word':
        write_word_file(content, output_file)

    else:
        raise ValueError("Invalid format")
