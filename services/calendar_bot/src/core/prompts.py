"""
AI Prompt 模板
"""
from typing import List, Dict, Any


def generate_role_description(family_members: List[Dict[str, Any]]) -> str:
    """
    生成家庭成员角色描述

    Args:
        family_members: 家庭成员配置列表

    Returns:
        角色描述字符串
    """
    desc = "Classify based on WHO:\n"
    for member in family_members:
        desc += f"    - **{member['name']}**: {member['role']}\n"
    desc += "    - **Family**: Shared events for everyone."
    return desc


def get_system_prompt(
    user_timezone: str,
    current_time: str,
    family_members: List[Dict[str, Any]],
    is_explicit_event_mode: bool = False
) -> str:
    """
    生成系统 Prompt

    Args:
        user_timezone: 用户时区
        current_time: 当前时间
        family_members: 家庭成员列表
        is_explicit_event_mode: 是否为显式事件模式

    Returns:
        系统 Prompt 字符串
    """
    # 聊天指令
    chat_instruction = ""
    if not is_explicit_event_mode:
        chat_instruction = (
            "If input is clearly NOT an event/task (e.g. casual chat), "
            "reply naturally in plain text. DO NOT output JSON."
        )
    else:
        chat_instruction = "User explicitly requested an event. You MUST return JSON."

    # 生成角色描述
    role_description = generate_role_description(family_members)

    # 成员列表
    members_list = "|".join([m['name'] for m in family_members] + ["Family"])

    return f"""
    Current User Context: {current_time} (Timezone: {user_timezone}).

    【Task】Parse request into Google Calendar Event JSON.
    {chat_instruction}

    【RULE 1: Family Categories】
    {role_description}

    【RULE 2: Tasks vs Events】
    - **Normal Event**: Specific time (e.g. "Meeting at 3pm").
      -> Set "is_all_day": false, "start_time": "YYYY-MM-DD HH:MM:SS".
    - **Task/Todo**: No specific time (e.g. "Buy milk", "Call Mom today", "Jason's Football match").
      -> Set "is_all_day": true.
      -> Set "start_time": "YYYY-MM-DD" (Date ONLY, no time).
      -> No need for timezones or end_time.

    【RULE 3: Date Logic】
    - Missing year? Assume UPCOMING relative to Now ({current_time}).
    - Validate Weekday.

    【Output JSON】
    {{
        "is_event": true,
        "is_all_day": boolean,
        "category": "{members_list}",
        "summary": "Title",
        "start_time": "YYYY-MM-DD HH:MM:SS" OR "YYYY-MM-DD",
        "start_timezone": "IANA_TZ" (Optional if all_day),
        "end_time": "...",
        "end_timezone": "...",
        "location": "...",
        "description": "...",
        "recurrence": []
    }}
    """
