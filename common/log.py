import logging
import sys
from config.config_manager import config


class EnhancedLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)

    def error_with_trace(self, msg, *args, **kwargs):
        """Always log errors with stack trace"""
        kwargs['exc_info'] = True
        self.error(msg, *args, **kwargs)


class CustomFormatter(logging.Formatter):
    def format(self, record):
        # 暂存原始的 exc_text
        original_exc_text = record.exc_text

        # 如果没有异常信息，将 exc_text 设为空字符串
        if not record.exc_info:
            record.exc_text = ""
        else:
            # 如果有异常信息，在前面加换行符
            if record.exc_text:
                record.exc_text = "\n" + record.exc_text

        # 格式化消息
        formatted = super().format(record)

        # 恢复原始的 exc_text
        record.exc_text = original_exc_text

        return formatted


def _reset_logger(log):
    """Reset and configure logger with both file and console handlers"""
    # Clear existing handlers
    for handler in log.handlers:
        handler.close()
        log.removeHandler(handler)
        del handler
    log.handlers.clear()
    log.propagate = False

    # 修改日志格式，移除多余的 exc_info
    log_format = (
        "[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d][%(threadName)s] - "
        "%(message)s"
        "%(exc_text)s"  # 使用 exc_text 而不是 exc_info
    )

    # 使用自定义的 CustomFormatter
    formatter = CustomFormatter(
        log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create console handler
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.setFormatter(formatter)

    # Create file handler
    file_handle = logging.FileHandler("run.log", encoding="utf-8")
    file_handle.setFormatter(formatter)

    # Add both handlers
    log.addHandler(file_handle)
    log.addHandler(console_handle)


def _get_logger():
    """Initialize and return the logger"""
    logging.setLoggerClass(EnhancedLogger)
    log = logging.getLogger("log")
    _reset_logger(log)

    # Get log level from config
    log_level_str = config.get("logging.level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    log.setLevel(log_level)

    return log


# Global logger instance
logger = _get_logger()
