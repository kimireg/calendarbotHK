#!/usr/bin/env python3
"""
Singbox Auto Updater
自动更新Singbox配置
"""

import json
import logging
import os
from pathlib import Path
from datetime import datetime

from src.subscription_checker import SubscriptionChecker
from src.updater import SingboxUpdater
from src.generator import SingboxAirGenerator
from src.scheduler import UpdateScheduler, setup_logging
from src.telegram_notifier import TelegramNotifier


class SingboxAutoUpdater:
    """Singbox自动更新器"""
    
    def __init__(self, config_file: Path):
        """
        Args:
            config_file: 配置文件路径
        """
        # 加载配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            file_config = json.load(f)
        
        # 从环境变量覆盖配置（优先级：环境变量 > 配置文件）
        self.config = self._load_config_with_env(file_config)
        
        # 设置路径
        self.base_dir = Path(__file__).parent
        self.subscription_url = self.config['subscription_url']
        self.base_config_path = self.base_dir / self.config['base_config_path']
        self.history_dir = self.base_dir / self.config['subscription_history_dir']
        self.output_dir = self.base_dir / self.config['output_dir']
        self.log_dir = self.base_dir / self.config['log_dir']
        
        # 创建目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self.logger = setup_logging(self.log_dir, self.config.get('log_level', 'INFO'))
        
        # 记录配置来源
        self._log_config_sources()
        
        # 初始化组件
        self.checker = SubscriptionChecker(self.subscription_url, self.history_dir)
        self.updater = SingboxUpdater()
        self.generator = SingboxAirGenerator()
        
        # 初始化Telegram通知器（如果配置了）
        self.telegram_notifier = None
        if self.config.get('enable_telegram_notification', False):
            bot_token = self.config.get('telegram_bot_token')
            chat_id = self.config.get('telegram_chat_id')
            
            if bot_token and chat_id:
                self.telegram_notifier = TelegramNotifier(bot_token, chat_id)
                # 测试连接
                if self.telegram_notifier.test_connection():
                    self.logger.info("✅ Telegram notifier initialized")
                else:
                    self.logger.warning("⚠️  Telegram connection test failed")
                    self.telegram_notifier = None
            else:
                self.logger.warning("⚠️  Telegram enabled but credentials not configured")
    
    def _load_config_with_env(self, file_config: dict) -> dict:
        """
        从环境变量加载配置，覆盖文件配置
        
        环境变量映射：
        - SINGBOX_SUBSCRIPTION_URL -> subscription_url
        - SINGBOX_TELEGRAM_BOT_TOKEN -> telegram_bot_token
        - SINGBOX_TELEGRAM_CHAT_ID -> telegram_chat_id
        - SINGBOX_CHECK_INTERVAL_HOURS -> check_interval_hours
        - SINGBOX_LOG_LEVEL -> log_level
        - SINGBOX_ENABLE_TELEGRAM -> enable_telegram_notification
        
        Args:
            file_config: 从文件加载的配置
            
        Returns:
            合并后的配置
        """
        config = file_config.copy()
        
        # 环境变量映射
        env_mappings = {
            'SINGBOX_SUBSCRIPTION_URL': ('subscription_url', str),
            'SINGBOX_TELEGRAM_BOT_TOKEN': ('telegram_bot_token', str),
            'SINGBOX_TELEGRAM_CHAT_ID': ('telegram_chat_id', str),
            'SINGBOX_CHECK_INTERVAL_HOURS': ('check_interval_hours', int),
            'SINGBOX_LOG_LEVEL': ('log_level', str),
            'SINGBOX_ENABLE_TELEGRAM': ('enable_telegram_notification', bool),
        }
        
        # 从环境变量读取
        for env_key, (config_key, value_type) in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # 类型转换
                if value_type == bool:
                    config[config_key] = env_value.lower() in ('true', '1', 'yes', 'on')
                elif value_type == int:
                    try:
                        config[config_key] = int(env_value)
                    except ValueError:
                        self.logger.warning(f"⚠️  Invalid integer value for {env_key}: {env_value}")
                else:
                    config[config_key] = env_value
        
        return config
    
    def _log_config_sources(self):
        """记录配置来源"""
        self.logger.info("📋 Configuration loaded:")
        
        # 检查哪些配置来自环境变量
        env_configs = []
        if os.getenv('SINGBOX_SUBSCRIPTION_URL'):
            env_configs.append('subscription_url')
        if os.getenv('SINGBOX_TELEGRAM_BOT_TOKEN'):
            env_configs.append('telegram_bot_token')
        if os.getenv('SINGBOX_TELEGRAM_CHAT_ID'):
            env_configs.append('telegram_chat_id')
        if os.getenv('SINGBOX_CHECK_INTERVAL_HOURS'):
            env_configs.append('check_interval_hours')
        if os.getenv('SINGBOX_LOG_LEVEL'):
            env_configs.append('log_level')
        if os.getenv('SINGBOX_ENABLE_TELEGRAM'):
            env_configs.append('enable_telegram_notification')
        
        if env_configs:
            self.logger.info(f"   From environment variables: {', '.join(env_configs)}")
        else:
            self.logger.info("   From config file only")
        
    def update_configs(self):
        """执行更新流程"""
        try:
            self.logger.info("=" * 70)
            self.logger.info("🚀 Starting update check")
            self.logger.info("=" * 70)
            
            # 检查更新
            has_update, new_data, version_name = self.checker.check_for_updates()
            
            if not has_update:
                self.logger.info("✅ No updates needed")
                return
            
            self.logger.info(f"🆕 New version detected: {version_name}")
            
            # 获取变更摘要
            _, latest_data = self.checker.get_latest_version()
            if latest_data:
                changes = self.checker.get_changes_summary(latest_data, new_data)
                self.logger.info(f"📊 Changes summary:")
                self.logger.info(f"   Added: {len(changes['added'])} servers")
                self.logger.info(f"   Removed: {len(changes['removed'])} servers")
                self.logger.info(f"   Modified: {len(changes['modified'])} servers")
                self.logger.info(f"   Total: {changes['total_old']} → {changes['total_new']}")
            
            # 步骤1：更新Pro配置
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pro_output_path = self.output_dir / f"Singbox_Pro_V5_9_Updated_{timestamp}.json"
            
            updated_pro_config = self.updater.update_pro_config(
                self.base_config_path,
                new_data,
                pro_output_path
            )
            
            # 步骤2：生成Air版本
            air_files = self.generator.generate_air_versions(
                pro_output_path,
                self.output_dir
            )
            
            # 总结
            self.logger.info("\n" + "=" * 70)
            self.logger.info("✅ Update completed successfully!")
            self.logger.info("=" * 70)
            self.logger.info(f"📁 Generated files:")
            self.logger.info(f"   Pro:     {pro_output_path.name}")
            self.logger.info(f"   Air V5.9: {air_files['air_v59'].name}")
            self.logger.info(f"   Air V7.8: {air_files['air_v78'].name}")
            
            # 如果配置了Telegram通知，发送通知和文件
            if self.telegram_notifier:
                self.logger.info("📱 Sending Telegram notification...")
                
                config_files = [
                    pro_output_path,
                    air_files['air_v59'],
                    air_files['air_v78']
                ]
                
                success = self.telegram_notifier.send_update_notification(
                    version_name,
                    changes if latest_data else None,
                    config_files
                )
                
                if success:
                    self.logger.info("✅ Telegram notification sent successfully")
                else:
                    self.logger.warning("⚠️  Telegram notification failed")
            
            # 旧版通知（兼容）
            elif self.config.get('enable_notifications', False):
                self._send_notification(version_name, changes if latest_data else None)
            
        except Exception as e:
            self.logger.error(f"❌ Update failed: {e}", exc_info=True)
    
    def _send_notification(self, version: str, changes: dict = None):
        """发送通知（可扩展）"""
        # 这里可以实现webhook通知、邮件通知等
        self.logger.info(f"📧 Notification: New version {version} deployed")
        if changes:
            self.logger.info(f"   Changes: +{len(changes['added'])} -{len(changes['removed'])} ~{len(changes['modified'])}")
    
    def run(self, mode: str = 'schedule'):
        """
        运行更新器
        
        Args:
            mode: 'schedule' 定时运行, 'once' 运行一次
        """
        scheduler = UpdateScheduler(
            check_interval_hours=self.config.get('check_interval_hours', 6)
        )
        
        if mode == 'once':
            scheduler.run_once(self.update_configs)
        else:
            scheduler.schedule_updates(self.update_configs)
            scheduler.run()


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Singbox Auto Updater')
    parser.add_argument(
        '--config',
        default='config/settings.json',
        help='Configuration file path'
    )
    parser.add_argument(
        '--mode',
        choices=['schedule', 'once'],
        default='schedule',
        help='Run mode: schedule (continuous) or once (single run)'
    )
    
    args = parser.parse_args()
    
    # 创建并运行更新器
    updater = SingboxAutoUpdater(Path(args.config))
    updater.run(mode=args.mode)


if __name__ == '__main__':
    main()
