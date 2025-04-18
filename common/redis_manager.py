import redis
import os
from config.config_manager import config
from common.log import logger

class RedisManager:
    _instance = None
    _redis_client = None
    _key_prefix = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_redis(self):
        if not self._redis_client:
            redis_config = config.get("redis")
            if not redis_config:
                raise ValueError("Redis configuration not found")
            
            self._key_prefix = redis_config.get('key_prefix', '')
            logger.info(f"Initializing Redis connection to {redis_config['host']}:{redis_config['port']} with prefix '{self._key_prefix}'")
            
            self._redis_client = redis.Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                password=redis_config['password'],
                db=redis_config['db'],
                decode_responses=True
            )

    def get_client(self):
        if not self._redis_client:
            self.init_redis()
        return self._redis_client

    def get_prefixed_key(self, key: str) -> str:
        """为key添加前缀"""
        return f"{self._key_prefix}{key}"

# 创建全局实例
redis_manager = RedisManager() 