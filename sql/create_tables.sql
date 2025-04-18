-- 创建微信用户表
CREATE TABLE IF NOT EXISTS `wxuser` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `wx_user_id` varchar(20) NOT NULL COMMENT 'wx_user_id',
  `wx_username` varchar(50) DEFAULT NULL COMMENT 'wx_username',
  `wx_user_comment` varchar(255) DEFAULT NULL,
  `customer_id` varchar(50) DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `wx_user_id` (`wx_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微信用户表';

-- 创建微信群组表
CREATE TABLE IF NOT EXISTS `wxgroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `wx_group_id` varchar(20) NOT NULL COMMENT 'wx_group_id',
  `wx_group_name` varchar(50) DEFAULT NULL COMMENT 'wx_group_name',
  `wx_group_comment` varchar(255) DEFAULT NULL,
  `customer_id` varchar(50) DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `wx_group_id` (`wx_group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微信群组表';

-- 创建客户绑定密钥表
CREATE TABLE IF NOT EXISTS `custom_bind_key` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` varchar(50) ,
  `customer` varchar(50)  COMMENT '客户名称',
  `bind_key` varchar(255) NOT NULL COMMENT '绑定key',
  `created_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `bind_time` datetime DEFAULT NULL COMMENT '绑定时间',
  `status` tinyint(1) DEFAULT 0 COMMENT '绑定状态 0:未绑定 1:已绑定',
  `bind_type` tinyint(1) DEFAULT NULL COMMENT '绑定类型 1:用户 2:群组',
  `bind_id` varchar(50) DEFAULT NULL COMMENT '绑定ID(wx_user_id或wx_group_id)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `bind_key` (`bind_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户绑定密钥表';

-- 创建管理员用户表
CREATE TABLE IF NOT EXISTS `admin_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `wx_user_id` varchar(50) NOT NULL COMMENT '微信用户ID',
  `wx_username` varchar(100) DEFAULT NULL COMMENT '微信用户名',
  `is_super_admin` tinyint(1) DEFAULT 0 COMMENT '是否超级管理员',
  `created_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `comment` varchar(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `wx_user_id` (`wx_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员用户表';

-- 插入初始管理员数据（可选）
-- INSERT INTO `admin_users` (`wx_user_id`, `wx_username`, `is_super_admin`, `comment`)
-- VALUES ('wxid_7br2m2wm63th22', '管理员', 1, '初始超级管理员');
