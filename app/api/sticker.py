"""表情包API"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_db
from app.models.sticker import (
    StickerEmotion,
    StickerPersonalityMatch,
    StickerSendStrategy,
    StickerType,
)
from app.services.sticker import StickerSelector, StickerService, init_default_stickers

router = APIRouter(prefix="/sticker", tags=["表情包"])


# ========== 请求/响应模型 ==========
class StickerCreateRequest(BaseModel):
    """创建表情包请求"""

    name: str
    type: StickerType
    url: str
    emotion: Optional[StickerEmotion] = None
    personality_match: StickerPersonalityMatch = StickerPersonalityMatch.ALL
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    description: Optional[str] = None
    source: Optional[str] = None
    file_size: Optional[int] = None
    file_format: Optional[str] = None
    base_weight: float = 1.0


class StickerUpdateRequest(BaseModel):
    """更新表情包请求"""

    name: Optional[str] = None
    type: Optional[StickerType] = None
    url: Optional[str] = None
    emotion: Optional[StickerEmotion] = None
    personality_match: Optional[StickerPersonalityMatch] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    description: Optional[str] = None
    source: Optional[str] = None
    file_size: Optional[int] = None
    file_format: Optional[str] = None
    base_weight: Optional[float] = None
    is_active: Optional[bool] = None


class StickerSelectionRequest(BaseModel):
    """表情包选择请求"""

    current_emotion: dict[str, float]
    personality_type: str = "default"
    context_keywords: Optional[List[str]] = None
    is_serious_context: bool = False


class StickerSelectionResponse(BaseModel):
    """表情包选择响应"""

    sticker: Optional[dict] = None
    send_mode: str  # "only_sticker", "text_with_sticker", "no_sticker"
    match_score: Optional[float] = None
    reason: Optional[str] = None


class StickerListResponse(BaseModel):
    """表情包列表响应"""

    items: List[dict]
    total: int
    offset: int
    limit: int


class StickerStatisticsResponse(BaseModel):
    """表情包统计响应"""

    total_stickers: int
    by_type: dict[str, int]
    by_emotion: dict[str, int]
    total_usage: int


# ========== API接口 ==========
@router.get("/list", response_model=StickerListResponse)
async def list_stickers(
    type: Optional[StickerType] = Query(None, description="表情包类型"),
    emotion: Optional[StickerEmotion] = Query(None, description="关联情绪"),
    personality_match: Optional[StickerPersonalityMatch] = Query(None, description="适配人格"),
    is_active: bool = Query(True, description="是否启用"),
    limit: int = Query(100, ge=1, le=1000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
):
    """分页查询表情包列表"""
    sticker_service = StickerService(db)
    stickers, total = await sticker_service.list_stickers(
        type=type,
        emotion=emotion,
        personality_match=personality_match,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    return StickerListResponse(
        items=[sticker.to_dict() for sticker in stickers],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/search")
async def search_stickers(
    keyword: str = Query(..., description="搜索关键词"),
    type: Optional[StickerType] = Query(None, description="表情包类型"),
    emotion: Optional[StickerEmotion] = Query(None, description="关联情绪"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db),
):
    """搜索表情包"""
    sticker_service = StickerService(db)
    stickers = await sticker_service.search_stickers(
        keyword=keyword,
        type=type,
        emotion=emotion,
        limit=limit,
    )

    return [sticker.to_dict() for sticker in stickers]


@router.get("/{sticker_id}")
async def get_sticker(
    sticker_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取单个表情包详情"""
    sticker_service = StickerService(db)
    sticker = await sticker_service.get_sticker_by_id(sticker_id)

    if not sticker:
        raise HTTPException(status_code=404, detail="表情包不存在")

    return sticker.to_dict()


