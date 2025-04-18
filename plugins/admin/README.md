# Admin Plugin

## 简介

Admin Plugin 是一个管理员功能插件，用于提供管理员特定的命令和功能。该插件可以识别管理员用户，并允许他们执行特殊命令，如创建绑定密钥和修改系统配置。

## 功能特点

- 管理员身份验证（配置文件和数据库结合）
- 创建绑定密钥命令 (`/add_bind`)
- 修改默认OpenAI模型命令 (`/model`)
- 可扩展的命令系统，方便添加新命令

## 安装

该插件是系统的组件，默认已集成在系统中，无需额外安装步骤。

## 配置

### 全局配置

插件配置位于全局配置文件 `plugins/config.yaml` 中：

```yaml
admin:
  enabled: true
  priority: 5
  module_name: admin_plugin
  class_name: AdminPlugin
  config:
    admin_users:
      - "wxid_example1"  # 管理员微信ID
      - "wxid_example2"
```

### 插件专用配置

插件的专用配置位于 `plugins/admin/plugin_config.yaml`：

```yaml
enabled: true
priority: 5
module_name: admin_plugin
class_name: AdminPlugin
config:
  admin_users:
    - "wxid_example1"  # 管理员微信ID
  admin_commands:
    add_bind:
      command: "/add_bind"
      description: "创建新的绑定密钥"
      help_message: "格式: /add_bind <客户ID> <客户名称>"
    model:
      command: "/model"
      description: "修改默认的OpenAI模型"
      help_message: "格式: /model <模型名称>"
```

## 使用方法

### 添加绑定密钥

管理员可以使用以下命令创建新的绑定密钥：

```
/add_bind customer123 测试客户
```

这将创建一个新的绑定密钥，并返回密钥信息。

### 修改默认模型

管理员可以使用以下命令修改系统默认的OpenAI模型：

```
/model gpt-4
```

这将更新系统环境变量中的默认模型设置。

## 数据库表

插件使用 `admin_users` 表存储管理员信息：

| 字段 | 类型 | 描述 |
|------|------|------|
| id | Integer | 主键 |
| wx_user_id | String | 微信用户ID |
| wx_username | String | 微信用户名 |
| is_super_admin | Boolean | 是否超级管理员 |
| created_time | DateTime | 创建时间 |
| comment | String | 备注 |

## 开发说明

插件实现了以下核心方法：

- `process(context)`: 处理消息上下文，判断是否是管理员命令
- `_is_admin(user_id)`: 检查用户是否是管理员
- `_handle_add_bind(context, args)`: 处理添加绑定密钥命令
- `_handle_model(context, args)`: 处理修改默认模型命令
