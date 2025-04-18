import os
import time
import json
import web
import asyncio
import requests
from typing import List, Dict, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv
from gewechat_client import GewechatClient
from .context import Context, ContextType, ProcessState
from .message import Message
from config.config_manager import config
from common.log import logger
from common.redis_manager import redis_manager
from common.cache_manager import CacheManager
from plugins.base import Plugin, Message

# 全局变量存储robot实例和事件循环
robot_instance = None
_event_loop = None


class CallbackHandler:
    """回调处理类"""

    def POST(self):
        web_data = web.data()
        logger.debug("[gewechat] receive data: %s", web_data)
        data = json.loads(web_data)

        if isinstance(data, dict) and 'testMsg' in data and 'token' in data:
            logger.info("[gewechat] 收到gewechat服务发送的回调测试消息")
            return "success"

        # 处理好友请求消息
        msg_type = data.get('Data', {}).get('MsgType')
        if msg_type == 37:  # 好友请求消息类型
            try:
                # 获取请求相关信息
                from_user = data.get('Data', {}).get('FromUserName')
                ticket = data.get('Data', {}).get('Ticket')
                content = data.get('Data', {}).get('Content', {}).get('string', '')

                if from_user and ticket and robot_instance:
                    # 使用robot_instance的client来调用add_contacts
                    response = robot_instance.client.add_contacts(
                        app_id=robot_instance.app_id,
                        user_id=from_user,
                        ticket=ticket,
                        scene=3  # 来自好友请求
                    )

                    if response.get('ret') == 200:
                        logger.info(f"[gewechat] Successfully accepted friend request from {from_user}")
                        # 获取用户信息并记录
                        brief_info = robot_instance.client.get_brief_info(robot_instance.app_id, [from_user])
                        if brief_info.get('ret') == 200 and brief_info.get('data'):
                            nickname = brief_info['data'][0].get('nickName', from_user)
                            logger.info(f"[gewechat] New friend added: {nickname} ({from_user})")
                            
                            # 可选：发送欢迎消息
                            welcome_msg = f"你好，我是AI助手。很高兴认识你！"
                            robot_instance.client.post_text(
                                robot_instance.app_id,
                                from_user,
                                welcome_msg
                            )
                    else:
                        logger.error(f"[gewechat] Failed to accept friend request: {response}")

                return "success"
            except Exception as e:
                logger.error(f"[gewechat] Error handling friend request: {e}")
                return "success"

        if msg_type == 51:
            logger.debug("[gewechat] ignore status sync message")
            return "success"

        if data.get('Wxid') == data.get('Data', {}).get('FromUserName', {}).get('string'):
            logger.debug("[gewechat] ignore message from myself")
            return "success"

        create_time = data.get('Data', {}).get('CreateTime', 0)
        if int(create_time) < int(time.time()) - 300:
            logger.debug("[gewechat] ignore expired message")
            return "success"

        content = data.get('Data', {}).get('Content', {}).get('string', '')

        # 处理类型49的消息（引用消息、小程序、公众号等）
        if msg_type == 49:
            try:
                # 找到XML声明的位置并移除前缀
                xml_start = content.find('<?xml version=')
                if xml_start != -1:
                    content_xml = content[xml_start:]
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(content_xml)
                    appmsg = root.find('appmsg')
                    if appmsg is not None:
                        msg_type_node = appmsg.find('type')
                        if msg_type_node is not None:
                            msg_subtype = msg_type_node.text
                            if msg_subtype == '57':  # 引用消息
                                refermsg = appmsg.find('refermsg')
                                if refermsg is not None:
                                    displayname = refermsg.find('displayname').text if refermsg.find('displayname') is not None else ''
                                    quoted_content = refermsg.find('content').text if refermsg.find('content') is not None else ''
                                    title = appmsg.find('title').text if appmsg.find('title') is not None else ''
                                    # 更新content为更友好的格式
                                    content = f"回复 {displayname} 【（引用）{quoted_content}】: {title}"
                            elif msg_subtype == '5':  # 链接消息
                                title = appmsg.find('title').text if appmsg.find('title') is not None else ''
                                url = appmsg.find('url').text if appmsg.find('url') is not None else ''
                                content = f"[链接] {title}\n{url}" if title else url
                            elif msg_subtype == '33':  # 小程序
                                title = appmsg.find('title').text if appmsg.find('title') is not None else ''
                                content = f"[小程序] {title}"
                            # 更新data中的content
                            data['Data']['Content']['string'] = content
            except Exception as e:
                logger.error_with_trace(f"[gewechat] Error parsing type 49 message: {e}")

        # 其他消息处理逻辑...
        from_user = data.get('Data', {}).get('FromUserName', {}).get('string', '')
        is_group = "@chatroom" in from_user
        logger.debug(f"[gewechat] {'Group' if is_group else 'Private'} message from {from_user}: {content}")

        # 构造消息对象
        message = Message(
            # type=str(data.get('Data', {}).get('MsgType')),
            # content=data.get('Data', {}).get('Content', {}).get('string', ''),
            type=str(msg_type),
            content=content,  # 使用处理后的content
            sender_id=data.get('Data', {}).get('FromUserName', {}).get('string'),
            room_id=data.get('Data', {}).get('FromUserName', {}).get('string'),
            raw_data=data,
            create_time=data.get('Data', {}).get('CreateTime', int(time.time())),
            msg_id=str(data.get('Data', {}).get('NewMsgId', '')),
            app_id=robot_instance.app_id if robot_instance else None
        )

        # 获取并设置发送者昵称
        sender_id = message.sender_id
        try:
            # 使用_robot_instance的client来获取用户信息
            brief_info_response = robot_instance.client.get_brief_info(robot_instance.app_id, [sender_id])
            if brief_info_response.get('ret') == 200 and brief_info_response.get('data'):
                brief_info = brief_info_response['data'][0]
                message.set_sender_info(brief_info.get('nickName', sender_id))

                # 如果是群聊消息，获取实际发送者信息
                if message.is_group:
                    content_str = data.get('Data', {}).get('Content', {}).get('string', '')
                    actual_user_id = content_str.split(':', 1)[0]
                    chatroom_member_list_response = robot_instance.client.get_chatroom_member_list(robot_instance.app_id, sender_id)
                    if chatroom_member_list_response.get('ret') == 200 and chatroom_member_list_response.get('data', {}).get('memberList'):
                        for member_info in chatroom_member_list_response['data']['memberList']:
                            if member_info['wxid'] == actual_user_id:
                                actual_nickname = member_info.get('displayName') or member_info.get('nickName', actual_user_id)
                                message.set_sender_info(actual_nickname)
                                break
        except Exception as e:
            logger.warning(f"Failed to get sender nickname for {sender_id}: {e}")
            message.set_sender_info(sender_id)  # 使用sender_id作为默认昵称

        # 忽略状态同步消息
        if message.type == "51":
            logger.debug("[gewechat] ignore status sync message")
            return "success"

        # 忽略来自自己的消息
        if data.get('Wxid') == message.sender_id:
            logger.debug("[gewechat] ignore message from myself")
            return "success"

        # 忽略过期消息
        if message.is_expired(300):  # 5分钟前的消息
            logger.debug("[gewechat] ignore expired message")
            return "success"

        # 忽略非文本消息（可选，根据需求配置）
        supported_types = {"1", "3", "34", "47", "49"}  # 文本、图片、语音、表情、链接/引用消息
        if message.type not in supported_types:
            logger.debug(f"[gewechat] ignore unsupported message type: {message.type}")
            return "success"

        # 处理群消息
        if message.is_group:
            content = message.content
            if ":" in content:
                actual_user_id, content = content.split(":", 1)
                message.actual_user_id = actual_user_id
                message.content = content.strip()

            # 检查是否被@（从PushContent中）
            push_content = data.get('Data', {}).get('PushContent', '')
            message.is_at = '在群聊中@了你' in push_content

        # 处理实际消息
        if robot_instance:
            # logger.debug(
            #     f"[gewechat] {'Group' if message.is_group else 'Private'} message from {message.sender}: {message.content}")

            # 创建新的事件循环来处理消息
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(robot_instance.process_message(message))
            except Exception as e:
                logger.error(f"[gewechat] Error processing message: {e}")
            finally:
                loop.close()

        return "success"

    def GET(self):
        """处理文件下载请求"""
        params = web.input(file="")
        file_path = params.file
        if not file_path:
            return "gewechat callback server is running"

        # 使用os.path.abspath清理路径
        clean_path = os.path.abspath(file_path)
        tmp_dir = os.path.abspath("tmp")

        # 检查文件路径是否在tmp目录下
        if not clean_path.startswith(tmp_dir):
            print(
                f"[gewechat] Forbidden access to file outside tmp directory: file_path={file_path}, clean_path={clean_path}, tmp_dir={tmp_dir}")
            raise web.forbidden()

        if os.path.exists(clean_path):
            # 获取文件类型
            file_type = "application/octet-stream"
            if clean_path.endswith('.mp3'):
                file_type = "audio/mpeg"
            elif clean_path.endswith(('.jpg', '.jpeg')):
                file_type = "image/jpeg"
            elif clean_path.endswith('.png'):
                file_type = "image/png"
            elif clean_path.endswith('.gif'):
                file_type = "image/gif"

            # 设置响应头
            web.header('Content-Type', file_type)
            web.header('Content-Disposition', f'attachment; filename="{os.path.basename(clean_path)}"')

            with open(clean_path, 'rb') as f:
                return f.read()
        else:
            print(f"[gewechat] File not found: {clean_path}")
            raise web.notfound()