@router.post("/", status_code=201)
async def create_sticker(
    request: StickerCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """创建新表情包"""
    sticker_service = StickerService(db)
    sticker = await sticker_service.create_sticker(**request.dict())
    return sticker.to_dict()


@router.put("/{sticker_id}")
async def update_sticker(
    sticker_id: str,
    request: StickerUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """更新表情包信息"""
    sticker_service = StickerService(db)
    sticker = await sticker_service.update_sticker(
        sticker_id=sticker_id, **request.dict(exclude_unset=True)
    )

    if not sticker:
        raise HTTPException(status_code=404, detail="表情包不存在")

    return sticker.to_dict()


@router.delete("/{sticker_id}", status_code=204)
async def delete_sticker(
    sticker_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除表情包（软删除）"""
    sticker_service = StickerService(db)
    success = await sticker_service.delete_sticker(sticker_id)

    if not success:
        raise HTTPException(status_code=404, detail="表情包不存在")


@router.post("/select", response_model=StickerSelectionResponse)
async def select_sticker(
    request: StickerSelectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """智能选择表情包"""
    selector = StickerSelector(db)
    sticker, send_mode = await selector.select_stickers_for_reply(
        current_emotion=request.current_emotion,
        personality_type=request.personality_type,
        context_keywords=request.context_keywords,
        is_serious_context=request.is_serious_context,
    )

    if not sticker:
        return StickerSelectionResponse(
            sticker=None, send_mode="no_sticker", match_score=None, reason=None
        )

    return StickerSelectionResponse(
        sticker=sticker.to_dict(),
        send_mode=send_mode,
        match_score=None,  # 简化返回，如需详细信息可调用select_optimal_sticker
        reason=None,
    )


@router.post("/select/detailed")
async def select_sticker_detailed(
    request: StickerSelectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """智能选择表情包（返回详细匹配信息）"""
    selector = StickerSelector(db)
    selection = await selector.select_optimal_sticker(
        current_emotion=request.current_emotion,
        personality_type=request.personality_type,
        context_keywords=request.context_keywords,
        is_serious_context=request.is_serious_context,
    )

    if not selection:
        return {
            "sticker": None,
            "send_mode": "no_sticker",
            "match_score": 0,
            "emotion_match": 0,
            "personality_match": 0,
            "context_match": 0,
            "reason": "当前场景不适合发表情包",
        }

    # 确定发送模式
    send_mode = "text_with_sticker"
    if request.personality_type:
        personality_coeff = StickerSendStrategy().personality_adjustment.get(
            request.personality_type, 1.0
        )
        import random

        if random.random() < 0.375 * personality_coeff:
            send_mode = "only_sticker"

    # 记录使用次数
    await selector.sticker_service.increment_usage(selection.sticker.id)

    return {
        "sticker": selection.sticker.to_dict(),
        "send_mode": send_mode,
        "match_score": selection.match_score,
        "emotion_match": selection.emotion_match,
        "personality_match": selection.personality_match,
        "context_match": selection.context_match,
        "reason": selection.reason,
    }


@router.get("/statistics", response_model=StickerStatisticsResponse)
async def get_sticker_statistics(
    db: AsyncSession = Depends(get_db),
):
    """获取表情包统计信息"""
    sticker_service = StickerService(db)
    stats = await sticker_service.get_statistics()
    return StickerStatisticsResponse(**stats)


@router.post("/init", status_code=200)
async def initialize_stickers(
    overwrite: bool = Query(False, description="是否覆盖已有的表情包"),
    db: AsyncSession = Depends(get_db),
):
    """初始化默认表情包库"""
    count = await init_default_stickers(db, overwrite=overwrite)
    return {"success": True, "imported_count": count, "message": f"成功导入 {count} 个默认表情包"}


@router.post("/batch-import")
async def batch_import_stickers(
    stickers: List[StickerCreateRequest],
    db: AsyncSession = Depends(get_db),
):
    """批量导入表情包"""
    sticker_service = StickerService(db)
    count = await sticker_service.batch_import_stickers([s.dict() for s in stickers])
    return {"success": True, "imported_count": count, "message": f"成功导入 {count} 个表情包"}
