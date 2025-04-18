# Listen Plugin

## 简介

Listen Plugin 是一个群组监听插件，允许用户在私聊中开启监听模式，当用户在群组中发言时，系统会通过私聊通知用户当前群组的信息。

## 功能特点

- 支持通过私聊命令开启/关闭监听模式
- 监听模式自动过期（默认2小时）
- 使用 Redis 存储监听状态
- 支持群组名称缓存

## 安装

该插件是系统的组件，默认已集成在系统中，无需额外安装步骤。

## 配置

### 全局配置

插件配置位于全局配置文件 `plugins/config.yaml` 中：

```yaml
listen:
  enabled: true
  priority: 40
  module_name: listen_plugin
  class_name: ListenPlugin
  config:
    listen_command: "/listen"
    stop_listen_command: "/stop_listen"
    listen_expire: 7200
```

### 配置选项说明

- `listen_command`: 开启监听模式的命令
- `stop_listen_command`: 关闭监听模式的命令
- `listen_expire`: 监听模式自动过期时间（秒）
- `messages`: 各种提示消息的模板

## 使用方法

### 开启监听模式

在私聊中发送：
```
/listen
```

### 关闭监听模式

在私聊中发送：
```
/stop_listen
```

## 工作原理

1. 用户在私聊中发送 `/listen` 命令
2. 系统在 Redis 中记录用户的监听状态，设置过期时间
3. 当用户在群组中发言时，系统检查用户是否处于监听模式
4. 如果是，则通过私聊发送群组信息给用户
5. 用户可以随时通过 `/stop_listen` 命令关闭监听模式

## 数据存储

插件使用 Redis 存储监听状态：

- Key 格式：`gewe-auth:listen_mode:{user_id}`
- Value：`"1"`
- 过期时间：2小时（可配置）

## 依赖服务

- Redis：用于存储监听状态
- CacheManager：用于获取群组名称