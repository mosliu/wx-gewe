from typing import Dict, Optional
from common.redis_manager import redis_manager
from common.log import logger

class CacheManager:
    """缓存管理类"""
    
    # 缓存key前缀
    USER_INFO_PREFIX = "user_info:"
    GROUP_INFO_PREFIX = "group_info:"
    CACHE_EXPIRE = 1800  # 30分钟过期时间

    _robot = None  # 类变量存储robot实例

    @classmethod
    def init(cls, robot) -> None:
        """初始化缓存管理器"""
        cls._robot = robot
        logger.info("CacheManager initialized with robot instance")

    @classmethod
    def clear_all_cache(cls) -> None:
        """清除所有缓存"""
        redis_client = redis_manager.get_client()
        patterns = [
            redis_manager.get_prefixed_key("user_info:*"),
            redis_manager.get_prefixed_key("group_info:*"),
            redis_manager.get_prefixed_key("chatroom_names"),
            redis_manager.get_prefixed_key("chatroom_ids"),
            redis_manager.get_prefixed_key("gewe-auth:*")
        ]
        for pattern in patterns:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys for pattern: {pattern}")

    @classmethod
    def cache_user_info(cls, user_id: str, user_info: Dict) -> None:
        """缓存用户信息"""
        redis_client = redis_manager.get_client()
        cache_key = redis_manager.get_prefixed_key(f"{cls.USER_INFO_PREFIX}{user_id}")
        redis_client.hmset(cache_key, user_info)
        redis_client.expire(cache_key, cls.CACHE_EXPIRE)

    @classmethod
    def get_cached_user_info(cls, user_id: str) -> Optional[Dict]:
        """获取缓存的用户信息"""
        redis_client = redis_manager.get_client()
        cache_key = redis_manager.get_prefixed_key(f"{cls.USER_INFO_PREFIX}{user_id}")
        user_info = redis_client.hgetall(cache_key)
        return user_info if user_info else None

    @classmethod
    def cache_group_info(cls, group_id: str, group_info: Dict) -> None:
        """缓存群组信息"""
        try:
            redis_client = redis_manager.get_client()
            cache_key = redis_manager.get_prefixed_key(f"{cls.GROUP_INFO_PREFIX}{group_id}")
            
            if group_info:
                redis_client.hmset(cache_key, group_info)
                redis_client.expire(cache_key, cls.CACHE_EXPIRE)
                
                group_name = group_info.get('nickName')
                if group_name:
                    logger.info(f"Caching group mapping: {group_name} -> {group_id}")
                    pipe = redis_client.pipeline()
                    chatroom_names_key = redis_manager.get_prefixed_key("chatroom_names")
                    chatroom_ids_key = redis_manager.get_prefixed_key("chatroom_ids")
                    pipe.hset(chatroom_names_key, group_name, group_id)
                    pipe.hset(chatroom_ids_key, group_id, group_name)
                    pipe.expire(chatroom_names_key, cls.CACHE_EXPIRE)
                    pipe.expire(chatroom_ids_key, cls.CACHE_EXPIRE)
                    pipe.execute()
        except Exception as e:
            logger.error_with_trace(f"Error caching group info for {group_id}: {e}")

    @classmethod
    def get_cached_group_info(cls, group_id: str) -> Optional[Dict]:
        """获取缓存的群组信息"""
        redis_client = redis_manager.get_client()
        cache_key = redis_manager.get_prefixed_key(f"{cls.GROUP_INFO_PREFIX}{group_id}")
        group_info = redis_client.hgetall(cache_key)
        return group_info if group_info else None

    @classmethod
    async def get_group_name(cls, group_id: str) -> Optional[str]:
        """获取群组名称，优先从缓存获取，没有则从API获取并缓存"""
        redis_client = redis_manager.get_client()
        room_name = redis_client.hget(redis_manager.get_prefixed_key("chatroom_ids"), group_id)
        
        if room_name:
            return room_name
        
        # Redis没有，从API获取（如果提供了robot实例）
        try:
            room_name = await cls._robot.get_room_name_by_id(group_id)
            if room_name:
                # 更新缓存
                pipe = redis_client.pipeline()
                pipe.hset(redis_manager.get_prefixed_key("chatroom_names"), room_name, group_id)
                pipe.hset(redis_manager.get_prefixed_key("chatroom_ids"), group_id, room_name)
                pipe.expire(redis_manager.get_prefixed_key("chatroom_names"), cls.CACHE_EXPIRE)
                pipe.expire(redis_manager.get_prefixed_key("chatroom_ids"), cls.CACHE_EXPIRE)
                pipe.execute()

                logger.debug(f"Updated cache for group {group_id}: {room_name}")
                return room_name

        except Exception as e:
            logger.error(f"Error getting room name for {group_id}: {e}")

        return None

    @classmethod
    def get_group_id(cls, group_name: str) -> Optional[str]:
        """获取群组ID"""
        redis_client = redis_manager.get_client()
        return redis_client.hget(redis_manager.get_prefixed_key("chatroom_names"), group_name)

    @classmethod
    def check_cache_status(cls) -> None:
        """检查缓存状态"""
        try:
            redis_client = redis_manager.get_client()
            
            # 检查群组信息缓存
            group_keys = redis_client.keys(f"{cls.GROUP_INFO_PREFIX}*")
            logger.info(f"Found {len(group_keys)} cached group info entries")
            
            # 检查群名映射缓存
            chatroom_names = redis_client.hgetall("chatroom_names")
            chatroom_ids = redis_client.hgetall("chatroom_ids")
            logger.info(f"Chatroom names mapping: {chatroom_names}")
            logger.info(f"Chatroom IDs mapping: {chatroom_ids}")
            
            # 检查用户信息缓存
            user_keys = redis_client.keys(f"{cls.USER_INFO_PREFIX}*")
            logger.info(f"Found {len(user_keys)} cached user info entries")
        except Exception as e:
            logger.error(f"Error checking cache status: {e}")

    @classmethod
    def update_user_cache(cls, user_id: str, user_info: Dict) -> None:
        """更新用户缓存信息"""
        try:
            redis_client = redis_manager.get_client()
            cache_key = redis_manager.get_prefixed_key(f"{cls.USER_INFO_PREFIX}{user_id}")

            if user_info:
                redis_client.hmset(cache_key, user_info)
                redis_client.expire(cache_key, cls.CACHE_EXPIRE)
                logger.debug(f"Updated user cache for {user_id}")
        except Exception as e:
            logger.error(f"Error updating user cache for {user_id}: {e}")

    @classmethod
    def update_group_cache(cls, group_id: str, group_name: str) -> None:
        """更新群组缓存信息"""
        try:
            redis_client = redis_manager.get_client()

            if group_name:
                # 使用pipeline来确保原子性
                pipe = redis_client.pipeline()
                pipe.hset(redis_manager.get_prefixed_key("chatroom_names"), group_name, group_id)
                pipe.hset(redis_manager.get_prefixed_key("chatroom_ids"), group_id, group_name)
                pipe.expire(redis_manager.get_prefixed_key("chatroom_names"), cls.CACHE_EXPIRE)
                pipe.expire(redis_manager.get_prefixed_key("chatroom_ids"), cls.CACHE_EXPIRE)
                pipe.execute()
                logger.debug(f"Updated group cache mapping: {group_name} -> {group_id}")
        except Exception as e:
            logger.error(f"Error updating group cache for {group_id}: {e}")
