from typing import Dict, Optional
from bot.context import Context
from bot.message import Message

class Plugin:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.robot = None  # Add robot instance variable
    
    def set_robot(self, robot):
        """Set robot instance for the plugin"""
        self.robot = robot
    
    async def process(self, context: Context) -> Optional[Context]:
        """
        处理上下文
        返回None: 终止处理链
        返回Context: 继续处理链
        """
        raise NotImplementedError