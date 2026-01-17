"""
Google Calendar 集成
"""
import json
import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pytz

from ..core.timezone_utils import resolve_timezone, smart_fix_year, smart_fix_end_time
from ..core.event_validator import EventValidator, normalize_recurrence

logger = logging.getLogger(__name__)


class GoogleCalendarClient:
    """Google Calendar 客户端"""

    def __init__(self, credentials_json: str, event_validator: EventValidator):
        """
        初始化客户端

        Args:
            credentials_json: Google 凭证 JSON 字符串
            event_validator: 事件验证器
        """
        self.credentials_json = credentials_json
        self.validator = event_validator
        self._service = None

    def get_service(self):
        """获取 Google Calendar 服务"""
        if self._service:
            return self._service

        if not self.credentials_json:
            raise ValueError("Google credentials not configured")

        try:
            info = json.loads(self.credentials_json)
            creds = Credentials.from_service_account_info(
                info,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            self._service = build('calendar', 'v3', credentials=creds)
            logger.info("✅ Google Calendar service initialized")
            return self._service
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Calendar: {e}")
            raise

    def _check_conflicts(
        self,
        service,
        calendar_id: str,
        start_dt: datetime,
        end_dt: datetime
    ) -> List[str]:
        """
        检查时间冲突

        Args:
            service: Google Calendar 服务
            calendar_id: 日历 ID
            start_dt: 开始时间
            end_dt: 结束时间

        Returns:
            冲突事件列表
        """
        try:
            time_min = start_dt.isoformat()
            time_max = end_dt.isoformat()

            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            items = events_result.get('items', [])

            # 只返回有具体时间的事件（排除全天事件）
            conflicts = []
            for event in items:
                if 'dateTime' in event['start']:
                    summary = event.get('summary', '无标题')
                    conflicts.append(f"• {summary}")

            return conflicts

        except Exception as e:
            logger.error(f"❌ Check conflicts error: {e}")
            return []

    def _insert_event(self, service, calendar_id: str, body: Dict) -> Dict:
        """
        插入事件

        Args:
            service: Google Calendar 服务
            calendar_id: 日历 ID
            body: 事件数据

        Returns:
            创建的事件对象
        """
        return service.events().insert(
            calendarId=calendar_id,
            body=body
        ).execute()

    async def create_event(
        self,
        event_data: Dict[str, Any],
        calendar_id: str,
        user_current_tz: str,
        default_category: str
    ) -> Tuple[bool, str, List[str], Optional[datetime], Optional[datetime], Optional[str], Optional[str], str, bool]:
        """
        创建日历事件

        Args:
            event_data: 事件数据
            calendar_id: 目标日历 ID
            user_current_tz: 用户当前时区
            default_category: 默认分类

        Returns:
            (成功, 链接/错误信息, 冲突列表, 开始时间, 结束时间, 日历ID, 事件ID, 回退消息, 是否全天)
        """
        # 验证数据
        is_valid, err_msg = self.validator.validate_and_fix_payload(event_data, default_category)
        if not is_valid:
            return False, f"数据校验失败: {err_msg}", [], None, None, None, None, "", False

        try:
            service = self.get_service()
            is_all_day = event_data.get('is_all_day', False)

            # 构建事件主体
            body = {
                'summary': event_data.get('summary', 'New Event'),
                'description': f"{event_data.get('description', '')}\n\n[Created by CalendarBot]",
                'location': event_data.get('location', ''),
            }

            dt_start_display = None
            dt_end_display = None
            fallback_msg = ""
            conflicts = []

            if is_all_day:
                # 全天事件
                start_date_str = event_data['start_time']
                dt_start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                dt_end_date = dt_start_date + timedelta(days=1)

                body['start'] = {'date': start_date_str}
                body['end'] = {'date': dt_end_date.strftime('%Y-%m-%d')}
                body['colorId'] = '11'  # 番茄色标记全天事件

                dt_start_display = dt_start_date
                dt_end_display = dt_end_date

            else:
                # 普通事件（有具体时间）
                raw_start_tz = event_data.get('start_timezone', event_data.get('event_timezone'))
                final_start_tz, start_tz_obj, fb_start = resolve_timezone(raw_start_tz, user_current_tz)

                raw_end_tz = event_data.get('end_timezone', raw_start_tz)
                final_end_tz, end_tz_obj, fb_end = resolve_timezone(raw_end_tz, user_current_tz)

                if fb_start or fb_end:
                    fallback_msg = f"\n⚠️ AI未识别时区，已按 {user_current_tz} 安排。"

                # 解析开始时间
                dt_start_naive = datetime.strptime(event_data['start_time'], '%Y-%m-%d %H:%M:%S')
                dt_start_aware, dt_start_naive = smart_fix_year(dt_start_naive, start_tz_obj)

                # 解析结束时间
                if event_data.get('end_time'):
                    dt_end_naive_raw = datetime.strptime(event_data['end_time'], '%Y-%m-%d %H:%M:%S')
                    dt_end_aware = smart_fix_end_time(dt_start_aware, dt_end_naive_raw, end_tz_obj)
                else:
                    # 默认持续 1 小时
                    dt_end_aware = dt_start_aware + timedelta(hours=1)
                    final_end_tz = final_start_tz

                # 检查冲突
                conflicts = await asyncio.to_thread(
                    self._check_conflicts,
                    service,
                    calendar_id,
                    dt_start_aware,
                    dt_end_aware
                )

                # 设置时间
                body['start'] = {
                    'dateTime': dt_start_naive.isoformat(),
                    'timeZone': final_start_tz
                }
                body['end'] = {
                    'dateTime': dt_end_aware.strftime('%Y-%m-%dT%H:%M:%S'),
                    'timeZone': final_end_tz
                }

                dt_start_display = dt_start_aware
                dt_end_display = dt_end_aware

            # 添加重复规则
            if recurrence := normalize_recurrence(event_data.get('recurrence')):
                body['recurrence'] = recurrence

            # 插入事件
            event = await asyncio.to_thread(self._insert_event, service, calendar_id, body)

            return (
                True,
                event.get('htmlLink'),
                conflicts,
                dt_start_display,
                dt_end_display,
                calendar_id,
                event['id'],
                fallback_msg,
                is_all_day
            )

        except Exception as e:
            logger.error(f"❌ Create event error: {e}", exc_info=True)
            return False, str(e), [], None, None, None, None, "", False

    async def delete_event(self, calendar_id: str, event_id: str) -> Tuple[bool, str]:
        """
        删除事件

        Args:
            calendar_id: 日历 ID
            event_id: 事件 ID

        Returns:
            (成功, 消息)
        """
        try:
            service = self.get_service()
            await asyncio.to_thread(
                service.events().delete(calendarId=calendar_id, eventId=event_id).execute
            )
            return True, "已删除"
        except Exception as e:
            logger.error(f"❌ Delete event error: {e}")
            return False, str(e)

    async def list_today_events(
        self,
        calendar_id: str,
        user_timezone: str
    ) -> List[Dict[str, Any]]:
        """
        列出今天的事件

        Args:
            calendar_id: 日历 ID
            user_timezone: 用户时区

        Returns:
            事件列表
        """
        try:
            service = self.get_service()
            tz_obj = pytz.timezone(user_timezone)
            now = datetime.now(tz_obj)

            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)

            events_result = await asyncio.to_thread(
                service.events().list(
                    calendarId=calendar_id,
                    timeMin=start_of_day.isoformat(),
                    timeMax=end_of_day.isoformat(),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute
            )

            return events_result.get('items', [])

        except Exception as e:
            logger.error(f"❌ List events error: {e}")
            raise
