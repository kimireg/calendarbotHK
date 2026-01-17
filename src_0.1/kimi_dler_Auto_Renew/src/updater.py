#!/usr/bin/env python3
"""
Singbox Configuration Updater
基于 singbox-updater skill
"""

import json
from copy import deepcopy
from typing import Dict, List, Set
from pathlib import Path


class SingboxUpdater:
    """Singbox配置更新器"""
    
    # 地区映射（基于emoji）
    REGION_MAPPING = {
        '🇭🇰': ['HKonly', 'AllServer'],  # 香港
        '🇨🇳': ['HKonly', 'AllServer'],  # 台湾
        '🇸🇬': ['SGonly', 'AllServer'],  # 新加坡
        '🇯🇵': ['AllServer'],            # 日本
        '🇺🇸': ['USonly', 'AllServer'],  # 美国
    }
    
    def __init__(self):
        self.custom_servers = ['SGNowaHomePlus', 'SGoffice']
    
    def parse_servers_by_region(self, subscription_data: Dict) -> Dict[str, List[Dict]]:
        """解析订阅服务器按地区分类"""
        servers_by_region = {
            'HKonly': [],
            'SGonly': [],
            'USonly': [],
            'AllServer': []
        }
        
        outbounds = subscription_data.get('outbounds', [])
        
        # 统计
        stats = {'🇭🇰': 0, '🇨🇳': 0, '🇸🇬': 0, '🇯🇵': 0, '🇺🇸': 0}
        
        for server in outbounds:
            tag = server.get('tag', '')
            
            # 根据emoji分类
            for emoji, regions in self.REGION_MAPPING.items():
                if emoji in tag:
                    for region in regions:
                        servers_by_region[region].append(server)
                    stats[emoji] += 1
                    break
        
        # 打印统计
        print("\n📊 Subscription servers summary:")
        hk_tw = stats['🇭🇰'] + stats['🇨🇳']
        print(f"   🇭🇰 HK/TW: {hk_tw} servers")
        print(f"   🇸🇬 SG: {stats['🇸🇬']} servers")
        print(f"   🇯🇵 JP: {stats['🇯🇵']} servers")
        print(f"   🇺🇸 US: {stats['🇺🇸']} servers")
        print(f"   🌍 Total: {len(outbounds)} servers")
        
        return servers_by_region
    
    def identify_custom_servers(self, config: Dict) -> Dict[str, Set[str]]:
        """识别自定义服务器在哪些组中"""
        custom_in_groups = {}
        
        for outbound in config['outbounds']:
            if outbound.get('type') in ['selector', 'urltest']:
                group_tag = outbound['tag']
                outbounds_list = outbound.get('outbounds', [])
                
                for custom in self.custom_servers:
                    if custom in outbounds_list:
                        if custom not in custom_in_groups:
                            custom_in_groups[custom] = set()
                        custom_in_groups[custom].add(group_tag)
        
        return custom_in_groups
    
    def update_config(self, config: Dict, servers_by_region: Dict[str, List[Dict]]) -> Dict:
        """更新配置"""
        updated_config = deepcopy(config)
        
        # 识别自定义服务器
        custom_in_groups = self.identify_custom_servers(config)
        
        if custom_in_groups:
            print("\n🔒 Custom servers to preserve:")
            for custom, groups in custom_in_groups.items():
                print(f"   {', '.join(groups)}: {custom}")
        
        # 移除所有订阅服务器的定义
        subscription_tags = set()
        for servers in servers_by_region.values():
            subscription_tags.update(s['tag'] for s in servers)
        
        # 保留自定义服务器和非服务器outbound
        new_outbounds = []
        for outbound in updated_config['outbounds']:
            tag = outbound.get('tag')
            if tag not in subscription_tags:
                new_outbounds.append(outbound)
        
        # 添加新的订阅服务器
        all_subscription_servers = []
        for servers in servers_by_region.values():
            all_subscription_servers.extend(servers)
        
        # 去重
        seen = set()
        unique_servers = []
        for server in all_subscription_servers:
            tag = server['tag']
            if tag not in seen:
                seen.add(tag)
                unique_servers.append(server)
        
        new_outbounds.extend(unique_servers)
        updated_config['outbounds'] = new_outbounds
        
        # 更新服务器组
        print("\n🔄 Updating configuration...")
        groups_to_update = ['HKonly', 'SGonly', 'USonly', 'AllServer']
        updated_groups = 0
        
        for outbound in updated_config['outbounds']:
            if outbound.get('tag') in groups_to_update:
                group_tag = outbound['tag']
                
                # 获取订阅服务器
                subscription_servers = [s['tag'] for s in servers_by_region.get(group_tag, [])]
                
                # 保留自定义服务器
                custom_servers_in_group = []
                for custom in self.custom_servers:
                    if group_tag in custom_in_groups.get(custom, set()):
                        custom_servers_in_group.append(custom)
                
                # 合并
                outbound['outbounds'] = subscription_servers + custom_servers_in_group
                
                print(f"   ✓ {group_tag}: {len(subscription_servers)} subscription + {len(custom_servers_in_group)} custom servers")
                updated_groups += 1
        
        print(f"\n✅ Updated {updated_groups} server groups")
        print(f"✅ Total outbounds in config: {len(updated_config['outbounds'])}")
        
        return updated_config
    
    def update_pro_config(self, config_path: Path, subscription_data: Dict, output_path: Path) -> Dict:
        """更新Pro配置的完整流程"""
        print("=" * 70)
        print("🚀 步骤1：更新Singbox Pro配置 (singbox-updater)")
        print("=" * 70)
        
        # 读取配置
        print(f"\n📖 Reading config: {config_path.name}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✅ Config loaded: {len(config['outbounds'])} outbounds")
        
        # 解析订阅
        print(f"\n📥 Parsing subscription...")
        servers_by_region = self.parse_servers_by_region(subscription_data)
        
        # 更新
        updated_config = self.update_config(config, servers_by_region)
        
        # 保存
        print(f"\n💾 Saving updated config...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(updated_config, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Configuration updated successfully!")
        print(f"📝 Saved to: {output_path}")
        
        print("\n" + "=" * 70)
        print("✅ 步骤1完成：Pro配置已更新")
        print("=" * 70)
        
        return updated_config
