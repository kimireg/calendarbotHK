"""
配置管理模块
使用 Pydantic 进行环境变量验证
"""
import os
import json
import logging
from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class FamilyMemberConfig(BaseSettings):
    """家庭成员配置"""
    name: str
    role: str
    env_var: str
    icon: str = "📅"


class CalendarBotConfig(BaseSettings):
    """Calendar Bot 配置"""

    # Telegram 配置
    telegram_token: str = Field(..., alias="TELEGRAM_TOKEN")
    allowed_user_ids: str = Field(..., alias="ALLOWED_USER_IDS")

    # OpenRouter AI 配置
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL"
    )
    llm_model_name: str = Field(
        default="google/gemini-3-flash-preview",
        alias="LLM_MODEL_NAME"
    )

    # Google Calendar 配置
    google_credentials_json: str = Field(..., alias="GOOGLE_CREDENTIALS_JSON")
    google_calendar_id: str = Field(..., alias="GOOGLE_CALENDAR_ID")
    google_calendar_id_kiki: Optional[str] = Field(None, alias="GOOGLE_CALENDAR_ID_KIKI")
    google_calendar_id_jason: Optional[str] = Field(None, alias="GOOGLE_CALENDAR_ID_JASON")
    google_calendar_id_janet: Optional[str] = Field(None, alias="GOOGLE_CALENDAR_ID_JANET")
    google_calendar_id_family: Optional[str] = Field(None, alias="GOOGLE_CALENDAR_ID_FAMILY")

    # 家庭成员配置（JSON 格式）
    family_config: Optional[str] = Field(None, alias="FAMILY_CONFIG")

    # Zeabur 远程控制配置
    zeabur_api_token: Optional[str] = Field(None, alias="ZEABUR_API_TOKEN")
    zeabur_targets: Optional[str] = Field(None, alias="ZEABUR_TARGETS")

    # 应用配置
    default_timezone: str = Field(default="Asia/Singapore", alias="DEFAULT_HOME_TZ")
    database_path: str = Field(default="data/calendar_bot_v2.db", alias="DB_PATH")

    # 日志配置
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("allowed_user_ids")
    @classmethod
    def parse_user_ids(cls, v: str) -> List[int]:
        """解析允许的用户 ID"""
        if not v:
            raise ValueError("ALLOWED_USER_IDS cannot be empty")
        return [int(x.strip()) for x in v.split(",") if x.strip()]

    @property
    def allowed_ids(self) -> List[int]:
        """获取解析后的用户 ID 列表"""
        return self.parse_user_ids(self.allowed_user_ids)

    def get_family_members(self) -> List[Dict[str, Any]]:
        """
        获取家庭成员配置
        优先使用 FAMILY_CONFIG 环境变量，否则使用默认配置
        """
        if self.family_config:
            try:
                return json.loads(self.family_config)
            except json.JSONDecodeError:
                logging.error("❌ FAMILY_CONFIG JSON 格式错误，使用默认配置")

        # 默认配置
        return [
            {
                "name": "Kimi",
                "role": "Default / Father",
                "env_var": "GOOGLE_CALENDAR_ID",
                "icon": "👱‍♂️"
            },
            {
                "name": "Kiki",
                "role": "Daughter",
                "env_var": "GOOGLE_CALENDAR_ID_KIKI",
                "icon": "👧"
            },
            {
                "name": "Jason",
                "role": "Son",
                "env_var": "GOOGLE_CALENDAR_ID_JASON",
                "icon": "👦"
            },
            {
                "name": "Janet",
                "role": "Wife",
                "env_var": "GOOGLE_CALENDAR_ID_JANET",
                "icon": "👩‍🎨"
            }
        ]

    def get_calendar_id(self, category: str) -> str:
        """
        根据分类获取对应的日历 ID
        """
        env_mapping = {
            "Kimi": self.google_calendar_id,
            "Kiki": self.google_calendar_id_kiki,
            "Jason": self.google_calendar_id_jason,
            "Janet": self.google_calendar_id_janet,
            "Family": self.google_calendar_id_family,
        }

        calendar_id = env_mapping.get(category)

        # 如果没有配置，回退到主日历
        if not calendar_id:
            logging.warning(f"⚠️ Calendar ID for '{category}' not configured, fallback to primary")
            return self.google_calendar_id or "primary"

        return calendar_id


def load_config() -> CalendarBotConfig:
    """加载配置"""
    return CalendarBotConfig()
