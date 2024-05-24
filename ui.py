import tkinter as tk
from tkinter import filedialog
from yt_transcript import main
import tkinter.messagebox as messagebox
import threading
import os
import locale
locale.setlocale(locale.LC_ALL, 'C.utf8')
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
    language = language_entry.get() or "en"
    whisper_model_size = whisper_model_size_entry.get() or "medium"
    model_name = model_name_entry.get() or "auto"
    timestamp_content = timestamp_content_entry.get() or "False"
    output_dir = filedialog.askdirectory()  # Ask for directory
    script_dir = os.path.dirname(os.path.realpath(__file__))
    output_dir = (
        output_dir if output_dir else script_dir
    )  # If output_dir is empty, use default script_dir
    pic_embed = pic_embed_entry.get() or "True"  # New line
    TTS_create = TTS_create_entry.get() or "True"  # New line

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
    language_entry.delete(0, "end")
    whisper_model_size_entry.delete(0, "end")
    model_name_entry.delete(0, "end")
    timestamp_content_entry.delete(0, "end")
    pic_embed_entry.delete(0, "end")
    TTS_create_entry.delete(0, "end")

    # Run main function in a new thread

    threading.Thread(target=main, args=(args,), daemon=True).start()

    # Show a message box
    messagebox.showinfo("Information", "Submission successful")


root = tk.Tk()

link_label = tk.Label(root, text="Link")
link_label.pack()
link_entry = tk.Entry(root)
link_entry.pack()

prompt_label = tk.Label(root, text="Prompt")
prompt_label.pack()
prompt_entry = tk.Entry(root)
prompt_entry.pack()

language_label = tk.Label(root, text="Language")
language_label.pack()
language_entry = tk.Entry(root)
language_entry.pack()

whisper_model_size_label = tk.Label(root, text="Whisper Model Size")
whisper_model_size_label.pack()
whisper_model_size_entry = tk.Entry(root)
whisper_model_size_entry.pack()

model_name_label = tk.Label(root, text="Model Name")
model_name_label.pack()
model_name_entry = tk.Entry(root)
model_name_entry.pack()

timestamp_content_label = tk.Label(root, text="Timestamp Content")
timestamp_content_label.pack()
timestamp_content_entry = tk.Entry(root)
timestamp_content_entry.pack()

pic_embed_label = tk.Label(root, text="Pic Embed")
pic_embed_label.pack()
pic_embed_entry = tk.Entry(root)
pic_embed_entry.pack()

TTS_create_label = tk.Label(root, text="TTS Create")
TTS_create_label.pack()
TTS_create_entry = tk.Entry(root)
TTS_create_entry.pack()

submit_button = tk.Button(root, text="Submit", command=submit)
submit_button.pack()

root.mainloop()
