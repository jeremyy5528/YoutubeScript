# pdf_TTS
from parse_article import parse_pdf,get_title
from TTS_module import generate_audio_openvoice
import os
def pdf_TTS(pdf_file,output_dir): 
    def sanitize_filename(filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:80]
    
    def get_abstract(pdf_content):    
        if len(pdf_content['abstract'])==0:
            return
        
        text= ''.join(pdf_content['abstract'])
        file_name = sanitize_filename('00_abstract_'+pure_filename)
        return file_name,text

    def fulltext_generator(pdf_content, pure_filename):
        def number_generator(n):
            for i in range(1,n+1):
                yield "{:02}".format(i)
        for section, i in zip(pdf_content['sections'], number_generator(len(pdf_content['sections'])+1)):
            if len(section['paragraphs']) == 0:
                continue
            file_name = sanitize_filename(f"{i}_{section['H1']}"+"_"+f"{section['H2']}_{pure_filename}")
            text = ''.join(section['paragraphs'])
            yield file_name, text
            
    pdf_content = parse_pdf( pdf_file)
    pure_filename = sanitize_filename(get_title(config_path=".\\resources\\grobid_config.json",pdf_file=pdf_file))
    
    file_name, text = get_abstract(pdf_content)
    output_dir = os.path.join(output_dir,pure_filename)
    os.mkdir(output_dir)
    generate_audio_openvoice(text,output_dir, pure_filename = file_name,language =  'en', speaker='default', mimic_tone_reference=False)
    
    for file_name, text in fulltext_generator(pdf_content, pure_filename):
        generate_audio_openvoice(text, output_dir, pure_filename = file_name,language =  'en', speaker='default', mimic_tone_reference=False)

