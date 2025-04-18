"""
Admin Plugin 默认配置
"""

DEFAULT_CONFIG = {
    "enabled": True,
    "priority": 5,  # 优先级，数字越小优先级越高，设置为5使其在bind插件之前执行
    "admin_commands": {
        "add_bind": {
            "command": "/add_bind",
            "description": "创建新的绑定密钥",
            "help_message": "格式: /add_bind <客户ID> <客户名称>"
        },
        "model": {
            "command": "/model",
            "description": "修改默认的OpenAI模型",
            "help_message": "格式: /model <模型名称>"
        }
    },
    "admin_users": [
        # 在这里添加默认管理员的微信ID
    ],
    "help_message": "管理员命令:\n/add_bind <客户ID> <客户名称> - 创建新的绑定密钥\n/model <模型名称> - 修改默认的OpenAI模型"
}
