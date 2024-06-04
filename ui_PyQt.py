from PyQt5.QtWidgets import QTextEdit, QMessageBox,QApplication, QHeaderView,QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit, QFileDialog,QTableWidget,QTableWidgetItem
from PyQt5.QtCore import QThread,pyqtSignal,Qt,QThreadPool
import os
from PyQt5.QtGui import QMovie,QColor
from yt_transcript import main
import sys
from logger import SignalHandler, setup_logger
class Args:
    def __init__(
    self,
    link,
    prompt,
    llm_format,
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
        self.llm_format = llm_format
        self.language = language
        self.whisper_model_size = whisper_model_size
        self.model_name = model_name
        self.timestamp_content = timestamp_content
        self.output_dir = output_dir
        self.pic_embed = pic_embed
        self.TTS_create = TTS_create

class Worker(QThread):
    log_message = pyqtSignal(str)
    all_tasks_finished = pyqtSignal() 
    start_with_row = pyqtSignal(int)  # New signal with parameter
    finished_with_row = pyqtSignal(int)  # New signal with parameter

    def __init__(self):
        super().__init__()
        self.handler = SignalHandler(self.log_message)
        self.logger = setup_logger(self.handler)
        self.args_list = []  # Change args to a list of args

    def run(self):
        for i, args in enumerate(self.args_list):  # Iterate over all args in the list
            self.start_with_row.emit(i)  # Emit signal with row number
            main(args)
            self.finished_with_row.emit(i)  # Emit signal with row number
        self.all_tasks_finished.emit()  

    def set_args(self, args):
        self.args_list.append(args)  # Add new args to the list
    def re_init_args(self):
        self.args_list = []  # Add new args to the list

    def __del__(self):
        self.logger.removeHandler(self.handler)

class AppDemo(QWidget):
    def __init__(self):
        super().__init__()

        self.worker = Worker()
        self.worker.start_with_row.connect(self.show_start_message_with_row)  # Connect new signal
        self.worker.finished_with_row.connect(self.show_finished_message_with_row)  # Connect new signal
        self.worker.log_message.connect(self.add_log_message_to_table)  # Connect log_message signal to add_log_message_to_table method
        self.worker.all_tasks_finished.connect(self.show_all_tasks_finished_message) 

        self.loading_label = QLabel(self)
        window_width = self.width()
        window_height = self.height()
        label_width = int(window_width * 0.05)  # 50% of the window width
        label_height = int(window_height * 0.05)  # 50% of the window height
        label_x = int((window_width) *0.07)  # Center the label horizontally
        label_y = int((window_height)*0.01 ) # Center the label vertically
        self.loading_movie = QMovie(os.path.join('.','resources','loading.webp'))
        self.loading_label.setGeometry(label_x, label_y, label_width, label_height)
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setScaledContents(True)  #
        self.layout = QVBoxLayout()

        self.link_entry = QLineEdit()
        self.layout.addWidget(QLabel('Link*'))
        self.layout.addWidget(self.link_entry)

        self.prompt_options = ["summarize the content","條列重點","請將內容翻譯為繁體中文",  "撰寫介紹文章"]
        self.prompt_combobox = QComboBox()
        self.prompt_combobox.addItems(self.prompt_options)
        self.prompt_combobox.setEditable(True)
        self.layout.addWidget(QLabel('Prompt'))
        self.layout.addWidget(self.prompt_combobox)
        
        self.llm_format_options = ["detail","summary","both"]
        self.llm_format_combobox = QComboBox()
        self.llm_format_combobox.addItems(self.llm_format_options)
        index = self.llm_format_combobox.findText('summary', Qt.MatchFixedString)
        if index >= 0:
            self.llm_format_combobox.setCurrentIndex(index)
        self.layout.addWidget(QLabel('LLM Format'))
        self.layout.addWidget(self.llm_format_combobox)

        self.language_options = ["en", "zh"]
        self.language_combobox = QComboBox()
        self.language_combobox.addItems(self.language_options)
        self.layout.addWidget(QLabel('Output Language'))
        self.layout.addWidget(self.language_combobox)

        self.whisper_model_size_options = ["small", "medium", "large"]
        self.whisper_model_size_combobox = QComboBox()
        self.whisper_model_size_combobox.addItems(self.whisper_model_size_options)
        index = self.whisper_model_size_combobox.findText('medium', Qt.MatchFixedString)
        if index >= 0:
            self.whisper_model_size_combobox.setCurrentIndex(index)
        self.layout.addWidget(QLabel('Whisper Model Size'))
        self.layout.addWidget(self.whisper_model_size_combobox)

        self.model_name_options= ['auto','llama3','ycchen/breeze-7b-instruct-v1_0','r3m8/llama3-simpo:latest']
        self.model_name_combobox = QComboBox()
        self.model_name_combobox.setEditable(True)
        self.model_name_combobox.addItems(self.model_name_options)
        self.layout.addWidget(QLabel('Model Name'))
        self.layout.addWidget(self.model_name_combobox)

        self.timestamp_content_options = ["True", "False"]
        self.timestamp_content_combobox = QComboBox()
        self.timestamp_content_combobox.addItems(self.timestamp_content_options)
        index = self.timestamp_content_combobox.findText('False', Qt.MatchFixedString)
        if index >= 0:
            self.timestamp_content_combobox.setCurrentIndex(index)
        self.layout.addWidget(QLabel('Timestamp Content'))
        self.layout.addWidget(self.timestamp_content_combobox)

        self.pic_embed_options = ["True", "False"]
        self.pic_embed_combobox = QComboBox()
        self.pic_embed_combobox.addItems(self.pic_embed_options)
        self.layout.addWidget(QLabel('Picture Embed'))
        index = self.pic_embed_combobox.findText('False', Qt.MatchFixedString)
        if index >= 0:
            self.pic_embed_combobox.setCurrentIndex(index)
        self.layout.addWidget(self.pic_embed_combobox)

        self.TTS_create_options = ["True", "False"]
        self.TTS_create_combobox = QComboBox()
        self.TTS_create_combobox.addItems(self.TTS_create_options)
        self.layout.addWidget(QLabel('TTS Create'))
        self.layout.addWidget(self.TTS_create_combobox)

        
        self.output_dir_entry = QLineEdit()
        desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        self.output_dir_entry.setText(desktop_path)
        self.layout.addWidget(QLabel('Output Folder'))
        self.layout.addWidget(self.output_dir_entry)
        
        self.output_dir_button = QPushButton('Select Output Folder')
        self.output_dir_button.clicked.connect(self.select_output_dir)
        self.layout.addWidget(self.output_dir_button)
        
        self.submit_button = QPushButton('Submit')
        self.submit_button.clicked.connect(self.submit)
        self.layout.addWidget(self.submit_button)
        


        self.queue_table = QTableWidget(0, 12)  # 11 columns for each parameter and regist button

        self.queue_table.setHorizontalHeaderLabels([
            'Status', 'Link', 'Prompt','LLM format', 'Language', 'Whisper Model Size', 'Model Name', 'Timestamp Content', 'Pic Embed', 'TTS Create', 'Output Folder','Delete'
        ])
        self.layout.addWidget(self.queue_table)

        self.batch_regist_button = QPushButton('Execute All')
        self.batch_regist_button.clicked.connect(self.init_regist)
        self.batch_regist_button.clicked.connect(self.batch_regist)
        self.layout.addWidget(self.batch_regist_button)

        # Add a new QLabel and QTextEdit for the log message
        self.layout.addWidget(QLabel('Log Message'))
        self.log_message_entry = QTextEdit()
        self.layout.addWidget(self.log_message_entry)

        self.setLayout(self.layout)
        

    def select_output_dir(self):
        output_dir = QFileDialog.getExistingDirectory(self, 'Select Output Directory')
        self.output_dir_entry.setText(output_dir)
    def show_start_message_with_row(self,row):
        self.queue_table.setItem(row, 0, QTableWidgetItem('Running...'))
    def show_finished_message_with_row(self,row):
        item = QTableWidgetItem('Finished')
        item.setBackground(QColor(144, 238, 144))  # Light green
        self.queue_table.setItem(row, 0, item)
    def init_regist(self):
        # Set the first column of each row to "Pending"
        for row in range(self.queue_table.rowCount()):
            item = QTableWidgetItem('Pending')
            self.queue_table.setItem(row, 0, item)
    
        # Clear the args_list parameter of self.worker
        self.worker.re_init_args()
    def show_all_tasks_finished_message(self):
        self.loading_movie.stop()
        self.loading_label.hide()
        QMessageBox.information(self, "Information", "task completed")

    def submit(self):
        link = self.link_entry.text() or ""
        prompt = self.prompt_combobox.currentText() or "summary the following content"
        llm_format = self.llm_format_combobox.currentText() or "detail"
        language = self.language_combobox.currentText()
        whisper_model_size = self.whisper_model_size_combobox.currentText()
        model_name = self.model_name_combobox.currentText() or "auto"
        timestamp_content = self.timestamp_content_combobox.currentText()
        pic_embed = self.pic_embed_combobox.currentText()
        TTS_create = self.TTS_create_combobox.currentText()
        output_dir = self.output_dir_entry.text()
        delete_button = QPushButton('Delete')
        delete_button.clicked.connect(self.delete_row)
    
        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)
        self.queue_table.setItem(row, 0, QTableWidgetItem('Pending'))
        self.queue_table.setItem(row, 1, QTableWidgetItem(link))
        self.queue_table.setItem(row, 2, QTableWidgetItem(prompt))
        self.queue_table.setItem(row, 3, QTableWidgetItem(llm_format))
        self.queue_table.setItem(row, 4, QTableWidgetItem(language))
        self.queue_table.setItem(row, 5, QTableWidgetItem(whisper_model_size))
        self.queue_table.setItem(row, 6, QTableWidgetItem(model_name))
        self.queue_table.setItem(row, 7, QTableWidgetItem(timestamp_content))
        self.queue_table.setItem(row, 8, QTableWidgetItem(pic_embed))
        self.queue_table.setItem(row, 9, QTableWidgetItem(TTS_create))
        self.queue_table.setItem(row, 10, QTableWidgetItem(output_dir))
        self.queue_table.setCellWidget(row, 11, delete_button)
        self.queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def add_log_message_to_table(self, messages):
        # Update status in the first column
        self.log_message_entry.setText(messages)
    
    def delete_row(self):
        button = self.sender()
        if button:
            row = self.queue_table.indexAt(button.pos()).row()
            self.queue_table.removeRow(row)

    def regist(self, row):
        link = self.queue_table.item(row, 1).text()
        prompt = self.queue_table.item(row, 2).text()
        llm_format = self.queue_table.item(row, 3).text()
        language = self.queue_table.item(row, 4).text()
        whisper_model_size = self.queue_table.item(row, 5).text()
        model_name = self.queue_table.item(row, 6).text()
        timestamp_content = self.queue_table.item(row, 7).text()
        pic_embed = self.queue_table.item(row, 8).text()
        TTS_create = self.queue_table.item(row, 9).text()
        output_dir = self.queue_table.item(row, 10).text()
        args = Args(
            link,
            prompt,
            llm_format,
            language,
            whisper_model_size,
            model_name,
            timestamp_content,
            output_dir,
            pic_embed, 
            TTS_create
        )
        self.worker.set_args(args)
        self.loading_movie.start()
        self.loading_label.show()
    def row_regist(self, row):
        self.regist(row)
       

    def batch_regist(self):
        QMessageBox.information(self, "Information", "Task submission successful.")
        for row in range(self.queue_table.rowCount()):
            self.regist(row)
        self.worker.start()
        
app = QApplication(sys.argv)

demo = AppDemo()
demo.show()

sys.exit(app.exec_())