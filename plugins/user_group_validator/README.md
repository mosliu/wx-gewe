# User Group Validator Plugin

## 简介

User Group Validator Plugin 是一个用户和群组验证插件，用于控制哪些用户或群组可以访问系统功能。该插件通过配置白名单和数据库记录来验证用户或群组的权限，确保只有授权的用户或群组能够使用系统。

## 功能特点

- 支持用户白名单配置
- 支持群组白名单配置
- 支持数据库验证
- 可配置未授权消息处理方式
- 灵活的处理链控制

## 安装

该插件是系统的核心组件，默认已集成在系统中，无需额外安装步骤。

## 配置

### 全局配置

插件配置位于全局配置文件 `plugins/config.yaml` 中：

```yaml
user_group_validator:
  enabled: true
  priority: 20
  module_name: user_group_validator_plugin
  class_name: UserGroupValidatorPlugin
  config:
    allow_unauthorized: false
    unauthorized_message: "未授权的访问"
    return_unauthorized_message: false
    allowed_groups: 
      - "17223854314@chatroom"  # 使用群ID
      - "测试群"                 # 使用群名
    allowed_users: ["wxid_7br2m2wm63th22"]
```

### 插件配置

插件的专用配置位于 `plugins/user_group_validator/plugin_config.yaml`：

```yaml
enabled: true
priority: 10
module_name: user_group_validator_plugin
class_name: UserGroupValidatorPlugin
config:
  allow_unauthorized: false
  unauthorized_message: "未授权的访问"
  return_unauthorized_message: false
  allowed_groups: ["17223854314@chatroom"]
  allowed_users: ["wxid_7br2m2wm63th22"]
```

## 配置选项说明

- `allow_unauthorized`: 是否允许未授权访问，设置为 `true` 时将跳过验证
- `unauthorized_message`: 未授权时的提示消息
- `return_unauthorized_message`: 是否返回未授权提示消息，设置为 `false` 时将直接忽略未授权消息
- `allowed_groups`: 允许访问的群组列表，可以使用群ID或群名
- `allowed_users`: 允许访问的用户列表，使用微信ID

## 工作原理

1. 插件接收消息上下文
2. 检查配置是否允许未授权访问
3. 根据消息来源（个人或群组）执行相应的验证：
   - 对于群组消息：
     - 检查群ID或群名是否在白名单中
     - 检查数据库中是否有对应的群组记录
   - 对于个人消息：
     - 检查用户ID是否在白名单中
     - 检查数据库中是否有对应的用户记录
4. 根据验证结果和配置决定处理方式：
   - 如果验证通过，继续处理链
   - 如果验证失败且配置为返回未授权消息，则返回提示
   - 如果验证失败且配置为不返回未授权消息，则终止处理且不回复

## 数据库表

该插件使用以下数据库表：

- `WxUser`: 存储已授权的用户信息
- `WxGroup`: 存储已授权的群组信息

## 与其他插件的关系

该插件通常与 Bind Plugin 配合使用：

1. Bind Plugin 负责将用户或群组与系统客户关联，并在数据库中创建记录
2. User Group Validator Plugin 负责验证用户或群组是否已绑定或在白名单中
3. 只有通过验证的用户或群组才能使用系统的其他功能
