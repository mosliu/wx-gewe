# AI Plugin

## 简介

AI Plugin 是一个基于 OpenAI API 的智能助手插件，可以处理文本和图片消息，并提供智能回复。该插件支持多种 OpenAI 模型，默认使用 GPT-4o 模型，用户可以根据需要切换不同的模型。

## 功能特点

- 使用 `ai!` 前缀触发插件
- 支持文本消息处理
- 支持图片分析（多模态能力）
- 支持模型切换
- 可配置的 API 密钥和端点

## 安装

1. 确保已安装所需依赖：

```bash
pip install openai>=1.12.0 aiohttp>=3.8.5 pillow>=10.0.0
```

2. 在 `.env` 文件中配置 OpenAI API 密钥：

```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_DEFAULT_MODEL=gpt-4o
```

## 配置

插件配置位于 `plugins/ai/plugin_config.yaml`，可以根据需要修改：

```yaml
enabled: true
priority: 50
module_name: ai_plugin
class_name: AIPlugin
config:
  models:
    gpt-4o:
      max_tokens: 4000
    gpt-4:
      max_tokens: 4000
    gpt-3.5-turbo:
      max_tokens: 4000
```

## 使用方法

### 基本使用

发送以 `ai!` 开头的消息即可触发 AI 助手：

```
ai! 请帮我写一首关于春天的诗
```

### 切换模型

可以使用 `model:` 前缀指定要使用的模型：

```
ai! model:gpt-3.5-turbo 请简要介绍量子计算
```

### 图片分析

发送图片并附带以 `ai!` 开头的文本，AI 助手将分析图片内容：

```
[图片] ai! 这张图片里有什么？
```

## 支持的模型

- `gpt-4o`：默认模型，支持图像和文本的多模态能力
- `gpt-4`：强大的语言模型
- `gpt-3.5-turbo`：更快的响应速度

## 开发说明

插件实现了以下核心方法：

- `process(context)`: 处理消息上下文，判断是否需要 AI 处理
- `_call_openai_api(query, model, files)`: 调用 OpenAI API 处理请求
- `_get_help_text()`: 生成帮助文本

## 注意事项

- 需要有效的 OpenAI API 密钥才能使用此插件
- 图片处理需要使用支持多模态的模型（如 gpt-4o）
- API 调用可能产生费用，请注意控制使用量
