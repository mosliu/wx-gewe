from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config.config_manager import config
from common.db_base import Base
from common.log import logger

# 导入models以确保表被创建
from common.models import WxUser, WxGroup

class DatabaseManager:
    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_db(self):
        if not self._engine:
            db_config = config.get("database")
            if not db_config:
                raise ValueError("Database configuration not found")
                
            db_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            logger.info(f"Initializing database connection to {db_config['host']}:{db_config['port']}/{db_config['database']}")
            
            self._engine = create_engine(
                db_url,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_pre_ping=True,  # Enable connection health checks
                pool_timeout=30,     # Connection timeout of 30 seconds
            )
            self._session_factory = scoped_session(sessionmaker(bind=self._engine))
            Base.metadata.create_all(self._engine)

    def get_session(self):
        if not self._session_factory:
            self.init_db()
        return self._session_factory()

    def close_session(self, session):
        if session:
            try:
                session.close()
            except Exception as e:
                logger.error(f"Error closing session: {e}")

# 创建全局实例
db_manager = DatabaseManager() 