# pdf_TTS
from parse_article import parse_pdf,get_title
from TTS_module import generate_audio_openvoice

def pdf_TTS(pdf_file,output_dir): 
    def sanitize_filename(filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    def abstract_TTS(pdf_content,pure_file):    
        if len(pdf_content['abstract'])==0:
            return
        file_name = pure_file+'_00_abstract'
        text= ''.join(pdf_content['abstract'])
        generate_audio_openvoice(text,output_dir, pure_filename = file_name,language =  'en', speaker='default', mimic_tone_reference=False)

    def number_generator(n):
        for i in range(1,n+1):
            yield "{:02}".format(i)
    pdf_content = parse_pdf( pdf_file)
    pure_file = sanitize_filename(get_title(config_path="C:\RAG\grobid_client_python\config.json",pdf_file=pdf_file))
    abstract_TTS(pdf_content,pure_file)
    for section,i in zip(pdf_content['sections'],number_generator(len(pdf_content['sections'])+1)):
        if len(section['paragraphs'])==0:
            continue
        file_name = f"{pure_file}_{i}_{section['H1']}"+f"{section['H2']}"
        print(type(file_name))
        text= ''.join(section['paragraphs'])
        generate_audio_openvoice(text, output_dir, pure_filename = file_name,language =  'en', speaker='default', mimic_tone_reference=False)
