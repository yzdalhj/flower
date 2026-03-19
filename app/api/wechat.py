"""微信客户端主控API"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.platform.gateway import get_gateway
from app.platform.types import PlatformType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wechat", tags=["wechat"])

settings = get_settings()


@router.get("/callback")
async def wechat_callback_verify(
    request: Request,
    signature: str,
    timestamp: str,
    nonce: str,
    echostr: str,
) -> PlainTextResponse:
    """微信公众号回调验证"""
    gateway = get_gateway()

    result = await gateway.process_webhook_verify(
        PlatformType.WECHAT_OFFICIAL,
        {
            "signature": signature,
            "timestamp": timestamp,
            "nonce": nonce,
            "echostr": echostr,
        },
    )

    if result is not None:
        return PlainTextResponse(content=result)

    raise HTTPException(status_code=400, detail="Verification failed")


@router.post("/callback")
async def wechat_callback(request: Request) -> PlainTextResponse:
    """微信公众号消息回调"""
    gateway = get_gateway()

    body = await request.body()
    body_str = body.decode("utf-8")

    xml_dict = {"xml": body_str}

    response = await gateway.process_message(PlatformType.WECHAT_OFFICIAL, xml_dict)

    if response and response.content.text:
        from app.platform.adapters.wechat_official import WechatOfficialAdapter

        if response:

            message = await gateway.get_adapter(PlatformType.WECHAT_OFFICIAL).parse_message(
                xml_dict
            )
            if message:
                adapter = WechatOfficialAdapter(token="")
                xml_response = adapter._response_to_xml(message, response)
                return PlainTextResponse(content=xml_response, media_type="application/xml")

    return PlainTextResponse(content="success")


@router.get("/status")
async def wechat_status() -> Dict[str, Any]:
    """微信接入状态查询"""
    gateway = get_gateway()
    adapter = gateway.get_adapter(PlatformType.WECHAT_OFFICIAL)

    return {
        "wechat_official_configured": adapter is not None,
        "status": "ready" if adapter else "not_configured",
    }


@router.post("/webhook/{platform}")
async def generic_webhook(request: Request, platform: str) -> Dict[str, Any]:
    """通用Webhook入口"""
    gateway = get_gateway()

    try:
        platform_type = PlatformType(platform)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")

    body = await request.json()

    response = await gateway.process_message(platform_type, body)

    if response:
        return {
            "success": True,
            "response": response.model_dump(),
        }

    return {"success": True}
