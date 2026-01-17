"""
时区处理工具
"""
from datetime import datetime, timedelta
from typing import Tuple
import pytz
import logging

logger = logging.getLogger(__name__)

# 时区映射表
TIMEZONE_CORRECTIONS = {
    'Asia/Beijing': 'Asia/Shanghai',
    'Asia/Osaka': 'Asia/Tokyo',
    'Asia/Kyoto': 'Asia/Tokyo',
    'America/Washington': 'America/New_York',
    'America/San_Francisco': 'America/Los_Angeles',
    'US/Pacific': 'America/Los_Angeles',
    'US/Eastern': 'America/New_York'
}

# 时区显示名称映射
TIMEZONE_DISPLAY_NAMES = {
    "Asia/Singapore": "新加坡",
    "Asia/Shanghai": "上海",
    "Asia/Tokyo": "东京",
    "Asia/Hong_Kong": "香港",
    "Europe/London": "伦敦",
    "America/New_York": "纽约",
    "America/Los_Angeles": "洛杉矶"
}


def resolve_timezone(tz_str: str, user_fallback_tz: str) -> Tuple[str, pytz.tzinfo, bool]:
    """
    解析时区字符串

    Args:
        tz_str: 时区字符串
        user_fallback_tz: 用户默认时区（回退值）

    Returns:
        (时区字符串, 时区对象, 是否回退)
    """
    # 如果没有指定或使用 UserContext，使用用户默认时区
    if not tz_str or tz_str == "UserContext":
        return user_fallback_tz, pytz.timezone(user_fallback_tz), False

    # 尝试修正时区名称
    candidate_tz = TIMEZONE_CORRECTIONS.get(tz_str, tz_str)

    try:
        return candidate_tz, pytz.timezone(candidate_tz), False
    except pytz.UnknownTimeZoneError:
        logger.warning(f"⚠️ Unknown timezone '{tz_str}', fallback to {user_fallback_tz}")
        return user_fallback_tz, pytz.timezone(user_fallback_tz), True


def get_timezone_display_name(tz_str: str) -> str:
    """
    获取时区显示名称

    Args:
        tz_str: 时区字符串

    Returns:
        显示名称
    """
    return TIMEZONE_DISPLAY_NAMES.get(tz_str, tz_str)


def smart_fix_year(dt_naive: datetime, tz_obj: pytz.tzinfo) -> Tuple[datetime, datetime]:
    """
    智能修正年份（如果日期已过，自动调整到明年）

    Args:
        dt_naive: 无时区的 datetime
        tz_obj: 时区对象

    Returns:
        (有时区的 datetime, 无时区的 datetime)
    """
    now = datetime.now(tz_obj)
    dt_aware = tz_obj.localize(dt_naive)

    # 如果日期在 90 天前，自动调整到明年
    while dt_aware < now - timedelta(days=90):
        try:
            dt_naive = dt_naive.replace(year=dt_naive.year + 1)
            dt_aware = tz_obj.localize(dt_naive)
        except ValueError:
            break

    return dt_aware, dt_naive


def smart_fix_end_time(
    dt_start_aware: datetime,
    dt_end_naive_raw: datetime,
    end_tz_obj: pytz.tzinfo
) -> datetime:
    """
    智能修正结束时间

    Args:
        dt_start_aware: 开始时间（有时区）
        dt_end_naive_raw: 原始结束时间（无时区）
        end_tz_obj: 结束时区对象

    Returns:
        修正后的结束时间（有时区）
    """
    current_year = dt_start_aware.year

    # 先尝试使用开始时间的年份
    try:
        dt_end_naive = dt_end_naive_raw.replace(year=current_year)
    except ValueError:
        # 如果是 2 月 29 日等特殊情况，调整为 28 日
        dt_end_naive = dt_end_naive_raw.replace(year=current_year, day=28)

    dt_end_aware = end_tz_obj.localize(dt_end_naive)

    # 如果结束时间早于开始时间，尝试调整
    if dt_end_aware < dt_start_aware:
        # 方案 1: 加一天
        dt_end_naive_plus_day = dt_end_naive + timedelta(days=1)
        dt_end_aware_plus_day = end_tz_obj.localize(dt_end_naive_plus_day)

        if dt_end_aware_plus_day >= dt_start_aware:
            return dt_end_aware_plus_day

        # 方案 2: 加一年
        try:
            dt_end_naive_plus_year = dt_end_naive.replace(year=current_year + 1)
            return end_tz_obj.localize(dt_end_naive_plus_year)
        except ValueError:
            return dt_end_aware_plus_day

    return dt_end_aware


def get_chinese_weekday(dt: datetime) -> str:
    """
    获取中文星期

    Args:
        dt: datetime 对象

    Returns:
        中文星期字符串
    """
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return weekdays[dt.weekday()]
