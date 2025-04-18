DEFAULT_CONFIG = {
    "listen_command": "/listen",
    "stop_listen_command": "/stop_listen",
    "listen_expire": 7200,  # 2小时过期
    "messages": {
        "start_success": "已开启群组监听模式，在群内发言时会收到群组信息。使用 /stop_listen 命令关闭监听模式。",
        "stop_success": "已关闭群组监听模式",
        "not_in_private": "请在私聊中使用此命令",
        "not_listening": "监听模式未开启",
        "notification_template": "您在群组「{group_name}」中发言\n群组ID: {group_id}"
    }
}