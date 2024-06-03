import logging
from logging.handlers import RotatingFileHandler
import os
class SignalHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)

def setup_logger(signal_handler=None):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # 创建一个handler对象来将日志信息写入文件
    file_handler = RotatingFileHandler(
        os.path.join(script_dir, "logfile.log"), maxBytes=10**6, backupCount=2
    )
    file_handler.setLevel(logging.DEBUG)

    # 创建一个handler对象来将日志信息输出到命令行
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    # 如果提供了SignalHandler，将其添加到logger
    if signal_handler is not None:
        logger.addHandler(signal_handler)

    # 创建一个formatter对象来设置日志信息的格式
    formatter = logging.Formatter(
        # ...
    )

    # 将formatter设置到handler对象中
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # 将handler对象添加到logger中
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
logger = setup_logger()