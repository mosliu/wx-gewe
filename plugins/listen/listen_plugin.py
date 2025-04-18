from typing import Optional
from bot.context import Context, ProcessState, ContextType
from plugins.base import Plugin
from common.log import logger
from common.redis_manager import redis_manager
from common.cache_manager import CacheManager

class ListenPlugin(Plugin):
    """群组监听插件"""
    
    LISTEN_MODE_KEY_PREFIX = "gewe-auth:listen_mode:"
    
    def __init__(self, config=None, plugin_manager=None):
        super().__init__(config)
        self.plugin_manager = plugin_manager
        
    async def process(self, context: Context) -> Optional[Context]:
        # 处理开启监听命令
        if context.content == self.config["listen_command"]:
            return await self._handle_listen_command(context)
            
        # 处理关闭监听命令
        if context.content == self.config["stop_listen_command"]:
            return await self._handle_stop_listen_command(context)
            
        # 处理监听模式下的消息
        if context.is_group:
            return await self._handle_group_message(context)
            
        context.process_state = ProcessState.CONTINUE
        return context
    
    async def _handle_listen_command(self, context: Context) -> Context:
        if context.is_group:
            context.rtn_content = self.config["messages"]["not_in_private"]
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
        
        redis_client = redis_manager.get_client()
        listen_key = redis_manager.get_prefixed_key(f"{self.LISTEN_MODE_KEY_PREFIX}{context.msg.sender_id}")
        
        # 设置监听模式
        redis_client.setex(listen_key, self.config["listen_expire"], "1")
        logger.info(f"User {context.msg.sender_id} enabled listen mode")
        
        context.rtn_content = self.config["messages"]["start_success"]
        context.process_state = ProcessState.FINISHED_WITH_DEFAULT
        return context
    
    async def _handle_stop_listen_command(self, context: Context) -> Context:
        if context.is_group:
            context.rtn_content = self.config["messages"]["not_in_private"]
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
            
        redis_client = redis_manager.get_client()
        listen_key = redis_manager.get_prefixed_key(f"{self.LISTEN_MODE_KEY_PREFIX}{context.msg.sender_id}")
        # listen_key = f"{self.LISTEN_MODE_KEY_PREFIX}{context.msg.sender_id}"
        
        # 检查是否在监听模式
        if not redis_client.exists(listen_key):
            context.rtn_content = self.config["messages"]["not_listening"]
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
            
        # 删除监听模式
        redis_client.delete(listen_key)
        logger.info(f"User {context.msg.sender_id} disabled listen mode")
        
        context.rtn_content = self.config["messages"]["stop_success"]
        context.process_state = ProcessState.FINISHED_WITH_DEFAULT
        return context
    
    async def _handle_group_message(self, context: Context) -> Context:
        redis_client = redis_manager.get_client()
        listen_key = redis_manager.get_prefixed_key(f"{self.LISTEN_MODE_KEY_PREFIX}{context.sender}")
        # listen_key = f"{self.LISTEN_MODE_KEY_PREFIX}{context.sender}"
        
        # 检查用户是否开启了监听模式
        if not redis_client.exists(listen_key):
            context.process_state = ProcessState.CONTINUE
            return context
            
        # 获取群组名称
        group_name = await CacheManager.get_group_name(context.msg.room_id)
        display_name = group_name or context.msg.room_id
        
        # 发送群组信息给用户
        notification = self.config["messages"]["notification_template"].format(
            group_name=display_name,
            group_id=context.msg.room_id
        )
        
        if self.robot:
            await self.robot.send_message(Context(
                type=ContextType.TEXT,  # 添加了type参数
                content=notification,
                receiver=context.sender,
                is_group=False,
                rtn_content=notification,
                process_state=ProcessState.FINISHED_WITH_DEFAULT,
                msg=context.msg
            ))
        else:
            logger.warning("Robot instance not available")
        
        context.process_state = ProcessState.CONTINUE
        return context