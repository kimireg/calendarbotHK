#!/usr/bin/env python3
"""
Subscription Checker
检查订阅是否有更新
"""

import json
import hashlib
import urllib.request
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple


class SubscriptionChecker:
    """订阅检查器"""
    
    def __init__(self, subscription_url: str, history_dir: Path):
        self.subscription_url = subscription_url
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
    def download_subscription(self) -> Optional[Dict]:
        """下载订阅文件"""
        try:
            print(f"📥 Downloading subscription from: {self.subscription_url[:80]}...")
            
            # 下载zip文件
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
                urllib.request.urlretrieve(self.subscription_url, tmp_zip.name)
                
                # 解压
                with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
                    # 通常第一个文件就是配置
                    config_filename = zip_ref.namelist()[0]
                    with zip_ref.open(config_filename) as config_file:
                        subscription_data = json.load(config_file)
                        
            print(f"✅ Downloaded: {len(subscription_data.get('outbounds', []))} servers")
            return subscription_data
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def calculate_hash(self, data: Dict) -> str:
        """计算数据的hash值"""
        # 只关注outbounds部分
        outbounds = data.get('outbounds', [])
        # 排序以确保一致性
        sorted_data = sorted(json.dumps(outbounds, sort_keys=True).encode())
        return hashlib.sha256(b''.join(sorted_data)).hexdigest()
    
    def get_latest_version(self) -> Optional[Tuple[str, Dict]]:
        """获取最新保存的版本"""
        version_files = sorted(self.history_dir.glob('subscription_*.json'), reverse=True)
        if version_files:
            latest_file = version_files[0]
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return latest_file.stem, data
        return None, None
    
    def save_version(self, data: Dict) -> str:
        """保存新版本"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version_name = f"subscription_{timestamp}"
        filepath = self.history_dir / f"{version_name}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"💾 Saved new version: {version_name}")
        return version_name
    
    def check_for_updates(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        检查是否有更新
        
        Returns:
            (has_update, new_data, version_name)
        """
        # 下载最新订阅
        new_data = self.download_subscription()
        if not new_data:
            return False, None, None
        
        # 获取最新保存的版本
        latest_version, latest_data = self.get_latest_version()
        
        if latest_data is None:
            # 第一次运行，保存初始版本
            print("🆕 First run, saving initial version")
            version_name = self.save_version(new_data)
            return True, new_data, version_name
        
        # 计算hash比较
        new_hash = self.calculate_hash(new_data)
        latest_hash = self.calculate_hash(latest_data)
        
        if new_hash != latest_hash:
            print("🔄 Changes detected!")
            print(f"   Old hash: {latest_hash[:16]}...")
            print(f"   New hash: {new_hash[:16]}...")
            
            # 保存新版本
            version_name = self.save_version(new_data)
            return True, new_data, version_name
        else:
            print("✅ No changes detected")
            return False, None, latest_version
    
    def get_changes_summary(self, old_data: Dict, new_data: Dict) -> Dict:
        """获取变更摘要"""
        old_servers = {s['tag']: s for s in old_data.get('outbounds', [])}
        new_servers = {s['tag']: s for s in new_data.get('outbounds', [])}
        
        added = set(new_servers.keys()) - set(old_servers.keys())
        removed = set(old_servers.keys()) - set(new_servers.keys())
        
        # 检查配置变更
        modified = []
        for tag in set(old_servers.keys()) & set(new_servers.keys()):
            if old_servers[tag] != new_servers[tag]:
                modified.append(tag)
        
        return {
            'added': list(added),
            'removed': list(removed),
            'modified': modified,
            'total_old': len(old_servers),
            'total_new': len(new_servers)
        }
