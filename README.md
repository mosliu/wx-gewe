# WeChat Bot System

## 简介

这是一个基于微信的智能机器人系统，提供了丰富的插件功能和可扩展的架构设计。系统支持群组管理、AI对话、消息监听等多种功能，并提供了Web界面用于消息推送。

## 主要功能

### 1. 插件系统
- 模块化的插件架构，支持动态加载和配置
- 插件优先级管理
- 灵活的消息处理链

### 2. 核心插件

#### AI助手 (优先级: 50)
- 基于OpenAI API的智能对话
- 支持多种模型（GPT-4o, GPT-4, GPT-3.5-turbo）
- 支持文本和图片分析
- 使用方式：以"ai!"或"小福"开头发送消息

#### 用户绑定 (优先级: 10)
- 支持用户和群组与系统客户关联
- 使用唯一密钥进行绑定
- 命令：`/bind <key>`

#### 用户验证 (优先级: 20)
- 白名单管理
- 权限控制
- 支持用户和群组验证

#### 关键词过滤 (优先级: 30)
- 自定义关键词监测
- 自动回复功能
- 可配置的响应模板

#### 群组监听 (优先级: 40)
- 私聊监听群组消息
- 自动过期机制（默认2小时）
- 命令：`/listen`, `/stop_listen`

#### 管理员功能 (优先级: 5)
- 创建绑定密钥
- 修改默认AI模型
- 清除缓存
- 管理员专属命令

### 3. Web推送接口
- 提供Web界面进行消息推送
- RESTful API支持
- 实时消息发送功能

## 系统要求

- Python 3.x
- Redis
- MySQL/PostgreSQL
- OpenAI API密钥（用于AI功能）

## 安装部署

1. 克隆仓库
```bash
git clone [repository_url]
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填写必要的配置信息
```

4. 启动服务
```bash
python main.py
```

## 配置说明

### 插件配置
插件配置有三个级别：
1. 默认配置：插件目录下的`config.py`
2. 全局配置：`plugins/config.yaml`
3. 插件专用配置：插件目录下的`plugin_config.yaml`

### 环境变量
- `BASE_URL`: Gewechat API地址
- `GEWECHAT_TOKEN`: API访问令牌
- `APP_ID`: 应用ID
- `OPENAI_API_KEY`: OpenAI API密钥
- `OPENAI_API_BASE`: OpenAI API基础URL

## API接口

### 消息推送
- 端点：`/push`
- 方法：POST
- 数据格式：
```json
{
    "room_id": "群组ID",
    "text": "消息内容"
}
```

## 开发指南

### 创建新插件
1. 在`plugins`目录下创建新的插件目录
2. 实现插件类（继承`Plugin`基类）
3. 创建配置文件
4. 在全局配置中注册插件

### 插件目录结构
```
plugins/
└── your_plugin/
    ├── __init__.py
    ├── your_plugin.py
    ├── config.py
    ├── plugin_config.yaml
    └── README.md
```

## 许可证

[许可证类型]

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request