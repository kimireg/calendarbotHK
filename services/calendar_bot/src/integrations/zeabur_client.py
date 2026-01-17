"""
Zeabur 远程控制客户端
"""
import json
import logging
from typing import Optional, Dict, Tuple

import requests

logger = logging.getLogger(__name__)


class ZeaburClient:
    """Zeabur API 客户端"""

    GRAPHQL_ENDPOINT = "https://api.zeabur.com/graphql"

    def __init__(self, api_token: Optional[str], targets_json: Optional[str]):
        """
        初始化客户端

        Args:
            api_token: Zeabur API Token
            targets_json: 目标服务配置 JSON
        """
        self.api_token = api_token
        self.targets = self._load_targets(targets_json)

    def _load_targets(self, targets_json: Optional[str]) -> Dict:
        """加载目标服务配置"""
        if not targets_json:
            return {}

        try:
            return json.loads(targets_json)
        except json.JSONDecodeError:
            logger.error("❌ ZEABUR_TARGETS JSON format error")
            return {}

    def _call_graphql(self, query: str, variables: dict = None) -> dict:
        """
        调用 Zeabur GraphQL API

        Args:
            query: GraphQL 查询
            variables: 变量

        Returns:
            响应数据
        """
        if not self.api_token:
            raise ValueError("ZEABUR_API_TOKEN not configured")

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.GRAPHQL_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def restart_service(self, service_id: str, environment_id: str) -> Tuple[bool, str]:
        """
        重启服务

        Args:
            service_id: 服务 ID
            environment_id: 环境 ID

        Returns:
            (成功, 消息)
        """
        mutation = """
        mutation RestartService($serviceID: ObjectID!, $environmentID: ObjectID!) {
            restartService(serviceID: $serviceID, environmentID: $environmentID)
        }
        """

        variables = {
            "serviceID": service_id,
            "environmentID": environment_id
        }

        try:
            logger.info(f"🔄 Restarting service: {service_id}")
            result = self._call_graphql(mutation, variables)

            if "errors" in result:
                error_msg = result["errors"][0].get("message", "Unknown error")
                logger.error(f"❌ Restart failed: {error_msg}")
                return False, error_msg

            logger.info(f"✅ Service restart initiated")
            return True, "✅ 服务重启指令已发送 (Zeabur)"

        except Exception as e:
            logger.error(f"❌ Request failed: {e}")
            return False, f"❌ 网络或API错误: {str(e)}"

    def restart_by_name(self, target_name: str) -> Tuple[bool, str, Optional[str]]:
        """
        通过名称重启服务

        Args:
            target_name: 目标名称

        Returns:
            (成功, 消息, 显示名称)
        """
        if target_name not in self.targets:
            return False, f"未找到目标 '{target_name}'", None

        target = self.targets[target_name]
        service_id = target.get("service_id")
        env_id = target.get("env_id")
        display_name = target.get("name", target_name)

        success, msg = self.restart_service(service_id, env_id)
        return success, msg, display_name

    def restart_singbox(self) -> Tuple[bool, str]:
        """
        快捷方式：重启 Singbox Updater

        Returns:
            (成功, 消息)
        """
        return self.restart_by_name("singbox")[0:2]
