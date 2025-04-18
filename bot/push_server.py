import json
import web
import os
from typing import Optional
from common.log import logger

class PushServer:
    def __init__(self, robot, host="0.0.0.0", port=5001):
        self.robot = robot
        self.host = host
        self.port = port
        
        # 获取项目根目录（bot的父目录）
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.info(f"PushServer base directory: {self.base_dir}")
        
        # 检查静态文件目录是否存在
        # static_dir = os.path.join(self.base_dir, 'static')
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/')
        if not os.path.exists(static_dir):
            logger.warning(f"Static directory does not exist: {static_dir}")
            os.makedirs(static_dir)
            logger.info(f"Created static directory: {static_dir}")
        
        # 设置模板目录（使用绝对路径）
        render = web.template.render(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates/'),
                                   globals={'server_host': f"{host}:{port}"})

        # 配置静态文件路径
        web.config.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/')  # 指定静态文件目录名
        # 配置静态文件处理
        web.config.debug = False  # 关闭调试模式以避免重载问题
        
        # 使用web.py的静态文件处理
        urls = (
            '/statics/(.*)', StaticHandler,
            '/push', 'PushHandler',
            '/', 'IndexHandler'
        )
        
        # 创建应用
        self.app = web.application(urls, globals())
        
        # 将robot实例、render和static_dir注入到handlers
        PushHandler.robot = self.robot
        IndexHandler.render = render
        StaticHandler.static_dir = static_dir
        
        # 添加调试日志
        logger.info(f"Initialized routes: {urls}")
        logger.info(f"Static files will be served from: {static_dir}")

    def start(self):
        """启动推送服务器"""
        logger.info(f"Starting push server on {self.host}:{self.port}")
        web.httpserver.runsimple(self.app.wsgifunc(), (self.host, self.port))

class IndexHandler:
    """处理首页请求"""
    render = None

    def GET(self):
        return self.render.index()

class StaticHandler:
    static_dir = None
    
    def GET(self, path):
        try:
            # 构建完整的文件路径
            file_path = os.path.join(self.static_dir, path)
            
            # 安全检查：确保文件路径在static目录内
            if not os.path.abspath(file_path).startswith(os.path.abspath(self.static_dir)):
                raise web.forbidden()
                
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                raise web.notfound()
                
            # 设置content type
            ext = os.path.splitext(path)[1].lower()
            content_types = {
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.ico': 'image/x-icon'
            }
            web.header('Content-Type', content_types.get(ext, 'application/octet-stream'))
            
            # 返回文件内容
            with open(file_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error serving static file {path}: {e}", exc_info=True)
            raise web.notfound()

class PushHandler:
    robot = None

    def POST(self):
        """处理推送请求"""
        try:
            web.header('Content-Type', 'application/json')
            data = json.loads(web.data())
            
            text = data.get('text')
            room_id = data.get('room_id')
            
            if not text or not room_id:
                return self._make_response(False, "Missing required parameters: text or room_id")
            
            if not self.robot:
                return self._make_response(False, "Robot instance not available")
                
            result = self.robot.client.post_text(
                self.robot.app_id,
                room_id,
                text
            )
            
            if result.get('ret') == 200:
                return self._make_response(True, "Message sent successfully")
            else:
                return self._make_response(False, f"Failed to send message: {result}")
                
        except Exception as e:
            logger.error(f"Error processing push request: {e}")
            return self._make_response(False, f"Error: {str(e)}")
    
    def _make_response(self, success: bool, message: str) -> str:
        return json.dumps({
            "success": success,
            "message": message
        })