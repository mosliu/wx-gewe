"""
AI Plugin 默认配置
"""

DEFAULT_CONFIG = {
    "enabled": True,
    "priority": 50,  # 优先级，数字越小优先级越高
    "models": {
        "gpt-4o": {
            "description": "GPT-4o - 最新的多模态模型，支持图像和文本",
            "max_tokens": 8192
        },
        "gpt-4o-mini": {
            "description": "GPT-4o-mini - 强大的语言模型",
            "max_tokens": 8192
        }
    }
}
