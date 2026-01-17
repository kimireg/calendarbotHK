"""
事件数据验证
"""
from datetime import datetime
from typing import Tuple, Set, Dict, Any
import logging

logger = logging.getLogger(__name__)


class EventValidator:
    """事件验证器"""

    def __init__(self, valid_categories: Set[str]):
        """
        初始化验证器

        Args:
            valid_categories: 有效的分类集合
        """
        self.valid_categories = valid_categories

    def validate_and_fix_payload(self, data: Dict[str, Any], default_category: str) -> Tuple[bool, str]:
        """
        验证并修复事件数据

        Args:
            data: 事件数据字典
            default_category: 默认分类

        Returns:
            (是否有效, 错误信息)
        """
        # 检查必填字段
        if not data.get('summary'):
            return False, "缺少事件标题 (summary)"

        if not data.get('start_time'):
            return False, "缺少开始时间 (start_time)"

        # 验证分类
        category = data.get('category')
        if category not in self.valid_categories:
            logger.warning(f"⚠️ Unknown category '{category}', fallback to '{default_category}'")
            data['category'] = default_category

        # 验证时间格式
        is_all_day = data.get('is_all_day', False)

        try:
            if is_all_day:
                # 全天事件：只需要日期
                datetime.strptime(data['start_time'], '%Y-%m-%d')
                if data.get('end_time'):
                    datetime.strptime(data['end_time'], '%Y-%m-%d')
            else:
                # 普通事件：需要日期时间
                datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
                if data.get('end_time'):
                    datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            return False, f"时间格式错误: {str(e)}"

        return True, "OK"


def normalize_recurrence(recurrence_data) -> list:
    """
    规范化重复规则

    Args:
        recurrence_data: 重复规则数据（字符串或列表）

    Returns:
        规范化后的列表
    """
    if not recurrence_data:
        return None

    # 转换为列表
    if isinstance(recurrence_data, str):
        rule_list = [recurrence_data]
    else:
        rule_list = recurrence_data

    # 规范化每条规则
    normalized = []
    for rule in rule_list:
        rule = rule.strip()
        if rule:
            # 确保以 RRULE: 开头
            if not rule.upper().startswith("RRULE:"):
                rule = "RRULE:" + rule
            normalized.append(rule)

    return normalized if normalized else None
