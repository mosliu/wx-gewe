import asyncio
import threading
from config.config_manager import config
from common.log import logger
from bot.robot import WeRobot
from bot.push_server import PushServer
from plugins.plugin_manager import plugin_manager
from common.database_manager import db_manager
from common.redis_manager import redis_manager
from common.cache_manager import CacheManager

async def main():
    try:
        logger.info("Starting application with log level: %s", config.get("logging.level"))

        # Initialize database and redis connections
        db_manager.init_db()
        redis_manager.init_redis()
        
        robot = WeRobot()
        logger.info("Initializing WeRobot...")
        
        # 初始化CacheManager
        CacheManager.init(robot)

        # 加载插件并设置 robot 实例
        for plugin in plugin_manager.get_plugins():
            robot.add_plugin(plugin)
        
        # 启动推送服务器（在新线程中）
        push_server_config = config.get("push_server")
        push_server = PushServer(
            robot,
            host=push_server_config["host"],
            port=push_server_config["port"]
        )
        push_thread = threading.Thread(target=push_server.start, daemon=True)
        push_thread.start()
        logger.info(f"Push server started on {push_server_config['host']}:{push_server_config['port']}")
        
        logger.info("Starting robot...")
        await robot.start()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())