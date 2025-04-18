import os
import logging
from typing import Any, Dict
from dotenv import load_dotenv

class ConfigManager:
    def __init__(self):
        self._config = {}
        self._initialize()
        self._setup_logging()

    def _initialize(self):
        """Initialize configuration from environment variables"""
        load_dotenv()
        
        # Logging Configuration
        self._config["logging"] = {
            "level": os.getenv("LOG_LEVEL", "INFO").upper()
        }
        
        # WeChat API Configuration
        self._config["gewechat"] = {
            "base_url": os.getenv("BASE_URL"),
            "app_id": os.getenv("APP_ID"),
            "token": os.getenv("GEWECHAT_TOKEN"),
            "callback_url": os.getenv("CALLBACK_URL")
        }

        # Push Server Configuration
        self._config["push_server"] = {
            "host": os.getenv("PUSH_SERVER_HOST", "0.0.0.0"),
            "port": int(os.getenv("PUSH_SERVER_PORT", 5001))
        }

        # Database Configuration
        self._config["database"] = {
            "type": os.getenv("DB_TYPE", "mysql"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME")
        }

        # Redis Configuration
        self._config["redis"] = {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", 6379)),
            "password": os.getenv("REDIS_PASSWORD", ""),
            "db": int(os.getenv("REDIS_DB", 0)),
            "key_prefix": os.getenv("REDIS_KEY_PREFIX", "")  # 新增这行
        }

    def _setup_logging(self):
        """Setup logging configuration"""
        log_level_str = self._config["logging"]["level"]
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        # 配置根日志记录器
        logging.basicConfig(
            level=log_level,
            format='[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 设置所有已存在的日志记录器的级别
        for logger_name in logging.root.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            logger.setLevel(log_level)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._config.copy()

# Global instance
config = ConfigManager()