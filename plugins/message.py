from dataclasses import dataclass, field
from typing import Any, Optional, Dict
from datetime import datetime
import time

@dataclass
class Message:
    type: str  # 消息类型
    content: Any  # 消息内容
    sender: str  # 发送者ID
    room_id: Optional[str] = None  # 群聊ID
    raw_data: Dict = field(default_factory=dict)  # 原始消息数据
    
    # 新增字段
    create_time: int = field(default_factory=lambda: int(time.time()))  # 消息创建时间
    msg_id: Optional[str] = None  # 消息ID
    is_group: bool = False  # 是否是群消息
    is_at: bool = False  # 是否被@
    
    # 发送者信息
    sender_nickname: Optional[str] = None  # 发送者昵称
    actual_user_id: Optional[str] = None  # 实际发送者ID（群消息中的发送者）
    actual_user_nickname: Optional[str] = None  # 实际发送者昵称
    
    # 接收者信息
    receiver: Optional[str] = None  # 接收者ID
    receiver_nickname: Optional[str] = None  # 接收者昵称
    
    # 其他元数据
    app_id: Optional[str] = None  # 应用ID
    extra_data: Dict = field(default_factory=dict)  # 附加数据

    def __post_init__(self):
        """初始化后处理"""
        # 确保extra_data存在
        if self.extra_data is None:
            self.extra_data = {}
            
        # 从raw_data中提取信息
        if self.raw_data:
            data = self.raw_data.get('Data', {})
            
            # 设置消息ID
            self.msg_id = str(data.get('NewMsgId', ''))
            
            # 设置创建时间
            if 'CreateTime' in data:
                self.create_time = data['CreateTime']
                
            # 设置群聊标志
            if self.room_id:
                self.is_group = "@chatroom" in self.room_id
                
            # 设置实际发送者信息（群消息）
            if self.is_group and 'Content' in data:
                content = data['Content'].get('string', '')
                if ':' in content:
                    self.actual_user_id = content.split(':', 1)[0]
                    
            # 检查是否被@（从PushContent中）
            if self.is_group:
                self.is_at = '在群聊中@了你' in data.get('PushContent', '')

    @property
    def create_time_str(self) -> str:
        """返回可读的创建时间"""
        return datetime.fromtimestamp(self.create_time).strftime('%Y-%m-%d %H:%M:%S')

    def set_sender_info(self, nickname: str):
        """设置发送者信息"""
        self.sender_nickname = nickname
        if self.is_group:
            self.actual_user_nickname = nickname

    def set_receiver_info(self, user_id: str, nickname: str):
        """设置接收者信息"""
        self.receiver = user_id
        self.receiver_nickname = nickname

    def is_expired(self, max_age_seconds: int = 300) -> bool:
        """检查消息是否过期"""
        return int(time.time()) - self.create_time > max_age_seconds

    def __str__(self) -> str:
        """返回消息的字符串表示"""
        msg_type = "Group" if self.is_group else "Private"
        sender = f"{self.sender_nickname}({self.sender})" if self.sender_nickname else self.sender
        if self.is_group and self.actual_user_nickname:
            sender = f"{self.actual_user_nickname}({self.actual_user_id})"
        
        return (f"[{msg_type} Message] "
                f"From: {sender}, "
                f"Content: {self.content}, "
                f"Time: {self.create_time_str}")