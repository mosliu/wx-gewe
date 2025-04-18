# Keyword Filter Plugin

## 简介

Keyword Filter Plugin 是一个关键词过滤插件，用于检测消息中是否包含预设的关键词，并根据配置进行相应的响应。该插件可用于自动回复、关键词触发等场景。

## 功能特点

- 支持多关键词配置
- 自定义回复模板
- 可配置的优先级
- 灵活的处理链控制

## 安装

该插件是系统的核心组件，默认已集成在系统中，无需额外安装步骤。

## 配置

### 全局配置

插件配置位于全局配置文件 `plugins/config.yaml` 中：

```yaml
keyword_filter:
  enabled: true
  priority: 30
  module_name: keyword_filter_plugin
  class_name: KeywordFilterPlugin
  config:
    keywords:
      - "你好"
      - "帮助"
```

### 默认配置

插件的默认配置位于 `plugins/keyword_filter/config.py`：

```python
DEFAULT_CONFIG = {
    "keywords": ["你好", "帮助"],
    "reply_template": "检测到关键词「{keyword}」"  # 可以自定义回复模板
}
```

## 使用方法

该插件会自动检测所有接收到的消息，无需用户进行特定操作。当消息中包含配置的关键词时，插件会根据配置的回复模板生成回复。

### 示例

1. 用户发送消息：`你好，请问如何使用这个系统？`
2. 插件检测到关键词 `你好`
3. 系统回复：`检测到关键词「你好」`

## 工作原理

1. 插件接收消息上下文
2. 检查消息内容是否包含配置的关键词
3. 如果匹配到关键词：
   - 记录匹配的关键词到上下文数据中
   - 使用配置的回复模板生成回复内容
   - 设置处理状态为 `FINISHED_WITH_DEFAULT`（终止处理链但执行默认回复）
4. 如果没有匹配到关键词：
   - 设置处理状态为 `CONTINUE`（继续处理链）

## 自定义扩展

### 添加新的关键词

可以通过修改配置文件添加新的关键词：

1. 编辑 `plugins/config.yaml` 文件
2. 在 `keyword_filter.config.keywords` 数组中添加新的关键词
3. 重启系统使配置生效

### 修改回复模板

可以通过修改配置文件自定义回复模板：

1. 编辑 `plugins/config.yaml` 文件
2. 添加或修改 `keyword_filter.config.reply_template` 字段
3. 在模板中使用 `{keyword}` 作为关键词的占位符
4. 重启系统使配置生效
