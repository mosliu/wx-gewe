import os
import re
import uuid
import dotenv
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from bot.context import Context, ProcessState
from plugins.base import Plugin
from common.log import logger
from common.database_manager import db_manager
from common.models import AdminUser, CustomBindKey
from sqlalchemy import or_
from common.event_bus import EventBus
from common.redis_manager import redis_manager
from common.cache_manager import CacheManager

class AdminPlugin(Plugin):
    """管理员功能插件"""
    
    def __init__(self, config: Dict = None, plugin_manager=None):
        super().__init__(config)
        self.plugin_manager = plugin_manager
        self.admin_users_cache = {}  # 缓存已验证的管理员
        self.env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        
        # 确保配置存在
        if self.config is None:
            self.config = {}
        
        # 确保admin_commands配置存在
        if "admin_commands" not in self.config:
            self.config["admin_commands"] = {
                "add_bind": {
                    "command": "/add_bind",
                    "description": "创建新的绑定密钥",
                    "help_message": "格式: /add_bind <客户ID> <客户名称>"
                },
                "model": {
                    "command": "/model",
                    "description": "修改默认的OpenAI模型",
                    "help_message": "格式: /model <模型名称>"
                },
                "clear_cache": {
                    "command": "/clear_cache",
                    "description": "清除Redis缓存",
                    "help_message": "格式: /clear_cache"
                }
            }
        
        logger.info("[Admin Plugin] Initialized")

    async def clear_auth_cache(self) -> None:
        """清除Redis中的认证缓存"""
        CacheManager.clear_all_cache()
        logger.info("[Admin Plugin] Cleared auth cache")

    async def process(self, context: Context) -> Optional[Context]:
        """处理上下文"""
        # 检查是否是私聊消息
        if context.is_group:
            return context
        
        # 检查是否是文本消息
        if not context.content or not isinstance(context.content, str):
            return context
        
        # 获取命令
        content = context.content.strip()
        command_match = None
        
        # 检查是否是管理员命令
        for cmd_key, cmd_config in self.config.get("admin_commands", {}).items():
            cmd = cmd_config.get("command", f"/{cmd_key}")
            if content.startswith(cmd):
                command_match = (cmd_key, cmd)
                break
        
        # 如果不是管理员命令，继续处理链
        if not command_match:
            return context
        
        # 检查是否是管理员
        if not await self._is_admin(context.sender):
            logger.info(f"[Admin Plugin] Non-admin user {context.sender} attempted to use admin command: {content}")
            context.rtn_content = "您不是管理员，无权执行此命令。"
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context

        # 处理其他管理员命令
        cmd_key, cmd = command_match
        args = content[len(cmd):].strip()
        
        try:
            if cmd_key == "add_bind":
                return await self._handle_add_bind(context, args)
            elif cmd_key == "model":
                return await self._handle_model(context, args)
            elif cmd_key == "clear_cache":
                return await self._handle_clear_cache(context, args)
            else:
                # 未知命令
                context.rtn_content = f"未知的管理员命令: {cmd}"
                context.process_state = ProcessState.FINISHED_WITH_DEFAULT
                return context
        except Exception as e:
            logger.error(f"[Admin Plugin] Error handling command {cmd}: {str(e)}")
            context.rtn_content = f"处理命令时出错: {str(e)}"
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
    
    async def _handle_clear_cache(self, context: Context, args: str) -> Context:
        """处理清除缓存命令"""
        try:
            CacheManager.clear_all_cache()
            context.rtn_content = "所有缓存已清除"
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
        except Exception as e:
            logger.error(f"[Admin Plugin] Error clearing cache: {str(e)}")
            context.rtn_content = f"清除缓存时出错: {str(e)}"
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context

    async def _is_admin(self, user_id: str) -> bool:
        """检查用户是否是管理员"""
        # 检查缓存
        if user_id in self.admin_users_cache:
            return self.admin_users_cache[user_id]
        
        # 检查配置中的管理员列表
        config_admins = self.config.get("admin_users", [])
        if user_id in config_admins:
            self.admin_users_cache[user_id] = True
            return True
        
        # 检查数据库中的管理员
        session = db_manager.get_session()
        try:
            admin = session.query(AdminUser).filter_by(wx_user_id=user_id).first()
            is_admin = admin is not None
            self.admin_users_cache[user_id] = is_admin
            return is_admin
        except Exception as e:
            logger.error(f"[Admin Plugin] Error checking admin status: {str(e)}")
            return False
        finally:
            db_manager.close_session(session)
    
    async def _handle_add_bind(self, context: Context, args: str) -> Context:
        """处理添加绑定密钥命令
        格式: /add_bind
        """
        # 生成绑定密钥
        bind_key = str(uuid.uuid4())
        
        # 保存到数据库
        session = db_manager.get_session()
        try:
            # 创建新的绑定密钥记录
            new_key = CustomBindKey(
                bind_key=bind_key,
                created_time=datetime.now(),
                status=0  # 未绑定状态
            )
            session.add(new_key)
            session.commit()
            
            # 返回绑定密钥
            context.rtn_content = f"新的绑定密钥: {bind_key}"
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
            
        except Exception as e:
            session.rollback()
            logger.error(f"[Admin Plugin] Error creating bind key: {str(e)}")
            context.rtn_content = f"创建绑定密钥时出错: {str(e)}"
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
        finally:
            db_manager.close_session(session)
    
    async def _handle_model(self, context: Context, args: str) -> Context:
        """处理修改默认模型命令"""
        logger.debug(f"[Admin Plugin] Handling model command with args: {args}")
        logger.debug(f"[Admin Plugin] Plugin manager exists: {self.plugin_manager is not None}")
        
        # 解析参数
        model = args.strip()
        if not model:
            context.content = self.config.get("admin_commands", {}).get("model", {}).get(
                "help_message", "格式: /model <模型名称>")
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
        
        # 获取有效的模型列表
        valid_models = []
        try:
            if self.plugin_manager:
                logger.debug("[Admin Plugin] Attempting to get AI plugin config")
                ai_plugin_config = self.plugin_manager.get_plugin_config('ai')
                logger.debug(f"[Admin Plugin] AI plugin config: {ai_plugin_config}")
                
                if ai_plugin_config and 'config' in ai_plugin_config and 'models' in ai_plugin_config['config']:
                    valid_models = list(ai_plugin_config['config']['models'].keys())
                    logger.debug(f"[Admin Plugin] Retrieved models from AI plugin: {valid_models}")
                else:
                    logger.debug("[Admin Plugin] AI plugin config structure is not as expected")
            else:
                logger.debug("[Admin Plugin] Plugin manager is not available")
        except Exception as e:
            logger.warning(f"[Admin Plugin] Failed to get AI plugin config: {str(e)}", exc_info=True)
        
        # 如果无法从 AI 插件获取模型列表，使用默认值
        if not valid_models:
            valid_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
            logger.debug(f"[Admin Plugin] Using default models: {valid_models}")
        
        logger.debug(f"[Admin Plugin] Checking if model '{model}' is in valid models: {valid_models}")
        if model not in valid_models:
            context.rtn_content = f"无效的模型名称: {model}\n支持的模型: {', '.join(valid_models)}"
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
        
        # 处理模型切换命令
        return await self._handle_model_command(context, model)
    
    async def _handle_model_command(self, context: Context, model: str) -> Context:
        """处理模型切换命令"""
        try:
            # 更新环境变量
            dotenv.load_dotenv(self.env_path)
            current_model = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o")
            
            # 更新.env文件
            dotenv.set_key(self.env_path, "OPENAI_DEFAULT_MODEL", model)
            
            # 更新当前环境变量
            os.environ["OPENAI_DEFAULT_MODEL"] = model
            
            # 发布模型更新事件
            EventBus.publish("model_updated", model)
            
            # 返回成功消息
            context.rtn_content = f"默认模型已更新！\n原模型: {current_model}\n新模型: {model}"
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
            
        except Exception as e:
            logger.error(f"[Admin Plugin] Error updating model: {str(e)}")
            context.rtn_content = f"更新模型失败: {str(e)}"
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
