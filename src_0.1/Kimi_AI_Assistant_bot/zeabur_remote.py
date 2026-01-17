# zeabur_remote.py
import os
import json
import logging
import requests
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# --- 配置 ---
ZEABUR_API_TOKEN = os.getenv("ZEABUR_API_TOKEN")
ZEABUR_GRAPHQL_ENDPOINT = "https://api.zeabur.com/graphql"

def _load_targets() -> Dict:
    """从环境变量加载目标服务配置"""
    targets_json = os.getenv("ZEABUR_TARGETS", "{}")
    try:
        return json.loads(targets_json)
    except json.JSONDecodeError:
        logger.error("ZEABUR_TARGETS 格式错误，无法解析 JSON")
        return {}

def _call_graphql(query: str, variables: dict = None) -> dict:
    """调用 Zeabur GraphQL API"""
    if not ZEABUR_API_TOKEN:
        raise ValueError("ZEABUR_API_TOKEN 未配置")
    
    headers = {
        "Authorization": f"Bearer {ZEABUR_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(
        ZEABUR_GRAPHQL_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=30
    )
    response.raise_for_status()
    return response.json()

def restart_service(service_id: str, environment_id: str) -> Tuple[bool, str]:
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
        logger.info(f"正在重启服务: {service_id}")
        result = _call_graphql(mutation, variables)
        
        if "errors" in result:
            error_msg = result["errors"][0].get("message", "未知错误")
            logger.error(f"重启失败: {error_msg}")
            return False, error_msg
        
        logger.info(f"重启成功: {result}")
        return True, "✅ 服务重启指令已发送 (Zeabur)"
        
    except Exception as e:
        logger.error(f"请求失败: {e}")
        return False, f"❌ 网络或API错误: {str(e)}"

def restart_by_name(target_name: str) -> Tuple[bool, str, Optional[str]]:
    targets = _load_targets()
    if target_name not in targets:
        return False, f"未找到目标 '{target_name}'", None
    
    target = targets[target_name]
    service_id = target.get("service_id")
    env_id = target.get("env_id")
    display_name = target.get("name", target_name)
    
    success, msg = restart_service(service_id, env_id)
    return success, msg, display_name

# 快捷方式
def restart_singbox() -> Tuple[bool, str]:
    return restart_by_name("singbox")[0:2]