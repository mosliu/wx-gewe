# 插件系统

## 简介

插件系统是本应用的核心组件，通过插件机制实现功能的模块化和可扩展性。每个插件都是独立的功能模块，可以根据需要启用或禁用，也可以自定义开发新的插件来扩展系统功能。

## 插件列表

当前系统包含以下插件：

| 插件名称 | 描述 | 优先级 | 默认状态 |
|---------|------|-------|---------|
| [bind](./bind/README.md) | 用户和群组绑定插件，用于将微信用户或群组与系统客户关联 | 10 | 启用 |
| [user_group_validator](./user_group_validator/README.md) | 用户和群组验证插件，用于控制哪些用户或群组可以访问系统功能 | 20 | 启用 |
| [keyword_filter](./keyword_filter/README.md) | 关键词过滤插件，用于检测消息中是否包含预设的关键词 | 30 | 启用 |
| [ai](./ai/README.md) | AI 插件，基于 OpenAI API 的智能助手，支持文本和图片处理 | 50 | 启用 |

## 插件工作流程

插件系统的工作流程如下：

1. 系统初始化时，`PluginManager` 加载所有已启用的插件
2. 插件按照优先级排序，优先级数值越小，越先执行
3. 当收到消息时，系统创建消息上下文 `Context`
4. 消息上下文依次通过每个插件的 `process` 方法处理
5. 每个插件可以修改上下文内容，或者决定是否继续处理链
6. 处理完成后，系统根据上下文的最终状态决定是否发送回复

## 插件处理状态

插件处理消息时可以设置以下处理状态：

- `ProcessState.CONTINUE`: 继续处理链，最后执行默认处理
- `ProcessState.FINISHED_WITH_DEFAULT`: 终止处理链，执行默认处理
- `ProcessState.FINISHED`: 终止处理链，不执行默认处理

## 插件配置

插件配置有三个级别：

1. **默认配置**：位于插件目录下的 `config.py` 文件中的 `DEFAULT_CONFIG` 变量
2. **全局配置**：位于 `plugins/config.yaml` 文件中
3. **插件专用配置**：位于插件目录下的 `plugin_config.yaml` 文件中

配置的优先级为：插件专用配置 > 全局配置 > 默认配置

## 开发新插件

### 插件目录结构

一个标准的插件目录结构如下：

```
plugins/
└── your_plugin/
    ├── __init__.py           # 导出插件类和默认配置
    ├── your_plugin.py        # 插件主类实现
    ├── config.py             # 默认配置
    ├── plugin_config.yaml    # 插件专用配置（可选）
    └── README.md             # 插件文档
```

### 插件类实现

插件类需要继承 `Plugin` 基类并实现 `process` 方法：

```python
from typing import Optional
from bot.context import Context, ProcessState
from plugins.base import Plugin

class YourPlugin(Plugin):
    """你的插件描述"""
    
    async def process(self, context: Context) -> Optional[Context]:
        # 处理逻辑
        # ...
        
        # 返回处理后的上下文
        return context
```

### 注册插件

在全局配置文件 `plugins/config.yaml` 中添加插件配置：

```yaml
your_plugin:
  enabled: true
  priority: 100  # 设置适当的优先级
  module_name: your_plugin
  class_name: YourPlugin
  config:
    # 插件特定配置
    option1: value1
    option2: value2
```

## 插件管理

可以通过修改 `plugins/config.yaml` 文件来管理插件：

- 启用/禁用插件：修改 `enabled` 字段
- 调整插件优先级：修改 `priority` 字段
- 修改插件配置：修改 `config` 字段下的配置项
