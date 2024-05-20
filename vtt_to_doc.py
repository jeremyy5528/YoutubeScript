from datetime import datetime, timedelta
import docx
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, blue
import webvtt


def timecode_to_seconds(timecode):
    """
    Converts a timecode string in the format 'HH:MM:SS' or 'MM:SS' or 'SS' to seconds.

    Args:
        timecode (str): The timecode string to convert.

    Returns:
        int: The equivalent number of seconds.

    Raises:
        ValueError: If the timecode format is invalid.
    """
    parts = timecode.split(":")
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


def create_youtube_hyperlink(caption, link, format):
    """
    Creates a hyperlink to a YouTube video based on the given caption, video ID, and format.

    Args:
        caption (Caption): The caption object containing the start, end, and text of the caption.
        link (str): The link of the YouTube video.
        format (str): The format of the hyperlink. Supported formats: 'docx'.

    Returns:
        tuple: A tuple containing the hyperlink text, URL, start time, and end time.

    """
    def remove_spaces_from_text(caption):
        """
        Remove &nbsp; and similar space markers from a caption.
    
        Args:
            caption (str): The caption from which to remove the space markers.
    
        Returns:
            str: The caption with the space markers removed.
        """
        # Replace &nbsp; with a space
        caption = caption.replace('&nbsp;', ' ')
        
        # Replace other HTML space entities
        caption = caption.replace('&ensp;', ' ')
        caption = caption.replace('&emsp;', ' ')
        caption = caption.replace('&thinsp;', ' ')
        return caption
    start, end, text = caption.start, caption.end, caption.text
    text = remove_spaces_from_text(text)
    total_seconds = timecode_to_seconds(start)
    if format == "docx":
        # For Word, we return the URL and text separately to create a hyperlink later
        return (
            text,
            f"{link}&t={total_seconds}s",
            start,
            end,
        )


def add_hyperlink(run, url, text):
    """
    Adds a hyperlink to a run in a Word document.

    Parameters:
    - run (docx.text.run.Run): The run to add the hyperlink to.
    - url (str): The URL of the hyperlink.
    - text (str): The text to display for the hyperlink.

    Returns:
    - hyperlink (docx.oxml.shared.OxmlElement): The created hyperlink element.
    """
    # Clear the text in the original run
    run.text = ""

    r_id = run.part.relate_to(
        url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True
    )

    hyperlink = parse_xml(
        r'<w:hyperlink xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" r:id="%s" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" />'
        % r_id
    )
    new_run = docx.oxml.shared.OxmlElement("w:r")
    run_text = docx.oxml.shared.OxmlElement("w:t")
    run_text.text = text
    new_run.append(run_text)
    hyperlink.append(new_run)
    run._r.append(hyperlink)
    return hyperlink


def write_word_file(content, output_file, minutes_per_paragraph=0.5):
    """
    Writes the content to a Word document with specified formatting.

    Args:
        content (list): A list of tuples containing the text, URL, start time, and end time.
        output_file (str): The path and filename of the output Word document.
        minutes_per_paragraph (float, optional): The maximum number of minutes per paragraph. Defaults to 0.5.

    Returns:
        None
    """

    doc = Document()
    para = doc.add_paragraph()  # Create a paragraph outside the loop
    start_time = parse_time(content[0][2])  # Parse the start time
    for text, url, start, end in content:
        current_time = parse_time(start)  # Parse the current start time
        if (current_time - start_time) >= timedelta(minutes=minutes_per_paragraph):
            para.add_run("\n")  # Insert a paragraph break
            start_code = start_time.time()
            start_code = start_code.strftime('%H:%M:%S')
            end_code = parse_time(previous_end)
            end_code = end_code.strftime('%H:%M:%S')
            para.add_run(f"({start_code} - {end_code}) \n")
            para.add_run("\n\n")  # Insert a paragraph break
            start_time = current_time
        run = para.add_run(text + " ")
        add_hyperlink(run, url, text)
        previous_end = end
    para.add_run("\n")  # Insert a paragraph break
    para.add_run(f"({start_time.time().strftime('%H:%M:%S')} - {parse_time(content[-1][3]).strftime('%H:%M:%S')}) \n")
    doc.save(output_file)
    print(f"Word file {output_file} created successfully")


def parse_time(time_str):
    """
    Parses a time string and returns a datetime object.

    Args:
        time_str (str): The time string to parse. It should be in the format "HH:MM:SS.sss" or "MM:SS.sss".

    Returns:
        datetime: A datetime object representing the parsed time.

    Raises:
        ValueError: If the time string is not in a valid format.

    """
    # Handle two types of time formats: "HH:MM:SS.sss" and "MM:SS.sss"
    if len(time_str.split(":")) == 3:
        return datetime.strptime(time_str, "%H:%M:%S.%f")
    else:
        return datetime.strptime(time_str, "%M:%S.%f")


def generate_content(vtt_file, link, format):
    """
    Generate content from a VTT file.

    Args:
        vtt_file (str): The path to the VTT file.
        link (str): The link of the video.
        format (str): The desired format of the content.

    Returns:
        list: A list of tuples containing the generated content. Each tuple consists of the text and hyperlink.

    """
    # Read the VTT file
    captions = webvtt.read(vtt_file)

    content = []
    for caption in captions:
        hyperlink = create_youtube_hyperlink(caption, link, format)
        content.append(hyperlink)  # Store the text and hyperlink as a tuple
    return content


def vtt_to_file(vtt_file, output_file, link, format):
    """
    Convert a VTT file to a specified format and write the content to an output file.

    Parameters:
    vtt_file (str): The path to the VTT file.
    output_file (str): The path to the output file.
    link (str): The link of the video.
    format (str): The desired format of the output file. Currently supports 'word'.

    Raises:
    ValueError: If an invalid format is provided.

    Returns:
    None
    """
    # Generate the content
    content = generate_content(vtt_file, link, format)

    # Write the content to the output file
    if format == "docx":
        write_word_file(content, output_file)

    else:
        raise ValueError("Invalid format")
