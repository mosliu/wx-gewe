from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from enum import Enum
from .message import Message

class ContextType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    LOCATION = "location"
    LINK = "link"
    EVENT = "event"

class ProcessState(Enum):
    CONTINUE = 1  # 继续处理链，最后执行默认处理
    FINISHED_WITH_DEFAULT = 2  # 终止处理链，执行默认处理
    FINISHED = 3  # 终止处理链，不执行默认处理

@dataclass
class Context:
    type: ContextType
    content: Any  # 接收到的原始消息内容
    rtn_content: Any = None  # 要返回的消息内容
    msg: Optional[Message] = None
    is_group: bool = False
    receiver: Optional[str] = None
    sender: Optional[str] = None
    data: Dict = field(default_factory=dict)
    process_state: ProcessState = ProcessState.CONTINUE  # 默认继续处理

    def __getitem__(self, key):
        return self.data.get(key)

    def __setitem__(self, key, value):
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)