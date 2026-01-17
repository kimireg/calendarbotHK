"""
事件解析模块
使用 AI 解析自然语言并生成事件数据
"""
import re
import json
import base64
import logging
from typing import Optional, Tuple, Any, Dict
from io import BytesIO
from datetime import datetime

import pytz
from openai import AsyncOpenAI

from .prompts import get_system_prompt

logger = logging.getLogger(__name__)


class EventParser:
    """事件解析器"""

    def __init__(self, openai_client: AsyncOpenAI, model_name: str):
        """
        初始化解析器

        Args:
            openai_client: OpenAI 客户端
            model_name: 模型名称
        """
        self.client = openai_client
        self.model_name = model_name

    def extract_json_from_text(self, text: str) -> Optional[Dict]:
        """
        从文本中提取 JSON

        Args:
            text: 包含 JSON 的文本

        Returns:
            解析后的字典或 None
        """
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试从 Markdown 代码块中提取
        try:
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

        return None

    async def parse_response(self, response: Any) -> Tuple[str, Any]:
        """
        解析 AI 响应

        Args:
            response: AI 响应对象

        Returns:
            (消息类型, 内容) - ("EVENT", dict) 或 ("TEXT", str)
        """
        content = response.choices[0].message.content
        clean_content = content.replace("```json", "").replace("```", "").strip()

        data = self.extract_json_from_text(clean_content)

        if data and isinstance(data, dict) and data.get('is_event'):
            return "EVENT", data

        return "TEXT", content

    async def parse_text_message(
        self,
        text: str,
        user_timezone: str,
        family_members: list,
        is_explicit_event: bool = False
    ) -> Tuple[str, Any]:
        """
        解析纯文本消息

        Args:
            text: 文本内容
            user_timezone: 用户时区
            family_members: 家庭成员配置
            is_explicit_event: 是否为显式事件请求

        Returns:
            (消息类型, 内容)
        """
        # 生成当前时间
        tz = pytz.timezone(user_timezone)
        current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        # 生成系统 Prompt
        system_prompt = get_system_prompt(
            user_timezone=user_timezone,
            current_time=current_time,
            family_members=family_members,
            is_explicit_event_mode=is_explicit_event
        )

        # 调用 AI
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3
            )

            return await self.parse_response(response)

        except Exception as e:
            logger.error(f"❌ AI parsing error: {e}")
            raise

    async def parse_image_message(
        self,
        image_bytes: bytes,
        caption: str,
        user_timezone: str,
        family_members: list
    ) -> Tuple[str, Any]:
        """
        解析图片消息（带可选文字说明）

        Args:
            image_bytes: 图片二进制数据
            caption: 图片说明文字
            user_timezone: 用户时区
            family_members: 家庭成员配置

        Returns:
            (消息类型, 内容)
        """
        # 生成当前时间
        tz = pytz.timezone(user_timezone)
        current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        # 生成系统 Prompt
        system_prompt = get_system_prompt(
            user_timezone=user_timezone,
            current_time=current_time,
            family_members=family_members,
            is_explicit_event_mode=False
        )

        # 转换为 Base64
        b64_image = base64.b64encode(image_bytes).decode()

        # 用户提示词
        user_prompt = caption.strip() if caption else "Extract event details from this image."

        # 调用 AI（视觉模型）
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )

            return await self.parse_response(response)

        except Exception as e:
            logger.error(f"❌ Image parsing error: {e}")
            raise
