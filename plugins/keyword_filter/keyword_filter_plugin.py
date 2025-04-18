from typing import Optional
from bot.context import Context, ProcessState
from plugins.base import Plugin
from common.log import logger

class KeywordFilterPlugin(Plugin):
    """关键词过滤插件"""
    
    async def process(self, context: Context) -> Optional[Context]:
        keywords = self.config.get("keywords", [])
        if not keywords:
            return context
            
        for keyword in keywords:
            if keyword in context.content:
                context.data["matched_keyword"] = keyword
                # 设置回复消息
                reply_template = self.config.get("reply_template", "检测到关键词: {keyword}")
                context.rtn_content = reply_template.format(keyword=keyword)
                logger.info(f"Keyword matched: {keyword}")
                # 终止处理链但执行默认回复
                context.process_state = ProcessState.FINISHED_WITH_DEFAULT
                return context
                
        logger.debug("No keyword matched, continuing processing chain")
        context.process_state = ProcessState.CONTINUE
        return context
