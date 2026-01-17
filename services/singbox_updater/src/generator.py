#!/usr/bin/env python3
"""
Singbox Air Version Generator
基于 singbox-air-generator skill
"""

import json
import re
from copy import deepcopy
from typing import Dict, List
from pathlib import Path


class SingboxAirGenerator:
    """Singbox Air版本生成器"""
    
    def __init__(self):
        self.custom_servers = ['SGNowaHomePlus', 'SGoffice']
    
    def extract_version(self, filename: str) -> str:
        """从文件名提取版本号"""
        match = re.search(r'V(\d+)_(\d+)', filename)
        if match:
            return f"{match.group(1)}_{match.group(2)}"
        return "5_9"  # 默认版本
    
    def generate_air_v59(self, pro_config: Dict, version: str) -> Dict:
        """
        生成Air V5.9 - 个人简化版
        - 移除应用组 (AIDefault, YouTube, Netflix, Apple, USonly)
        - 保留AllServer组
        - 保留自定义服务器
        - 简化路由规则
        """
        config = deepcopy(pro_config)
        
        # 要移除的组
        groups_to_remove = {'AIDefault', 'YouTube', 'Netflix', 'Apple', 'USonly'}
        
        print(f"   ❌ Removed groups: {', '.join(sorted(groups_to_remove))}")
        
        # 移除这些组
        config['outbounds'] = [
            o for o in config['outbounds']
            if o.get('tag') not in groups_to_remove
        ]
        
        # 更新Proxy选择器（移除对已删除组的引用，但不包含AllServer）
        for outbound in config['outbounds']:
            if outbound.get('tag') == 'Proxy':
                original_outbounds = outbound['outbounds']
                # 移除已删除的组和AllServer
                outbound['outbounds'] = [
                    o for o in original_outbounds
                    if o not in groups_to_remove and o != 'AllServer'
                ]
                print(f"   ✓ Updated Proxy selector: {outbound['outbounds']}")
        
        # 简化路由规则
        if 'route' in config and 'rules' in config['route']:
            original_rules = config['route']['rules']
            # 保留基本规则（CN直连等）
            simplified_rules = [
                r for r in original_rules
                if r.get('outbound') in ['direct', 'block', 'dns-out']
                or not any(app in str(r) for app in groups_to_remove)
            ]
            config['route']['rules'] = simplified_rules
            print(f"   ✓ Simplified routing rules: {len(original_rules)} → {len(simplified_rules)}")
        
        print(f"   ✅ Air V5.9 generated: {len(config['outbounds'])} outbounds")
        return config
    
    def generate_air_v78(self, pro_config: Dict) -> Dict:
        """
        生成Air V7.8 - 朋友试用版
        - 保留所有功能组
        - 移除自定义服务器
        - 保留完整路由规则
        """
        config = deepcopy(pro_config)
        
        # 清理Proxy和其他组中的自定义服务器引用
        cleaned_groups = []
        for outbound in config['outbounds']:
            if outbound.get('type') in ['selector', 'urltest']:
                original = outbound.get('outbounds', [])
                cleaned = [o for o in original if o not in self.custom_servers]
                if cleaned != original:
                    outbound['outbounds'] = cleaned
                    cleaned_groups.append(outbound['tag'])
        
        if cleaned_groups:
            for group in cleaned_groups:
                print(f"   ✓ Cleaned {group}: removed custom server references")
        
        # 移除自定义服务器的定义
        original_count = len(config['outbounds'])
        config['outbounds'] = [
            o for o in config['outbounds']
            if o.get('tag') not in self.custom_servers
        ]
        removed_count = original_count - len(config['outbounds'])
        
        if removed_count > 0:
            print(f"   ❌ Removed custom servers: {', '.join(self.custom_servers)}")
        
        print(f"   ✅ Air V7.8 generated: {len(config['outbounds'])} outbounds")
        return config
    
    def generate_air_versions(self, pro_config_path: Path, output_dir: Path) -> Dict[str, Path]:
        """生成Air版本的完整流程"""
        print("\n" + "=" * 70)
        print("🚀 步骤2：生成Air版本 (singbox-air-generator)")
        print("=" * 70)
        
        # 读取Pro配置
        print(f"\n📖 Reading Pro configuration: {pro_config_path.name}")
        with open(pro_config_path, 'r', encoding='utf-8') as f:
            pro_config = json.load(f)
        print(f"✅ Pro config loaded: {len(pro_config['outbounds'])} outbounds")
        
        # 提取版本号
        version = self.extract_version(pro_config_path.stem)
        
        output_files = {}
        
        # 生成Air V5.9
        print("\n🔹 Generating Air V5.9 (Personal Simplified Version)")
        print(f"   Version: {version}")
        air59 = self.generate_air_v59(pro_config, version)
        
        air59_path = output_dir / f"Singbox_Air_V{version}_Generated.json"
        with open(air59_path, 'w', encoding='utf-8') as f:
            json.dump(air59, f, indent=4, ensure_ascii=False)
        print(f"\n💾 Air V5.9 saved: {air59_path.name}")
        output_files['air_v59'] = air59_path
        
        # 生成Air V7.8
        print("\n🔹 Generating Air V7.8 (Friend Trial Version)")
        print(f"   Version: 7_8")
        air78 = self.generate_air_v78(pro_config)
        
        air78_path = output_dir / "Singbox_Air_V7_8_Generated.json"
        with open(air78_path, 'w', encoding='utf-8') as f:
            json.dump(air78, f, indent=4, ensure_ascii=False)
        print(f"💾 Air V7.8 saved: {air78_path.name}")
        output_files['air_v78'] = air78_path
        
        print("\n" + "=" * 70)
        print("✅ 步骤2完成：Air版本已生成")
        print("=" * 70)
        
        print(f"\n📊 Summary:")
        print(f"   Air V5.9 (Personal): {len(air59['outbounds'])} outbounds")
        print(f"   Air V7.8 (Friend):   {len(air78['outbounds'])} outbounds")
        
        return output_files