class WeRobot:
    CREDENTIALS_FILE = "credentials.json"

    def __init__(self):
        global robot_instance
        robot_instance = self

        # 首先尝试从credentials.json加载配置
        credentials = self._load_credentials()
        
        gewechat_config = config.get("gewechat")
        if not gewechat_config:
            raise ValueError("[gewechat] GeWechat configuration not found")

        # credentials中的配置优先级高于.env
        self.base_url = gewechat_config["base_url"]
        if not self.base_url:
            raise ValueError("[gewechat] BASE_URL not set in configuration")

        self.token = credentials.get("token") or gewechat_config["token"]
        self.app_id = credentials.get("app_id") or gewechat_config["app_id"]
        self.callback_url = gewechat_config["callback_url"]
        
        # 创建初始客户端
        self.client = GewechatClient(self.base_url, self.token)

        self.plugins = []
        self.chatrooms = {}
        self.max_retries = 3
        self.retry_delay = 5

        # 检查缓存状态
        CacheManager.check_cache_status()

    def _load_credentials(self):
        """从credentials.json加载配置"""
        try:
            if os.path.exists(self.CREDENTIALS_FILE):
                with open(self.CREDENTIALS_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"[gewechat] Failed to load credentials: {e}")
        return {}

    def _save_credentials(self, token, app_id):
        """保存配置到credentials.json"""
        try:
            credentials = {
                "token": token,
                "app_id": app_id
            }
            with open(self.CREDENTIALS_FILE, 'w') as f:
                json.dump(credentials, f, indent=2)
            logger.info("[gewechat] Credentials saved successfully")
        except Exception as e:
            logger.error_with_trace(f"[gewechat] Failed to save credentials: {e}")

    def add_plugin(self, plugin: Plugin):
        if hasattr(plugin, 'set_robot'):
            plugin.set_robot(self)
        """添加插件"""
        self.plugins.append(plugin)

    def _compose_context(self, msg: Message) -> Optional[Context]:
        """根据消息构造上下文"""
        try:
            if not msg:
                logger.error("[gewechat] Cannot compose context for null message")
                return None

            if not hasattr(msg, 'type') or not msg.type:
                logger.error(f"[gewechat] Invalid message type: {msg}")
                return None

            context_type = ContextType.TEXT  # 默认类型

            # 消息类型映射
            type_mapping = {
                "3": ContextType.IMAGE,
                "34": ContextType.VOICE,
                # 可以添加更多类型映射
            }

            context_type = type_mapping.get(msg.type, ContextType.TEXT)

            return Context(
                type=context_type,
                content=msg.content,
                msg=msg,
                is_group=msg.is_group,
                receiver=msg.room_id if msg.is_group else msg.sender_id,
                sender=msg.actual_user_id if msg.is_group else msg.sender_id,
                data={
                    "app_id": msg.app_id,
                    "msg_id": msg.msg_id,
                    "create_time": msg.create_time,
                    "raw_data": msg.raw_data
                }
            )
        except Exception as e:
            logger.error_with_trace(f"[gewechat] Error composing context: {e}, Message: {msg}")
            return None

    async def process_message(self, message: Message):
        """处理消息通过插件链"""
        try:
            # 添加消息有效性检查
            if not message:
                logger.error("[gewechat] Received null message")
                return

            # 添加详细日志
            logger.debug(f"[gewechat] Processing message: type={message.type}, content={message.content}, sender={message.sender_id}")
            
            context = self._compose_context(message)
            if not context:
                logger.error("[gewechat] Failed to compose context for message")
                return
            
            current_context = context

            for plugin in self.plugins:
                plugin_name = plugin.__class__.__name__
                
                if current_context is None or current_context.process_state != ProcessState.CONTINUE:
                    logger.debug(
                        f"[Plugin Chain] Skipping plugins after {plugin_name} Context is None: {current_context is None} Process state: {current_context.process_state if current_context else 'N/A'}"
                    )
                    break

                try:
                    current_context = await plugin.process(current_context)
                    logger.debug(
                        f"[Plugin Chain] Exiting plugin: {plugin_name},New process state: {current_context.process_state if current_context else 'None'}"
                    )

                except Exception as e:
                    logger.error_with_trace(
                        f"[Plugin Chain] Exception in plugin {plugin_name}: {e} Current context: {current_context}\n"
                    )

            if current_context and (
                    current_context.process_state == ProcessState.CONTINUE or
                    current_context.process_state == ProcessState.FINISHED_WITH_DEFAULT
            ):
                logger.debug(
                    f"[Plugin Chain] Executing default handler,state: {current_context.process_state}\n"
                )
                await self.send_message(current_context)
            else:
                logger.debug(
                    f"[Plugin Chain] Skipping default handler,state: {current_context.process_state if current_context else 'None'}"
                )
        except Exception as e:
            logger.error_with_trace(f"[gewechat] Error processing message: {e}, Message: {message}")

    async def send_message(self, context: Context):
        """发送消息"""
        if context.receiver and context.rtn_content:  # 只有设置了rtn_content才发送
            try:
                # 构造发送消息的参数
                if context.is_group and context.msg.actual_user_id:
                    # 如果是群聊且需要@用户
                    ats = context.msg.actual_user_id
                else:
                    ats = ""

                result = self.client.post_text(
                    self.app_id,
                    context.receiver,
                    context.rtn_content,  # 使用rtn_content而不是content
                    ats
                )

                if result.get('ret') != 200:
                    logger.error(f"[gewechat] Failed to send message: {result}")
                else:
                    logger.info(f"[gewechat] Successfully sent message to {context.receiver}: {context.rtn_content}")

            except Exception as e:
                logger.error(f"[gewechat] Error sending message: {e}")

    def verify_callback_url(self):
        """验证回调URL是否可访问"""
        try:
            response = requests.get(self.callback_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Callback URL verification failed: {e}")
            return False

    def set_callback_with_retry(self):
        """带重试机制的回调设置"""
        for attempt in range(self.max_retries):
            try:
                # 先验证回调URL是否可访问
                if not self.verify_callback_url():
                    print(f"Callback URL {self.callback_url} is not accessible")
                    time.sleep(self.retry_delay)
                    continue

                callback_resp = self.client.set_callback(self.token, self.callback_url)
                if callback_resp.get("ret") == 200:
                    print("Callback set successfully")
                    return True
                elif callback_resp.get("ret") == 500:
                    print(f"Set callback failed (attempt {attempt + 1}/{self.max_retries}): {callback_resp}")
                    time.sleep(self.retry_delay)
                else:
                    print(f"Set callback failed with unexpected error: {callback_resp}")
                    return False
            except Exception as e:
                print(f"Error setting callback (attempt {attempt + 1}/{self.max_retries}): {e}")
                time.sleep(self.retry_delay)

        print("Failed to set callback after maximum retries")
        return False

    def setup_callback_server(self):
        """设置并启动回调服务器"""
        if not self.callback_url:
            raise ValueError("CALLBACK_URL not set in .env")

        parsed_url = urlparse(self.callback_url)
        path = parsed_url.path
        if not path:
            raise ValueError("Callback URL must include a path")

        # 启动回调设置线程
        def set_callback():
            time.sleep(3)  # 等待服务器启动
            if not self.set_callback_with_retry():
                print("Warning: Callback setup failed, but continuing...")

        import threading
        callback_thread = threading.Thread(target=set_callback, daemon=True)
        callback_thread.start()

        # 配置路由
        urls = (
            path, CallbackHandler,  # 直接使用类，而不是字符串
            path + '/', CallbackHandler
        )
        app = web.application(urls, globals())
        return app

    async def update_chatrooms(self):
        """更新群聊信息"""
        try:
            # 获取联系人列表，包含群聊信息
            contact_list_resp = self.client.fetch_contacts_list(self.app_id)
            if not contact_list_resp:
                logger.error("Failed to get contact list")
                return

            # 筛选出群聊
            chatrooms = [contact for contact in contact_list_resp 
                        if "@chatroom" in contact]  # 群聊ID包含 @chatroom
        
            if not chatrooms:
                logger.info("No chatrooms found")
                return

            # 分批获取群聊详细信息
            batch_size = 80
            batched_chatrooms = [
                chatrooms[i:i + batch_size] 
                for i in range(0, len(chatrooms), batch_size)
            ]

            redis_client = redis_manager.get_client()
            # 使用pipeline来批量更新
            pipe = redis_client.pipeline()

            for batch in batched_chatrooms:
                info = self.client.get_brief_info(self.app_id, batch)
                if info.get('ret') != 200 or not info.get('data'):
                    continue

                for room in info['data']:
                    room_id = room['userName']
                    room_name = room.get('nickName')
                    if room_name:
                        # 更新群名映射缓存
                        pipe.hset("chatroom_names", room_name, room_id)
                        pipe.hset("chatroom_ids", room_id, room_name)
                    
                    self.chatrooms[room_id] = room
                    # 缓存群组信息
                    logger.info(f"Caching group info for {room_id}: {room}")
                    CacheManager.cache_group_info(room_id, room)

            # 执行所有缓存更新
            pipe.execute()
            # 设置过期时间
            redis_client.expire("chatroom_names", CacheManager.CACHE_EXPIRE)
            redis_client.expire("chatroom_ids", CacheManager.CACHE_EXPIRE)

            logger.info(f"Updated {len(self.chatrooms)} chatrooms information")

        except Exception as e:
            logger.error(f"Error updating chatrooms: {e}")

    async def get_user_info(self, user_id: str) -> Optional[Dict]:
        """获取用户信息（优先从缓存获取）"""
        # 先从缓存获取
        cached_info = CacheManager.get_cached_user_info(user_id)
        if cached_info:
            return cached_info

        # 缓存未命中，从API获取
        try:
            info = self.client.get_brief_info(self.app_id, [user_id])
            if info.get('ret') == 200 and info.get('data'):
                user_info = info['data'][0]
                # 缓存用户信息
                CacheManager.cache_user_info(user_id, user_info)
                return user_info
        except Exception as e:
            logger.error(f"Error getting user info for {user_id}: {e}")
        
        return None

    async def get_group_info(self, group_id: str) -> Optional[Dict]:
        """获取群组信息（优先从缓存获取）"""
        # 先从缓存获取
        cached_info = CacheManager.get_cached_group_info(group_id)
        if cached_info:
            return cached_info

        # 缓存未命中，从API获取
        try:
            info = self.client.get_brief_info(self.app_id, [group_id])
            if info.get('ret') == 200 and info.get('data'):
                group_info = info['data'][0]
                # 缓存群组信息
                CacheManager.cache_group_info(group_id, group_info)
                return group_info
        except Exception as e:
            logger.error(f"Error getting group info for {group_id}: {e}")
        
        return None

    def get_room_id_by_name(self, room_name: str) -> str:
        """根据群名获取群ID"""
        redis_client = redis_manager.get_client()
        return redis_client.hget("chatroom_names", room_name)

    async def get_room_name_by_id(self, room_id: str) -> Optional[str]:
        """根据群ID获取群名"""
        try:
            info = self.client.get_brief_info(self.app_id, [room_id])
            if info.get('ret') == 200 and info.get('data'):
                room_info = info['data'][0]
                return room_info.get('nickName')
        except Exception as e:
            logger.error_with_trace(f"Error getting room name for {room_id}: {e}")
        return None

    async def handle_message(self, msg_data: Dict):
        """处理接收到的消息"""
        try:
            # 忽略非用户消息
            if msg_data.get('MsgType') == 51:  # 状态同步消息
                return

            # 忽略过期消息
            create_time = msg_data.get('CreateTime', 0)
            if int(create_time) < int(time.time()) - 300:  # 5分钟前的消息
                return

            # 获取并缓存发送者信息
            sender_id = msg_data.get('FromUserName', {}).get('string', '')
            if sender_id:
                user_info = self.client.get_brief_info(self.app_id, [sender_id])
                if user_info.get('ret') == 200 and user_info.get('data'):
                    logger.info(f"Caching user info for {sender_id}: {user_info['data'][0]}")
                    CacheManager.cache_user_info(sender_id, user_info['data'][0])

            # 如果是群消息，获取并缓存群信息
            if "@chatroom" in sender_id:
                group_info = self.client.get_brief_info(self.app_id, [sender_id])
                if group_info.get('ret') == 200 and group_info.get('data'):
                    logger.info(f"Caching group info for {sender_id}: {group_info['data'][0]}")
                    CacheManager.cache_group_info(sender_id, group_info['data'][0])

            # 构造Message对象
            is_group = "@chatroom" in msg_data.get('FromUserName', {}).get('string', '')
            content = msg_data.get('Content', {}).get('string', '')
            msg_type = str(msg_data.get('MsgType'))

            # 处理类型49的消息（引用消息、小程序、公众号等）
            if msg_type == "49":
                content_xml = content
                # 找到XML声明的位置并移除前缀
                xml_start = content_xml.find('<?xml version=')
                if xml_start != -1:
                    content_xml = content_xml[xml_start:]
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(content_xml)
                    appmsg = root.find('appmsg')
                    if appmsg is not None:
                        msg_type_node = appmsg.find('type')
                        if msg_type_node is not None:
                            if msg_type_node.text == '57':  # 引用消息
                                refermsg = appmsg.find('refermsg')
                                if refermsg is not None:
                                    displayname = refermsg.find('displayname').text if refermsg.find('displayname') is not None else ''
                                    quoted_content = refermsg.find('content').text if refermsg.find('content') is not None else ''
                                    title = appmsg.find('title').text if appmsg.find('title') is not None else ''
                                    # 构造更简洁的引用消息格式
                                    content = f"回复 {displayname}「{quoted_content}」: {title}"
                            elif msg_type_node.text == '5':  # 链接消息
                                title = appmsg.find('title').text if appmsg.find('title') is not None else "无标题"
                                if "加入群聊" in title:
                                    content = "[群邀请消息]"
                                else:
                                    url = appmsg.find('url').text if appmsg.find('url') is not None else ""
                                    content = f"[链接] {title}\n{url}"
                except ET.ParseError:
                    content = "[无法解析的消息]"

            message = Message(
                type=msg_type,
                content=content,  # 使用处理后的content
                sender_id=msg_data.get('FromUserName', {}).get('string'),
                room_id=msg_data.get('FromUserName', {}).get('string') if is_group else None,
                extra_data={
                    'raw_data': msg_data,
                    'is_group': is_group
                }
            )

            await self.process_message(message)

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def relogin(self):
        """重新登录并获取新token"""
        try:
            logger.info("[gewechat] Starting relogin process...")
            
            # 获取新token
            try:
                token_resp = self.client.get_token()
                if not isinstance(token_resp, dict):
                    logger.error("[gewechat] Invalid token response format")
                    return False
                
                if token_resp.get("ret") != 200:
                    logger.error(f"[gewechat] Failed to get new token: {token_resp}")
                    return False
                
                new_token = token_resp.get("data")
                if not new_token:
                    logger.error("[gewechat] Received empty token")
                    return False

                self.token = new_token
                self.client = GewechatClient(self.base_url, self.token)
            
                # 执行登录 - 使用空的app_id来创建新设备
                app_id, error_msg = self.client.login(app_id="")
                if error_msg:
                    logger.error(f"[gewechat] Login failed: {error_msg}")
                    return False

                if not app_id:
                    logger.error("[gewechat] Received empty app_id after login")
                    return False

                # 更新配置
                self.app_id = app_id
                gewechat_config = config.get("gewechat")
                if gewechat_config:
                    gewechat_config["token"] = self.token
                    gewechat_config["app_id"] = app_id
            
                # 保存新的凭证到文件
                self._save_credentials(self.token, app_id)
            
                logger.info(f"[gewechat] Relogin successful. New token: {self.token}, New app_id: {app_id}")
                return True
            
            except Exception as e:
                logger.error(f"[gewechat] Error during token acquisition: {e}")
                return False

        except Exception as e:
            logger.error(f"[gewechat] Critical error during relogin: {e}")
            return False

    async def check_and_handle_token(self):
        """检查token状态并处理"""
        try:
            if not self.token or not self.app_id:
                logger.warning("[gewechat] Token or app_id is empty, attempting to relogin")
                return await self.relogin()

            # 尝试API调用来验证token和设备状态
            try:
                result = self.client.fetch_contacts_list(self.app_id)
                if isinstance(result, dict):  # 确保result是字典类型
                    if result.get('ret') == 500 and isinstance(result.get('msg'), str) and "设备已离线" in result.get('msg'):
                        logger.warning("[gewechat] Device offline detected, initiating relogin")
                        return await self.relogin()
                    elif result.get('ret') == 401:  # token无效
                        logger.warning("[gewechat] Invalid token, initiating relogin")
                        return await self.relogin()
                    elif result.get('ret') != 200:
                        error_msg = result.get('msg', 'Unknown error')
                        logger.error(f"[gewechat] API check failed: {error_msg}")
                        return await self.relogin()  # 任何错误都尝试重新登录
                return True
            except RuntimeError as e:
                error_msg = str(e)
                logger.warning(f"[gewechat] Runtime error during token check: {error_msg}")
                return await self.relogin()  # 遇到运行时错误也尝试重新登录
            except Exception as e:
                logger.error(f"[gewechat] Unexpected error during token check: {e}")
                return await self.relogin()

        except Exception as e:
            logger.error(f"[gewechat] Critical error during token check: {e}")
            return False

    async def start(self):
        """启动机器人"""
        try:
            # 设置全局事件循环
            global _event_loop
            _event_loop = asyncio.get_running_loop()

            # 初始化检查，增加重试逻辑
            max_retries = 3
            retry_delay = 5
            
            for attempt in range(max_retries):
                if await self.check_and_handle_token():
                    break
                if attempt < max_retries - 1:  # 如果不是最后一次尝试
                    logger.warning(f"[gewechat] Token initialization failed, retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
            else:  # 所有重试都失败
                raise Exception("[gewechat] Failed to initialize valid token after multiple attempts")

            # 初始获取群聊信息
            await self.update_chatrooms()

            # 启动回调服务器
            logger.info("[gewechat] Starting callback server...")
            app = self.setup_callback_server()

            def run_web_server():
                parsed_url = urlparse(self.callback_url)
                port = parsed_url.port or 80
                logger.info(f"Starting web server on port {port} with path {parsed_url.path}")
                try:
                    web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))
                except Exception as e:
                    logger.error(f"Error starting web server: {e}")

            import threading
            server_thread = threading.Thread(target=run_web_server, daemon=True)
            server_thread.start()

            # 定期检查token状态
            while True:
                await asyncio.sleep(300)  # 每5分钟检查一次
                await self.check_and_handle_token()

        except Exception as e:
            logger.error(f"[gewechat] Error during startup: {e}")
            raise
