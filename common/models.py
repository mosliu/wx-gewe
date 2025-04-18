from sqlalchemy import Column, Integer, String, DateTime, Boolean
from common.db_base import Base
from datetime import datetime

class WxUser(Base):
    __tablename__ = 'wxuser'

    id = Column(Integer, primary_key=True, autoincrement=True)
    wx_user_id = Column(String(20), comment='wx_user_id')
    wx_username = Column(String(50), comment='wx_username')
    wx_user_comment = Column(String(255))
    customer_id = Column(String(50))
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

    def __repr__(self):
        return f"<WxUser(id={self.id}, wx_user_id='{self.wx_user_id}', wx_username='{self.wx_username}')>"


class WxGroup(Base):
    __tablename__ = 'wxgroup'

    id = Column(Integer, primary_key=True, autoincrement=True)
    wx_group_id = Column(String(20), comment='wx_group_id')
    wx_group_name = Column(String(50), comment='wx_group_name')
    wx_group_comment = Column(String(255))
    customer_id = Column(String(50))
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

    def __repr__(self):
        return f"<WxGroup(id={self.id}, wx_group_id='{self.wx_group_id}', wx_group_name='{self.wx_group_name}')>"


class CustomBindKey(Base):
    __tablename__ = 'custom_bind_key'

    id = Column(Integer, primary_key=True)
    customer_id = Column(String(50))
    customer = Column(String(50), comment='客户名称')
    bind_key = Column(String(255), comment='绑定key')
    created_time = Column(DateTime, comment='创建时间')
    bind_time = Column(DateTime, comment='绑定时间')
    status = Column(Integer, default=0, comment='绑定状态 0:未绑定 1:已绑定')
    bind_type = Column(Integer, comment='绑定类型 1:用户 2:群组')
    bind_id = Column(String(50), comment='绑定ID(wx_user_id或wx_group_id)')

    def __repr__(self):
        return f"<CustomBindKey(id={self.id}, customer='{self.customer}', bind_key='{self.bind_key}', status={self.status})>"


class AdminUser(Base):
    __tablename__ = 'admin_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    wx_user_id = Column(String(50), unique=True, comment='微信用户ID')
    wx_username = Column(String(100), comment='微信用户名')
    is_super_admin = Column(Boolean, default=False, comment='是否超级管理员')
    created_time = Column(DateTime, default=datetime.now, comment='创建时间')
    comment = Column(String(255), comment='备注')

    def __repr__(self):
        return f"<AdminUser(id={self.id}, wx_user_id='{self.wx_user_id}', is_super_admin={self.is_super_admin})>"
