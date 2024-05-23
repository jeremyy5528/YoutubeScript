import logging
from logging.handlers import RotatingFileHandler
import os
def setup_logger():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # 創建一個handler對象來將日誌信息寫入文件
    file_handler = RotatingFileHandler(
        os.path.join(script_dir, "logfile.log"), maxBytes=10**6, backupCount=2
    )
    file_handler.setLevel(logging.DEBUG)

    # 創建一個handler對象來將日誌信息輸出到命令行
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    # 創建一個formatter對象來設定日誌信息的格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # 將handler添加到logger中
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
logger = setup_logger()