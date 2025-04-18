from typing import Optional, Dict
from bot.context import Context, ProcessState
from bot.robot import robot_instance
from plugins.base import Plugin
from common.log import logger
from common.database_manager import db_manager
from common.models import WxUser, WxGroup
from common.redis_manager import redis_manager
from common.cache_manager import CacheManager


class UserGroupValidatorPlugin(Plugin):
    """用户和群组验证插件"""
    
    CACHE_EXPIRE = 1800  # 30分钟过期时间
    GROUP_CACHE_KEY_PREFIX = "gewe-auth:group:"
    USER_CACHE_KEY_PREFIX = "gewe-auth:user:"

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.robot = None  # 将在 set_robot 中设置
        
        if self.config.get("clear_cache_on_startup", False):
            self.clear_auth_cache()
    
    # Remove set_robot method as it's now in the base class

    def clear_auth_cache(self) -> None:
        """清除所有认证相关的缓存"""
        CacheManager.clear_all_cache()
        logger.info("[UserGroupValidator] Cleared auth cache")

    async def check_group_auth(self, room_id: str, redis_client) -> bool:
        """检查群组权限，先查Redis，没有则查MySQL并缓存结果"""
        cache_key = redis_manager.get_prefixed_key(f"{self.GROUP_CACHE_KEY_PREFIX}{room_id}")
        cached_result = redis_client.get(cache_key)
        
        if cached_result is not None:
            return cached_result == "1"

        # 查询MySQL并缓存结果
        session = db_manager.get_session()
        try:
            group = session.query(WxGroup).filter_by(wx_group_id=room_id).first()
            is_authorized = group is not None
            
            redis_client.setex(
                cache_key,
                self.CACHE_EXPIRE,
                "1" if is_authorized else "0"
            )
            
            return is_authorized
        finally:
            db_manager.close_session(session)

    async def check_user_auth(self, user_id: str, redis_client) -> bool:
        """检查用户权限，先查Redis，没有则查MySQL并缓存结果"""
        cache_key = redis_manager.get_prefixed_key(f"{self.USER_CACHE_KEY_PREFIX}{user_id}")
        cached_result = redis_client.get(cache_key)
        
        if cached_result is not None:
            return cached_result == "1"

        # 查询MySQL并缓存结果
        session = db_manager.get_session()
        try:
            user = session.query(WxUser).filter_by(wx_user_id=user_id).first()
            is_authorized = user is not None
            
            redis_client.setex(
                cache_key,
                self.CACHE_EXPIRE,
                "1" if is_authorized else "0"
            )
            
            return is_authorized
        finally:
            db_manager.close_session(session)

    async def process(self, context: Context) -> Optional[Context]:
        try:
            # 首先检查配置中是否允许未授权访问
            if self.config.get("allow_unauthorized", False):
                context.process_state = ProcessState.CONTINUE
                return context

            redis_client = redis_manager.get_client()

            if context.is_group:
                # 先检查配置中的白名单群组
                allowed_groups = self.config.get("allowed_groups", [])
                room_id = context.msg.room_id

                # 安全地获取群名
                room_name = None
                if self.robot is not None:
                    try:
                        room_name = await CacheManager.get_group_name(room_id)
                    except Exception as e:
                        logger.error_with_trace(f"Failed to get room name for {room_id}: {e}")

                # 检查群ID或群名是否在白名单中
                if allowed_groups and (room_id in allowed_groups or (room_name and room_name in allowed_groups)):
                    logger.debug(f"Group {room_id} ({room_name or 'unknown name'}) found in config whitelist")
                    context.process_state = ProcessState.CONTINUE
                    return context

                # 检查Redis缓存和MySQL
                if await self.check_group_auth(room_id, redis_client):
                    logger.info(f"Valid group message from {room_id}")
                    context.process_state = ProcessState.CONTINUE
                    return context

                # 不在白名单和数据库中的群消息直接抛弃
                logger.debug(f"Discarding message from unauthorized group: {room_id}")
                return None
            else:
                # 先检查配置中的白名单用户
                allowed_users = self.config.get("allowed_users", [])
                if allowed_users and context.msg.sender_id in allowed_users:
                    logger.debug(f"User {context.msg.sender_id} found in config whitelist")
                    context.process_state = ProcessState.CONTINUE
                    return context

                # 检查Redis缓存和MySQL
                if await self.check_user_auth(context.msg.sender_id, redis_client):
                    logger.info(f"Valid user message from {context.msg.sender_id}")
                    context.process_state = ProcessState.CONTINUE
                    return context

                # 未授权消息处理
                unauthorized_msg = self.config.get("unauthorized_message", "未授权的访问")
                logger.debug(f"Unauthorized {'group' if context.is_group else 'user'} message")
                if self.config.get("return_unauthorized_message", False):
                    context.rtn_content = unauthorized_msg
                    context.process_state = ProcessState.FINISHED_WITH_DEFAULT
                    return context

                # 直接终止处理且不回复
                context.process_state = ProcessState.FINISHED
                return context

        except Exception as e:
            logger.error_with_trace(f"Error in {self.__class__.__name__}: {str(e)}")
            return context  # 发生错误时继续处理链
