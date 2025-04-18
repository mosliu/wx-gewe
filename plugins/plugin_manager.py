import os
import importlib
from typing import List, Dict, Type
from plugins.base import Plugin
import yaml
from common.log import logger

class PluginManager:
    def __init__(self):
        self._plugins: List[Plugin] = []
        self._load_configurations()
        self._load_plugins()

    def _load_configurations(self):
        """从配置文件加载插件配置"""
        # 加载全局配置
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
            self._plugin_configs = self._config.get('plugins', {})

    def _load_plugin_config(self, plugin_dir: str) -> Dict:
        """加载插件专用配置"""
        # 尝试加载插件目录下的配置文件
        plugin_config_path = os.path.join(os.path.dirname(__file__), plugin_dir, 'plugin_config.yaml')
        if os.path.exists(plugin_config_path):
            with open(plugin_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def _load_plugins(self):
        """根据配置加载插件"""
        # 获取插件目录列表
        plugin_dirs = [d for d in os.listdir(os.path.dirname(__file__))
                      if os.path.isdir(os.path.join(os.path.dirname(__file__), d))
                      and not d.startswith('__')]

        enabled_plugins = []
        for plugin_dir in plugin_dirs:
            # 加载插件专用配置
            plugin_specific_config = self._load_plugin_config(plugin_dir)

            # 合并全局配置
            global_config = self._plugin_configs.get(plugin_dir, {})

            # 插件专用配置优先级高于全局配置
            merged_config = {**global_config, **plugin_specific_config}

            if merged_config.get('enabled', True):
                enabled_plugins.append((plugin_dir, merged_config))

        # 按优先级排序
        enabled_plugins.sort(key=lambda x: x[1].get('priority', 100))

        for plugin_dir, plugin_config in enabled_plugins:
            try:
                # 动态导入插件模块
                module_name = plugin_config.get('module_name', 'plugin')
                class_name = plugin_config.get('class_name', 'Plugin')

                module_path = f"plugins.{plugin_dir}.{module_name}"
                module = importlib.import_module(module_path)

                # 获取插件类
                plugin_class = getattr(module, class_name)

                # 合并默认配置
                default_config = {}
                try:
                    config_module = importlib.import_module(f"plugins.{plugin_dir}.config")
                    default_config = getattr(config_module, 'DEFAULT_CONFIG', {})
                except ImportError:
                    pass

                # 合并所有配置，优先级：插件专用配置 > 全局配置 > 默认配置
                user_config = plugin_config.get('config', {})
                final_config = {**default_config, **user_config}

                # 实例化插件，对于AdminPlugin特殊处理
                if class_name == 'AdminPlugin':
                    plugin_instance = plugin_class(final_config, self)
                else:
                    plugin_instance = plugin_class(final_config)
                self._plugins.append(plugin_instance)

                logger.info(f"Successfully loaded plugin: {plugin_dir}")

            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_dir}: {str(e)}")

    def get_plugins(self) -> List[Plugin]:
        """获取所有已注册的插件"""
        return self._plugins

    def get_plugin_config(self, plugin_name: str) -> Dict:
        """获取指定插件的配置"""
        # 从全局配置中获取
        if plugin_name in self._plugin_configs:
            return self._plugin_configs[plugin_name]

        # 尝试从插件专用配置文件获取
        plugin_config_path = os.path.join(os.path.dirname(__file__), plugin_name, 'plugin_config.yaml')
        if os.path.exists(plugin_config_path):
            with open(plugin_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)

        return {}

# 创建全局实例
plugin_manager = PluginManager()