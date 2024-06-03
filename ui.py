import tkinter as tk
from tkinter import filedialog
from yt_transcript import main
import tkinter.messagebox as messagebox
from tkinter import ttk
import threading
import os
import locale
class Args:
    def __init__(
        self,
        link,
        prompt,
        language,
        whisper_model_size,
        model_name,
        timestamp_content,
        output_dir,
        pic_embed, 
        TTS_create 
    ):
        self.link = link
        self.prompt = prompt
        self.language = language
        self.whisper_model_size = whisper_model_size
        self.model_name = model_name
        self.timestamp_content = timestamp_content
        self.output_dir = output_dir
        self.pic_embed = pic_embed
        self.TTS_create = TTS_create



def submit():
    link = link_entry.get() or ""
    prompt = prompt_entry.get() or "summary the following content"
    language = language_var.get()
    whisper_model_size = whisper_model_size_var.get()
    pic_embed = pic_embed_var.get()
    TTS_create = TTS_create_var.get()
    model_name = model_name_entry.get() or "auto"
    timestamp_content = timestamp_content_var.get()
    output_dir = filedialog.askdirectory()  # Ask for directory
    script_dir = os.path.dirname(os.path.realpath(__file__))
    output_dir = (
        output_dir if output_dir else script_dir
    )  # If output_dir is empty, use default script_dir

    args = Args(
        link,
        prompt,
        language,
        whisper_model_size,
        model_name,
        timestamp_content,
        output_dir,
        pic_embed, 
        TTS_create
    )


    # Clear the entries
    link_entry.delete(0, "end")
    prompt_entry.delete(0, "end")
    model_name_entry.delete(0, "end")

    # Run main function in a new thread

    threading.Thread(target=main, args=(args,), daemon=True).start()

    # Show a message box
    messagebox.showinfo("Information", "Submission successful")


root = tk.Tk()

boolean_options = ["True", "False"]

link_label = tk.Label(root, text="Link")
link_label.pack()
link_entry = tk.Entry(root)
link_entry.pack()

prompt_label = tk.Label(root, text="Prompt")
prompt_label.pack()
prompt_entry = tk.Entry(root)
prompt_entry.pack()



language_options = ["en", "zh"]
language_var = tk.StringVar(root)
language_var.set(language_options[0])  # default value
language_optionmenu = tk.OptionMenu(root, language_var, *language_options)
language_optionmenu.pack()



whisper_model_size_label = tk.Label(root, text="Whisper Model Size")
whisper_model_size_label.pack()
whisper_model_size_options = ["small", "medium", "large"]
whisper_model_size_var = tk.StringVar(root)
whisper_model_size_var.set(whisper_model_size_options[1])  # default value
whisper_model_size_optionmenu = tk.OptionMenu(root, whisper_model_size_var, *whisper_model_size_options)
whisper_model_size_optionmenu.pack()

model_name_options= ['auto','llama3','ycchen/breeze-7b-instruct-v1_0','r3m8/llama3-simpo:latest']
model_name_label = tk.Label(root, text="Model Name")
model_name_label.pack()
model_name_entry = ttk.Combobox(root, values=model_name_options)
model_name_entry.pack()
model_name_entry.pack()
model_name_entry.insert(0, "auto")

timestamp_content_label = tk.Label(root, text="Timestamp Content")
timestamp_content_label.pack()
timestamp_content_var = tk.StringVar(root)
timestamp_content_var.set(boolean_options[0])  # default value
timestamp_content_optionmenu = tk.OptionMenu(root, timestamp_content_var, *boolean_options)
timestamp_content_optionmenu.pack()

pic_embed_label = tk.Label(root, text="Pic Embed")
pic_embed_label.pack()
pic_embed_var = tk.StringVar(root)
pic_embed_var.set(boolean_options[0])  # default value
pic_embed_optionmenu = tk.OptionMenu(root, pic_embed_var, *boolean_options)
pic_embed_optionmenu.pack()

TTS_create_label = tk.Label(root, text="TTS Create")
TTS_create_label.pack()
TTS_create_var = tk.StringVar(root)
TTS_create_var.set(boolean_options[0])  # default value
TTS_create_optionmenu = tk.OptionMenu(root, TTS_create_var, *boolean_options)
TTS_create_optionmenu.pack()

submit_button = tk.Button(root, text="Output Folder", command=submit)
submit_button.pack()

root.mainloop()
