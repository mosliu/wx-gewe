import os
import re
import base64
from typing import Optional, List, Dict, Any
import aiohttp
import json
from bot.context import Context, ContextType, ProcessState
from plugins.base import Plugin
from common.log import logger
from dotenv import load_dotenv
from common.event_bus import EventBus

# Load environment variables
load_dotenv()

class AIPlugin(Plugin):
    """AI 插件 - 使用 OpenAI API 处理消息"""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self._default_model = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o")
        
        # 订阅模型更新事件
        EventBus.subscribe("model_updated", self._on_model_updated)
        
        logger.info(f"[AI Plugin] Initialized with default model: {self._default_model}")
    
    @property
    def default_model(self) -> str:
        return self._default_model
    
    def _on_model_updated(self, new_model: str):
        """处理模型更新事件"""
        logger.info(f"[AI Plugin] Updating default model from {self._default_model} to {new_model}")
        self._default_model = new_model
    
    async def process(self, context: Context) -> Optional[Context]:
        """处理上下文"""
        # 检查是否是文本消息或图片消息
        is_text = context.type == ContextType.TEXT
        is_image = context.type == ContextType.IMAGE
        
        # 如果不是文本或图片消息，则跳过
        if not (is_text or is_image):
            return context
        
        # 如果是图片消息，检查是否有文本内容
        if is_image and not hasattr(context, 'content'):
            return context
        
        # 检查激活词
        activation_prefixes = ["ai!", "小福"]
        is_activated = False
        prefix_used = None
        
        for prefix in activation_prefixes:
            if context.content.startswith(prefix):
                is_activated = True
                prefix_used = prefix
                break
        
        # 如果是文本消息，检查是否包含激活词
        if is_text and not is_activated:
            return context
        
        # 如果是图片消息，检查是否有文本内容并且包含激活词
        if is_image and (not hasattr(context, 'content') or not is_activated):
            return context

        # 移除前缀
        prefix_length = len(prefix_used)
        query = context.content[prefix_length:].strip() if is_activated else "请分析这张图片"
        
        # 如果没有内容，返回帮助信息
        if not query and is_text:
            context.rtn_content = self._get_help_text()
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            return context
        
        # 检查是否有模型切换命令
        model = self.default_model
        model_match = re.match(r'^model:(\S+)\s+(.+)$', query)
        if model_match:
            model = model_match.group(1)
            query = model_match.group(2)
            logger.info(f"[AI Plugin] Using model: {model}")
        
        # 处理消息
        try:
            # 准备文件列表
            files = []
            
            # 如果是图片消息，添加图片到文件列表
            if is_image and hasattr(context, 'msg') and context.msg:
                image_path = context.msg.content if hasattr(context.msg, 'content') else None
                if image_path and os.path.exists(image_path):
                    files.append({"type": "image", "path": image_path})
                    logger.info(f"[AI Plugin] Added image from context: {image_path}")
            
            # 检查是否有额外的图片或文件
            if hasattr(context, 'msg') and context.msg and hasattr(context.msg, 'extra_data') and 'files' in context.msg.extra_data:
                extra_files = context.msg.extra_data['files']
                if extra_files:
                    files.extend(extra_files)
                    logger.info(f"[AI Plugin] Added {len(extra_files)} files from extra_data")
            
            # 调用 OpenAI API
            response = await self._call_openai_api(query, model, files)
            
            # 设置回复内容
            context.rtn_content = response
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
            
            logger.info(f"[AI Plugin] Successfully processed query with model {model}")
            
        except Exception as e:
            logger.error(f"[AI Plugin] Error processing query: {str(e)}")
            context.rtn_content = f"处理请求时出错: {str(e)}"
            context.process_state = ProcessState.FINISHED_WITH_DEFAULT
        
        return context
    
    async def _call_openai_api(self, query: str, model: str, files: List[Dict] = None) -> str:
        """调用 OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建消息
        messages = [{"role": "user", "content": []}]
        
        # 添加文本内容
        messages[0]["content"].append({
            "type": "text",
            "text": query
        })
        
        # 添加图片或文件内容
        if files:
            for file in files:
                if file.get("type") == "image":
                    # 处理图片
                    image_path = file.get("path")
                    if image_path and os.path.exists(image_path):
                        with open(image_path, "rb") as img_file:
                            base64_image = base64.b64encode(img_file.read()).decode('utf-8')
                            
                            messages[0]["content"].append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            })
        
        # 获取模型配置
        model_config = self.config.get("models", {}).get(model, {"max_tokens": 4000})
        max_tokens = model_config.get("max_tokens", 4000)
        
        # 构建请求数据
        data = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": max_tokens
        }
        
        # 记录请求信息
        logger.info(f"[AI Plugin] API Request:")
        logger.info(f"  - Model: {model}")
        logger.info(f"  - Query: {query}")
        logger.info(f"  - Max Tokens: {max_tokens}")
        logger.info(f"  - Files: {len(files) if files else 0} files attached")
        logger.info(f"  - Temperature: {data['temperature']}")

        # 发送请求
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_base}/chat/completions", headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"[AI Plugin] API Error: Status {response.status}")
                    logger.error(f"[AI Plugin] Error Details: {error_text}")
                    raise Exception(f"API request failed with status {response.status}: {error_text}")
                
                result = await response.json()
                
                # 记录响应信息
                if "usage" in result:
                    usage = result["usage"]
                    logger.info(f"[AI Plugin] API Response Usage:")
                    logger.info(f"  - Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
                    logger.info(f"  - Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
                    logger.info(f"  - Total Tokens: {usage.get('total_tokens', 'N/A')}")

                if "choices" in result and len(result["choices"]) > 0:
                    response_content = result["choices"][0]["message"]["content"]
                    logger.info(f"[AI Plugin] Response Content Length: {len(response_content)} chars")
                    return response_content
                else:
                    logger.error(f"[AI Plugin] Invalid API Response: {result}")
                    raise Exception("Invalid response from API")
    
    def _get_help_text(self) -> str:
        """获取帮助文本"""
        help_text = "AI 助手使用说明:\n\n"
        help_text += "1. 基本使用: \n"
        help_text += "   - ai! 你的问题\n"
        help_text += "   - 小福 你的问题\n"
        help_text += "2. 切换模型: \n"
        help_text += "   - ai! model:模型名称 你的问题\n"
        help_text += "   - 小福 model:模型名称 你的问题\n"
        help_text += "   例如: ai! model:gpt-4o-mini 帮我写一首诗\n\n"
        help_text += f"当前默认模型: {self.default_model}\n"
        help_text += "支持发送图片进行分析\n"
        
        return help_text
