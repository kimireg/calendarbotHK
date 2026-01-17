#!/usr/bin/env python3
"""
Telegram Notifier
通过Telegram Bot发送更新通知和配置文件
"""

import json
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, List


class TelegramNotifier:
    """Telegram通知器"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Args:
            bot_token: Telegram Bot Token
            chat_id: 接收消息的Chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger(__name__)
        
    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        发送文本消息
        
        Args:
            text: 消息内容
            parse_mode: 解析模式（Markdown或HTML）
        
        Returns:
            是否发送成功
        """
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_encoded)
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get('ok'):
                    self.logger.info("✅ Message sent to Telegram")
                    return True
                else:
                    self.logger.error(f"❌ Telegram API error: {result}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to send message: {e}")
            return False
    
    def send_file(self, file_path: Path, caption: str = "") -> bool:
        """
        发送文件
        
        Args:
            file_path: 文件路径
            caption: 文件说明
        
        Returns:
            是否发送成功
        """
        try:
            url = f"{self.base_url}/sendDocument"
            
            # 读取文件
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 准备multipart/form-data
            boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
            
            body = []
            
            # chat_id
            body.append(f'--{boundary}'.encode())
            body.append(b'Content-Disposition: form-data; name="chat_id"')
            body.append(b'')
            body.append(self.chat_id.encode())
            
            # caption
            if caption:
                body.append(f'--{boundary}'.encode())
                body.append(b'Content-Disposition: form-data; name="caption"')
                body.append(b'')
                body.append(caption.encode('utf-8'))
            
            # document
            body.append(f'--{boundary}'.encode())
            body.append(f'Content-Disposition: form-data; name="document"; filename="{file_path.name}"'.encode())
            body.append(b'Content-Type: application/json')
            body.append(b'')
            body.append(file_data)
            
            # 结束
            body.append(f'--{boundary}--'.encode())
            body.append(b'')
            
            body_data = b'\r\n'.join(body)
            
            # 发送请求
            headers = {
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
            
            req = urllib.request.Request(url, data=body_data, headers=headers)
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get('ok'):
                    self.logger.info(f"✅ File sent to Telegram: {file_path.name}")
                    return True
                else:
                    self.logger.error(f"❌ Telegram API error: {result}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to send file {file_path.name}: {e}")
            return False
    
    def send_update_notification(
        self, 
        version_name: str, 
        changes: Optional[dict],
        config_files: List[Path]
    ) -> bool:
        """
        发送更新通知和配置文件
        
        Args:
            version_name: 版本名称
            changes: 变更摘要
            config_files: 配置文件列表
        
        Returns:
            是否发送成功
        """
        try:
            # 1. 发送通知消息
            message = self._format_update_message(version_name, changes)
            if not self.send_message(message):
                return False
            
            # 2. 发送配置文件
            for config_file in config_files:
                if not config_file.exists():
                    self.logger.warning(f"⚠️  File not found: {config_file}")
                    continue
                
                # 根据文件名生成说明
                caption = self._get_file_caption(config_file)
                
                if not self.send_file(config_file, caption):
                    self.logger.error(f"❌ Failed to send: {config_file.name}")
                    # 继续发送其他文件
            
            self.logger.info("✅ Update notification sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send update notification: {e}")
            return False
    
    def _format_update_message(self, version_name: str, changes: Optional[dict]) -> str:
        """格式化更新消息"""
        message = f"🔄 *Singbox配置更新通知*\n\n"
        message += f"📦 *版本*: `{version_name}`\n"
        message += f"⏰ *时间*: {self._get_current_time()}\n\n"
        
        if changes:
            message += f"📊 *变更摘要*:\n"
            message += f"• 新增服务器: {len(changes['added'])} 个\n"
            message += f"• 移除服务器: {len(changes['removed'])} 个\n"
            message += f"• 配置更新: {len(changes['modified'])} 个\n"
            message += f"• 服务器总数: {changes['total_old']} → {changes['total_new']}\n\n"
        
        message += "📁 *生成的配置文件*:\n"
        message += "1️⃣ Pro V5.9 Updated (完整版)\n"
        message += "2️⃣ Air V5.9 (个人简化版)\n"
        message += "3️⃣ Air V7.8 (朋友分享版)\n\n"
        message += "⬇️ 正在发送配置文件..."
        
        return message
    
    def _get_file_caption(self, file_path: Path) -> str:
        """生成文件说明"""
        filename = file_path.name
        
        if "Pro" in filename and "Updated" in filename:
            return "📋 Pro V5.9 Updated\n完整功能版，包含所有订阅服务器和自定义服务器"
        elif "Air_V5_9" in filename:
            return "📱 Air V5.9\n个人简化版，保留AllServer组和自定义服务器"
        elif "Air_V7_8" in filename:
            return "👥 Air V7.8\n朋友分享版，已移除自定义服务器，可安全分享"
        else:
            return filename
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def test_connection(self) -> bool:
        """
        测试Telegram连接
        
        Returns:
            连接是否正常
        """
        try:
            url = f"{self.base_url}/getMe"
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get('ok'):
                    bot_info = result.get('result', {})
                    bot_name = bot_info.get('username', 'Unknown')
                    self.logger.info(f"✅ Connected to Telegram Bot: @{bot_name}")
                    return True
                else:
                    self.logger.error(f"❌ Telegram connection test failed: {result}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Telegram: {e}")
            return False


# 辅助函数：获取Chat ID的说明
def get_chat_id_instructions() -> str:
    """返回获取Chat ID的说明"""
    return """
    如何获取Telegram Chat ID：
    
    方法1：使用 @userinfobot
    1. 在Telegram中搜索 @userinfobot
    2. 发送 /start
    3. Bot会返回你的Chat ID
    
    方法2：使用 @RawDataBot
    1. 在Telegram中搜索 @RawDataBot  
    2. 发送任意消息
    3. Bot会返回包含Chat ID的JSON数据
    
    方法3：通过API
    1. 向你的Bot发送一条消息
    2. 访问: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
    3. 在返回的JSON中查找 "chat":{"id": XXXXXXX}
    """
