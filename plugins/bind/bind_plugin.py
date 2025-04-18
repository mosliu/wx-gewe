from datetime import datetime
from typing import Optional
import re
from bot.context import Context, ProcessState
from plugins.base import Plugin
from common.log import logger
from common.database_manager import db_manager
from common.redis_manager import redis_manager
from common.models import CustomBindKey, WxUser, WxGroup
from common.cache_manager import CacheManager
from plugins.user_group_validator.user_group_validator_plugin import UserGroupValidatorPlugin

class BindPlugin(Plugin):
    """绑定插件"""
    
    GROUP_CACHE_KEY_PREFIX = "gewe-auth:group:"
    USER_CACHE_KEY_PREFIX = "gewe-auth:user:"
    CACHE_EXPIRE = 1800  # 30分钟过期
    
    async def process(self, context: Context) -> Optional[Context]:
        if not context.content.startswith('/bind'):
            context.process_state = ProcessState.CONTINUE
            return context

        match = re.search(r'/bind\s+(\S+)', context.content)
        if not match:
            context.rtn_content = self.config.get("bind_help_message", "请输入正确的绑定格式：/bind <key>")
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context

        session = db_manager.get_session()
        redis_client = redis_manager.get_client()
        
        try:
            # 检查是否已经绑定
            if context.is_group:
                existing = session.query(WxGroup).filter_by(
                    wx_group_id=context.msg.room_id
                ).first()
                
                if existing:
                    group_name = await CacheManager.get_group_name(context.msg.room_id)
                    display_name = group_name or context.msg.room_id
                    context.rtn_content = f"群组 {display_name} 已经绑定，无需重复绑定"
                    context.process_state = ProcessState.FINISHED_WITH_DEFAULT
                    return context
            else:
                existing = session.query(WxUser).filter_by(
                    wx_user_id=context.msg.sender_id
                ).first()
                
                if existing:
                    display_name = context.msg.sender_nickname or context.msg.sender_id
                    context.rtn_content = f"用户 {display_name} 已经绑定，无需重复绑定"
                    context.process_state = ProcessState.FINISHED_WITH_DEFAULT
                    return context

            # 验证绑定key
            bind_key = match.group(1)
            key_record = session.query(CustomBindKey).filter_by(
                bind_key=bind_key,
                status=0
            ).first()

            if not key_record:
                context.rtn_content = "无效的绑定key或该key已被使用"
                context.process_state = ProcessState.FINISHED_WITH_DEFAULT
                return context

            key_record.status = 1
            key_record.bind_time = datetime.now()

            if context.is_group:
                group_name = await CacheManager.get_group_name(context.msg.room_id)
                logger.info(f"Binding group: id={context.msg.room_id}, name={group_name}")
                
                group = WxGroup(
                    wx_group_id=context.msg.room_id,
                    wx_group_name=group_name,
                    customer_id=key_record.customer_id
                )
                session.add(group)
                
                key_record.bind_type = 2
                key_record.bind_id = context.msg.room_id
                
                # 更新权限缓存
                cache_key = f"{self.GROUP_CACHE_KEY_PREFIX}{context.msg.room_id}"
                redis_client.setex(cache_key, self.CACHE_EXPIRE, "1")
                
                display_name = group_name or context.msg.room_id
                context.rtn_content = (
                    f"群组 {display_name} 绑定成功！\n"
                    f"客户ID: {key_record.customer_id}\n"
                    "现在可以开始使用机器人服务了"
                )
            else:
                wx_username = context.msg.sender_nickname or context.msg.sender_id
                user = WxUser(
                    wx_user_id=context.msg.sender_id,
                    wx_username=wx_username,
                    customer_id=key_record.customer_id
                )
                session.add(user)
                
                key_record.bind_type = 1
                key_record.bind_id = context.msg.sender_id
                
                # 更新权限缓存
                cache_key = f"{self.USER_CACHE_KEY_PREFIX}{context.msg.sender_id}"
                redis_client.setex(cache_key, self.CACHE_EXPIRE, "1")
                
                context.rtn_content = (
                    f"用户 {wx_username} 绑定成功！\n"
                    f"客户ID: {key_record.customer_id}\n"
                    "现在可以开始使用机器人服务了"
                )

            session.commit()
            logger.info(f"Bind successful for key {bind_key}")
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context

        except Exception as e:
            session.rollback()
            logger.error_with_trace(f"Error in bind process: {str(e)}")
            context.rtn_content = "绑定过程中发生错误，请稍后重试"
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
            
        finally:
            db_manager.close_session(session)