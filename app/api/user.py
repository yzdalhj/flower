"""用户管理 API"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import get_db
from app.models.account import Account
from app.models.user import User, UserProfile

router = APIRouter(prefix="/users", tags=["用户管理"])


class UserListItem(BaseModel):
    """用户列表项"""

    id: str
    account_id: str
    account_name: Optional[str]
    platform_user_id: str
    platform_type: str
    nickname: Optional[str]
    avatar_url: Optional[str]
    relationship_stage: str
    trust_score: float
    intimacy_score: float
    total_messages: int
    last_interaction_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """用户列表响应"""

    total: int
    items: List[UserListItem]


class UserProfileResponse(BaseModel):
    """用户画像响应"""

    id: str
    user_id: str
    age: Optional[int]
    gender: Optional[str]
    location: Optional[str]
    occupation: Optional[str]
    interests: Optional[List[str]]
    birthday: Optional[datetime]
    emotional_state: Optional[str]
    preferred_topics: Optional[List[str]]
    disliked_topics: Optional[List[str]]


class UserDetailResponse(BaseModel):
    """用户详情响应"""

    id: str
    account_id: str
    account_name: Optional[str]
    platform_user_id: str
    platform_type: str
    nickname: Optional[str]
    avatar_url: Optional[str]
    relationship_stage: str
    trust_score: float
    intimacy_score: float
    total_messages: int
    last_interaction_at: Optional[datetime]
    profile: Optional[UserProfileResponse]
    created_at: datetime
    updated_at: datetime


class UpdateUserRequest(BaseModel):
    """更新用户请求"""

    nickname: Optional[str] = None
    relationship_stage: Optional[str] = None
    trust_score: Optional[float] = None
    intimacy_score: Optional[float] = None


class UpdateUserProfileRequest(BaseModel):
    """更新用户画像请求"""

    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    occupation: Optional[str] = None
    interests: Optional[List[str]] = None
    birthday: Optional[datetime] = None
    emotional_state: Optional[str] = None
    preferred_topics: Optional[List[str]] = None
    disliked_topics: Optional[List[str]] = None


@router.get("", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    account_id: Optional[str] = Query(None, description="账号ID筛选"),
    platform_type: Optional[str] = Query(None, description="平台类型筛选"),
    relationship_stage: Optional[str] = Query(None, description="关系阶段筛选"),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """
    获取用户列表
    """
    # 构建基础查询
    base_query = select(User).options(selectinload(User.account))

    # 应用筛选条件
    if account_id:
        base_query = base_query.where(User.account_id == account_id)
    if platform_type:
        base_query = base_query.where(User.platform_type == platform_type)
    if relationship_stage:
        base_query = base_query.where(User.relationship_stage == relationship_stage)

    # 获取总数
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 获取分页数据
    offset = (page - 1) * page_size
    query = base_query.order_by(desc(User.last_interaction_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    # 构建响应
    items = []
    for user in users:
        items.append(
            UserListItem(
                id=user.id,
                account_id=user.account_id,
                account_name=user.account.name if user.account else None,
                platform_user_id=user.platform_user_id,
                platform_type=user.platform_type,
                nickname=user.nickname,
                avatar_url=user.avatar_url,
                relationship_stage=user.relationship_stage,
                trust_score=user.trust_score,
                intimacy_score=user.intimacy_score,
                total_messages=user.total_messages,
                last_interaction_at=user.last_interaction_at,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        )

    return UserListResponse(total=total, items=items)


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserDetailResponse:
    """
    获取用户详情
    """
    result = await db.execute(
        select(User)
        .options(selectinload(User.account), selectinload(User.profile))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 构建画像响应
    profile_response = None
    if user.profile:
        import json

        profile_response = UserProfileResponse(
            id=user.profile.id,
            user_id=user.profile.user_id,
            age=user.profile.age,
            gender=user.profile.gender,
            location=user.profile.location,
            occupation=user.profile.occupation,
            interests=json.loads(user.profile.interests) if user.profile.interests else None,
            birthday=user.profile.birthday,
            emotional_state=user.profile.emotional_state,
            preferred_topics=(
                json.loads(user.profile.preferred_topics) if user.profile.preferred_topics else None
            ),
            disliked_topics=(
                json.loads(user.profile.disliked_topics) if user.profile.disliked_topics else None
            ),
        )

    return UserDetailResponse(
        id=user.id,
        account_id=user.account_id,
        account_name=user.account.name if user.account else None,
        platform_user_id=user.platform_user_id,
        platform_type=user.platform_type,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        relationship_stage=user.relationship_stage,
        trust_score=user.trust_score,
        intimacy_score=user.intimacy_score,
        total_messages=user.total_messages,
        last_interaction_at=user.last_interaction_at,
        profile=profile_response,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.put("/{user_id}", response_model=UserListItem)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
) -> UserListItem:
    """
    更新用户信息
    """
    result = await db.execute(
        select(User).options(selectinload(User.account)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
    if request.nickname is not None:
        user.nickname = request.nickname
    if request.relationship_stage is not None:
        user.relationship_stage = request.relationship_stage
    if request.trust_score is not None:
        user.trust_score = request.trust_score
    if request.intimacy_score is not None:
        user.intimacy_score = request.intimacy_score

    await db.commit()
    await db.refresh(user)

    return UserListItem(
        id=user.id,
        account_id=user.account_id,
        account_name=user.account.name if user.account else None,
        platform_user_id=user.platform_user_id,
        platform_type=user.platform_type,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        relationship_stage=user.relationship_stage,
        trust_score=user.trust_score,
        intimacy_score=user.intimacy_score,
        total_messages=user.total_messages,
        last_interaction_at=user.last_interaction_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.put("/{user_id}/profile", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: str,
    request: UpdateUserProfileRequest,
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """
    更新用户画像
    """
    import json

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        # 创建新画像
        profile = UserProfile(user_id=user_id)
        db.add(profile)

    # 更新字段
    if request.age is not None:
        profile.age = request.age
    if request.gender is not None:
        profile.gender = request.gender
    if request.location is not None:
        profile.location = request.location
    if request.occupation is not None:
        profile.occupation = request.occupation
    if request.interests is not None:
        profile.interests = json.dumps(request.interests)
    if request.birthday is not None:
        profile.birthday = request.birthday
    if request.emotional_state is not None:
        profile.emotional_state = request.emotional_state
    if request.preferred_topics is not None:
        profile.preferred_topics = json.dumps(request.preferred_topics)
    if request.disliked_topics is not None:
        profile.disliked_topics = json.dumps(request.disliked_topics)

    await db.commit()
    await db.refresh(profile)

    return UserProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        age=profile.age,
        gender=profile.gender,
        location=profile.location,
        occupation=profile.occupation,
        interests=json.loads(profile.interests) if profile.interests else None,
        birthday=profile.birthday,
        emotional_state=profile.emotional_state,
        preferred_topics=json.loads(profile.preferred_topics) if profile.preferred_topics else None,
        disliked_topics=json.loads(profile.disliked_topics) if profile.disliked_topics else None,
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    删除用户
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.delete(user)
    await db.commit()

    return {"message": "用户已删除"}


@router.get("/accounts/tree", response_model=List[Dict[str, Any]])
async def get_account_tree(
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    获取账号树结构
    """
    result = await db.execute(select(Account).order_by(Account.name))
    accounts = result.scalars().all()

    tree = []
    for account in accounts:
        # 获取该账号下的用户数量
        user_count_result = await db.execute(
            select(func.count(User.id)).where(User.account_id == account.id)
        )
        user_count = user_count_result.scalar() or 0

        tree.append(
            {
                "id": account.id,
                "name": account.name,
                "platform": account.platform,
                "status": account.status,
                "user_count": user_count,
            }
        )

    return tree
