from app.services.relationship.relationship_service import RelationshipService

from .models import RelationshipStage
from .profile_service import UserProfileService


class ProfilePromptInjector:
    """
    用户画像Prompt注入器
    将用户画像信息注入到系统提示中
    """

    def __init__(
        self, profile_service: UserProfileService, relationship_service: RelationshipService
    ):
        self.profile_service = profile_service
        self.relationship_service = relationship_service

    async def build_profile_context(self, user_id: str) -> str:
        """
        构建用户画像上下文
        用于动态Prompt构建
        """
        profile = await self.profile_service.get_profile(user_id)

        if not profile:
            return ""

        context_parts = []

        # 基础画像
        summary = await self.profile_service.generate_profile_summary(user_id)
        if summary:
            context_parts.append(f"【用户画像】\n{summary}")

        # 关系状态
        rel = profile.relationship
        context_parts.append(
            f"""
【关系状态】
- 当前阶段: {self._translate_stage(rel.stage)}
- 亲密度: {rel.intimacy:.0%}
- 信任度: {rel.trust:.0%}
- 互动次数: {rel.interaction_count}
"""
        )

        # 关系阶段特定的行为指导
        behavior_guide = self._get_behavior_guide(rel.stage)
        context_parts.append(f"【行为指导】\n{behavior_guide}")

        return "\n\n".join(context_parts)

    def _translate_stage(self, stage: RelationshipStage) -> str:
        """翻译关系阶段"""
        translations = {
            RelationshipStage.STRANGER: "陌生人（礼貌交流）",
            RelationshipStage.ACQUAINTANCE: "熟人（日常聊天）",
            RelationshipStage.FRIEND: "朋友（情感支持）",
            RelationshipStage.CLOSE_FRIEND: "密友（深度交流）",
            RelationshipStage.CONFIDANT: "挚友（无话不谈）",
        }
        return translations.get(stage, "未知")

    def _get_behavior_guide(self, stage: RelationshipStage) -> str:
        """
        根据关系阶段返回行为指导
        """
        guides = {
            RelationshipStage.STRANGER: """
- 保持礼貌和距离
- 不涉及隐私话题
- 展现友好但不过分热情
- 回复相对正式
""",
            RelationshipStage.ACQUAINTANCE: """
- 可以聊日常话题
- 偶尔分享个人看法
- 开始记住对方喜好
- 语气可以更轻松
""",
            RelationshipStage.FRIEND: """
- 提供情感支持
- 记住重要细节
- 可以开玩笑和吐槽
- 用更口语化的表达
""",
            RelationshipStage.CLOSE_FRIEND: """
- 深度共情和理解
- 主动关心和问候
- 分享AI的"个人"经历
- 可以怼人、开玩笑
""",
            RelationshipStage.CONFIDANT: """
- 完全信任和接纳
- 无话不谈的亲密
- 像真正的挚友一样
- 可以说心里话
""",
        }
        return guides.get(stage, "")

    async def inject_into_prompt(self, base_prompt: str, user_id: str) -> str:
        """
        将用户画像上下文注入到基础Prompt中
        """
        profile_context = await self.build_profile_context(user_id)
        if not profile_context:
            return base_prompt

        # 在系统提示后插入画像上下文
        if "【系统提示】" in base_prompt:
            parts = base_prompt.split("【系统提示】", 1)
            return f"{parts[0]}【系统提示】\n\n{profile_context}\n\n{parts[1]}"
        else:
            return f"{profile_context}\n\n{base_prompt}"
