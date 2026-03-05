import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

import spacy

from .models import UserProfile


class UserProfileService:
    """
    用户画像管理服务
    集成spaCy NER进行实体提取和画像更新
    """

    def __init__(self):
        # 使用spaCy中文模型进行NER
        try:
            self.nlp = spacy.load("zh_core_web_sm")
        except OSError:
            # 如果模型未安装，使用基础模式（仅正则提取）
            self.nlp = None
        self.profile_store: Dict[str, UserProfile] = {}

    async def get_or_create_profile(self, user_id: str) -> UserProfile:
        """获取或创建用户画像"""
        if user_id not in self.profile_store:
            profile = UserProfile(user_id=user_id)
            self.profile_store[user_id] = profile
        return self.profile_store[user_id]

    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        return self.profile_store.get(user_id)

    async def save_profile(self, profile: UserProfile):
        """保存用户画像"""
        self.profile_store[profile.user_id] = profile

    async def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        使用spaCy NER提取文本中的实体

        Returns:
            {
                "PERSON": ["张三", "李四"],
                "ORG": ["腾讯"],
                "GPE": ["北京"],
                "EVENT": ["生日"],
                ...
            }
        """
        entities = defaultdict(list)

        # 如果spaCy模型可用，使用NER提取
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                entities[ent.label_].append(ent.text)
        else:
            # 基础正则提取（当spaCy模型不可用时）
            # 提取人名（简单规则：2-3个汉字）
            name_patterns = [
                r"我叫([\u4e00-\u9fa5]{2,3})",
                r"我是([\u4e00-\u9fa5]{2,3})",
            ]
            for pattern in name_patterns:
                matches = re.findall(pattern, text)
                entities["PERSON"].extend(matches)

            # 提取地点
            location_patterns = [
                r"在([\u4e00-\u9fa5]{2,5})(?:工作|生活|住)",
                r"住在([\u4e00-\u9fa5]{2,5})",
            ]
            for pattern in location_patterns:
                matches = re.findall(pattern, text)
                entities["GPE"].extend(matches)

            # 提取组织
            org_keywords = ["公司", "学校", "医院", "工厂", "企业", "集团"]
            for keyword in org_keywords:
                if keyword in text:
                    # 提取关键词前的2-4个字
                    match = re.search(rf"([\u4e00-\u9fa5]{{2,4}}){keyword}", text)
                    if match:
                        entities["ORG"].append(match.group(1) + keyword)

        # 额外提取偏好相关实体（自定义规则）
        preference_entities = self._extract_preferences(text)
        entities.update(preference_entities)

        return dict(entities)

    def _extract_preferences(self, text: str) -> Dict[str, List[str]]:
        """
        基于规则提取用户偏好
        使用正则和关键词匹配
        """
        preferences = defaultdict(list)

        # 喜好模式
        like_patterns = [
            r"喜欢(.+?)[，。！?]",
            r"爱(.+?)[，。！?]",
            r"对(.+?)感兴趣",
            r"我爱(.+?)[，。！?]",
            r"我最喜欢(.+?)[，。！?]",
        ]

        for pattern in like_patterns:
            matches = re.findall(pattern, text)
            preferences["LIKES"].extend([m.strip() for m in matches if m.strip()])

        # 厌恶模式
        dislike_patterns = [
            r"讨厌(.+?)[，。！?]",
            r"不喜欢(.+?)[，。！?]",
            r"烦(.+?)[，。！?]",
            r"我恨(.+?)[，。！?]",
            r"我最讨厌(.+?)[，。！?]",
        ]

        for pattern in dislike_patterns:
            matches = re.findall(pattern, text)
            preferences["DISLIKES"].extend([m.strip() for m in matches if m.strip()])

        return dict(preferences)

    async def update_profile_from_interaction(
        self, user_id: str, user_message: str, ai_response: str
    ) -> UserProfile:
        """
        基于单次互动更新用户画像
        """
        profile = await self.get_or_create_profile(user_id)

        # 1. 提取实体
        entities = await self.extract_entities(user_message)

        # 2. 更新基础信息
        await self._update_basic_info(profile, entities)

        # 3. 更新偏好
        await self._update_preferences(profile, entities)

        # 4. 更新互动统计
        await self._update_interaction_stats(profile)

        # 5. 更新实体缓存
        if entities:
            for entity_type, values in entities.items():
                if entity_type not in profile.extracted_entities:
                    profile.extracted_entities[entity_type] = []
                for value in values:
                    if value not in profile.extracted_entities[entity_type]:
                        profile.extracted_entities[entity_type].append(value)

        # 6. 更新时间戳
        profile.updated_at = datetime.now()

        # 7. 保存
        await self.save_profile(profile)

        return profile

    async def _update_basic_info(self, profile: UserProfile, entities: Dict):
        """更新基础信息"""
        # 姓名
        if "PERSON" in entities and entities["PERSON"]:
            name = entities["PERSON"][0]
            if not profile.basic_info.get("name") and len(name) <= 3:
                profile.basic_info["name"] = name

        # 地理位置
        if "GPE" in entities and entities["GPE"]:
            profile.basic_info["location"] = entities["GPE"][0]

        # 组织/职业推断
        if "ORG" in entities and entities["ORG"]:
            org = entities["ORG"][0]
            profile.basic_info["organization"] = org
            # 简单职业推断
            if any(
                keyword in org for keyword in ["科技", "软件", "互联网", "科技公司", "互联网公司"]
            ):
                profile.basic_info["occupation"] = "程序员"
            elif any(keyword in org for keyword in ["学校", "大学", "中学", "小学"]):
                profile.basic_info["occupation"] = "学生"
            elif any(keyword in org for keyword in ["医院", "诊所"]):
                profile.basic_info["occupation"] = "医生/护士"

        # 日期信息
        if "DATE" in entities:
            date_text = entities["DATE"][0]
            # 识别生日
            if any(keyword in date_text for keyword in ["生日", "出生", "年月"]):
                profile.basic_info["birthday"] = date_text

    async def _update_preferences(self, profile: UserProfile, entities: Dict):
        """更新用户偏好"""
        if "LIKES" in entities:
            if "likes" not in profile.preferences:
                profile.preferences["likes"] = []
            for like in entities["LIKES"]:
                if like not in profile.preferences["likes"] and len(like) <= 10:
                    profile.preferences["likes"].append(like)

        if "DISLIKES" in entities:
            if "dislikes" not in profile.preferences:
                profile.preferences["dislikes"] = []
            for dislike in entities["DISLIKES"]:
                if dislike not in profile.preferences["dislikes"] and len(dislike) <= 10:
                    profile.preferences["dislikes"].append(dislike)

    async def _update_interaction_stats(self, profile: UserProfile):
        """更新互动统计"""
        if "total_messages" not in profile.interaction_stats:
            profile.interaction_stats["total_messages"] = 0
        profile.interaction_stats["total_messages"] += 1

        profile.interaction_stats["last_interaction"] = datetime.now().isoformat()

        # 计算互动频率（最近7天）
        if "interaction_history" not in profile.interaction_stats:
            profile.interaction_stats["interaction_history"] = []
        profile.interaction_stats["interaction_history"].append(datetime.now().isoformat())

        # 只保留最近30天的记录
        thirty_days_ago = datetime.now().timestamp() - 30 * 24 * 3600
        profile.interaction_stats["interaction_history"] = [
            dt
            for dt in profile.interaction_stats["interaction_history"]
            if datetime.fromisoformat(dt).timestamp() > thirty_days_ago
        ]

        # 计算日平均互动次数
        days = min(30, len(profile.interaction_stats["interaction_history"]) // 10 + 1)
        profile.interaction_stats["interaction_frequency"] = min(
            1.0, len(profile.interaction_stats["interaction_history"]) / days / 10
        )

    async def generate_profile_summary(self, user_id: str) -> str:
        """
        生成用户画像文本摘要
        用于Prompt构建时的用户画像上下文
        """
        profile = await self.get_profile(user_id)

        if not profile:
            return ""

        summary_parts = []

        # 基础信息
        basic = profile.basic_info
        if basic.get("name"):
            summary_parts.append(f"用户叫{basic['name']}")
        if basic.get("location"):
            summary_parts.append(f"住在{basic['location']}")
        if basic.get("occupation"):
            summary_parts.append(f"是一名{basic['occupation']}")

        # 偏好
        prefs = profile.preferences
        if prefs.get("likes"):
            top_likes = prefs["likes"][:3]
            summary_parts.append(f"喜欢{', '.join(top_likes)}")
        if prefs.get("dislikes"):
            top_dislikes = prefs["dislikes"][:2]
            summary_parts.append(f"讨厌{', '.join(top_dislikes)}")

        # 情感模式
        emotional = profile.emotional_patterns
        if emotional.get("comfort_topics"):
            summary_parts.append(f"聊{', '.join(emotional['comfort_topics'][:2])}时心情会好")

        # 关系状态
        rel = profile.relationship
        summary_parts.append(f"目前关系阶段：{rel.stage.value}，亲密度{rel.intimacy:.2f}")

        return "。".join(summary_parts)
