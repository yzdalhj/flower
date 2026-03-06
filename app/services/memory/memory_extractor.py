"""
记忆提取服务
从对话中提取重要信息，检测事件，生成摘要
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ExtractedInfo:
    """提取的信息"""

    info_type: str  # name/age/location/preference/event/fact
    key: str
    value: str
    confidence: float = 0.8
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DetectedEvent:
    """检测到的事件"""

    event_type: str  # birthday/job_change/moving/relationship/etc
    description: str
    date: Optional[str] = None
    participants: List[str] = field(default_factory=list)
    importance: float = 0.7
    source: str = ""


@dataclass
class ConversationSummary:
    """对话摘要"""

    summary: str
    key_topics: List[str] = field(default_factory=list)
    extracted_info: List[ExtractedInfo] = field(default_factory=list)
    detected_events: List[DetectedEvent] = field(default_factory=list)
    emotional_tone: str = "neutral"
    conversation_length: int = 0


class MemoryExtractor:
    """
    记忆提取器
    从对话中提取重要信息
    """

    def __init__(self):
        self._init_patterns()

    def _init_patterns(self):
        """初始化匹配模式"""
        self.name_patterns = [
            r"我叫([\w\s]{1,20})",
            r"我的名字是([\w\s]{1,20})",
            r"大家都叫我([\w\s]{1,20})",
        ]

        self.age_patterns = [
            r"我今年(\d{1,2})岁",
            r"我(\d{1,2})岁",
            r"生日是(\d{1,2})月(\d{1,2})日",
        ]

        self.location_patterns = [
            r"我住在([\w\s]{2,30})",
            r"我在([\w\s]{2,30})",
            r"我来自([\w\s]{2,30})",
        ]

        self.preference_patterns = [
            r"我喜欢([\w\s]{1,30})",
            r"我爱([\w\s]{1,30})",
            r"我讨厌([\w\s]{1,30})",
            r"我不喜欢([\w\s]{1,30})",
            r"我最爱([\w\s]{1,30})",
        ]

        self.birthday_patterns = [
            r"生日是(\d{1,2})月(\d{1,2})日",
            r"我(\d{1,2})月(\d{1,2})日过生日",
            r"明天是我的生日",
            r"今天是我的生日",
        ]

        self.job_patterns = [
            r"我换工作了",
            r"我找到新工作了",
            r"我失业了",
            r"我辞职了",
            r"我在([\w\s]{2,30})工作",
            r"我是([\w\s]{2,20})",
        ]

        self.fact_patterns = [
            r"我有([\w\s]{1,20})",
            r"我养了([\w\s]{1,20})",
            r"我的([\w\s]{1,20})是",
        ]

    def extract_names(self, text: str) -> List[ExtractedInfo]:
        """提取名字"""
        names = []
        for pattern in self.name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                name = match.strip()
                if name and len(name) <= 20:
                    names.append(
                        ExtractedInfo(
                            info_type="name",
                            key="user_name",
                            value=name,
                            source=text[:50],
                            confidence=0.9,
                        )
                    )
        return names

    def extract_ages(self, text: str) -> List[ExtractedInfo]:
        """提取年龄"""
        ages = []
        for pattern in self.age_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) == 2:
                        birthday = f"{match[0]}月{match[1]}日"
                        ages.append(
                            ExtractedInfo(
                                info_type="event",
                                key="birthday",
                                value=birthday,
                                source=text[:50],
                                confidence=0.85,
                            )
                        )
                else:
                    age = match.strip()
                    if age.isdigit() and 1 <= int(age) <= 120:
                        ages.append(
                            ExtractedInfo(
                                info_type="fact",
                                key="age",
                                value=age,
                                source=text[:50],
                                confidence=0.9,
                            )
                        )
        return ages

    def extract_locations(self, text: str) -> List[ExtractedInfo]:
        """提取位置"""
        locations = []
        for pattern in self.location_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                loc = match.strip()
                if loc and len(loc) <= 30:
                    locations.append(
                        ExtractedInfo(
                            info_type="fact",
                            key="location",
                            value=loc,
                            source=text[:50],
                            confidence=0.8,
                        )
                    )
        return locations

    def extract_preferences(self, text: str) -> List[ExtractedInfo]:
        """提取偏好"""
        preferences = []
        for pattern in self.preference_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                pref = match.strip()
                if pref and len(pref) <= 30:
                    pref_type = (
                        "like"
                        if any(keyword in pattern for keyword in ["喜欢", "爱", "最爱"])
                        else "dislike"
                    )
                    preferences.append(
                        ExtractedInfo(
                            info_type="preference",
                            key=pref_type,
                            value=pref,
                            source=text[:50],
                            confidence=0.85,
                        )
                    )
        return preferences

    def extract_facts(self, text: str) -> List[ExtractedInfo]:
        """提取事实信息"""
        facts = []
        for pattern in self.fact_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                fact = match.strip()
                if fact and len(fact) <= 30:
                    facts.append(
                        ExtractedInfo(
                            info_type="fact",
                            key="possession",
                            value=fact,
                            source=text[:50],
                            confidence=0.75,
                        )
                    )
        return facts

    def detect_birthdays(self, text: str) -> List[DetectedEvent]:
        """检测生日事件"""
        events = []
        for pattern in self.birthday_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    desc = f"生日是{match[0]}月{match[1]}日"
                    events.append(
                        DetectedEvent(
                            event_type="birthday",
                            description=desc,
                            date=f"{match[0]}月{match[1]}日",
                            importance=0.9,
                            source=text[:50],
                        )
                    )
                elif "今天" in text or "明天" in text:
                    events.append(
                        DetectedEvent(
                            event_type="birthday",
                            description="生日快到了或今天是生日",
                            importance=0.95,
                            source=text[:50],
                        )
                    )
        return events

    def detect_job_changes(self, text: str) -> List[DetectedEvent]:
        """检测工作变动事件"""
        events = []
        job_keywords = ["换工作", "新工作", "失业", "辞职"]
        for keyword in job_keywords:
            if keyword in text:
                events.append(
                    DetectedEvent(
                        event_type="job_change", description=text, importance=0.85, source=text[:50]
                    )
                )
                break

        for pattern in self.job_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match and isinstance(match, str) and len(match) > 1:
                    events.append(
                        DetectedEvent(
                            event_type="job",
                            description=f"工作信息: {match}",
                            importance=0.7,
                            source=text[:50],
                        )
                    )
        return events

    def extract_all_info(self, text: str) -> List[ExtractedInfo]:
        """提取所有类型的信息"""
        all_info = []
        all_info.extend(self.extract_names(text))
        all_info.extend(self.extract_ages(text))
        all_info.extend(self.extract_locations(text))
        all_info.extend(self.extract_preferences(text))
        all_info.extend(self.extract_facts(text))
        return all_info

    def detect_events(self, text: str) -> List[DetectedEvent]:
        """检测所有事件"""
        events = []
        events.extend(self.detect_birthdays(text))
        events.extend(self.detect_job_changes(text))
        return events

    def generate_summary(self, messages: List[Dict[str, str]]) -> ConversationSummary:
        """
        生成对话摘要

        Args:
            messages: 消息列表，格式为 [{"role": "user"/"assistant", "content": "..."}]

        Returns:
            对话摘要
        """
        user_messages = [m["content"] for m in messages if m["role"] == "user"]

        extracted_info = []
        for msg in user_messages:
            extracted_info.extend(self.extract_all_info(msg))

        detected_events = []
        for msg in user_messages:
            detected_events.extend(self.detect_events(msg))

        key_topics = self._extract_topics(user_messages)

        summary = self._generate_summary_text(messages, extracted_info, detected_events)

        return ConversationSummary(
            summary=summary,
            key_topics=key_topics,
            extracted_info=extracted_info,
            detected_events=detected_events,
            conversation_length=len(messages),
        )

    def _extract_topics(self, user_messages: List[str]) -> List[str]:
        """提取关键词/话题"""
        topics = []
        topic_keywords = ["工作", "生活", "感情", "学习", "家庭", "朋友", "爱好", "健康"]
        all_text = " ".join(user_messages)

        for keyword in topic_keywords:
            if keyword in all_text:
                topics.append(keyword)

        if len(topics) == 0:
            topics.append("日常聊天")

        return topics[:5]

    def _generate_summary_text(
        self,
        messages: List[Dict[str, str]],
        extracted_info: List[ExtractedInfo],
        detected_events: List[DetectedEvent],
    ) -> str:
        """生成摘要文本"""
        parts = []

        if extracted_info:
            info_summary = []
            for info in extracted_info[:5]:
                info_summary.append(f"{info.key}: {info.value}")
            if info_summary:
                parts.append("了解到的信息：" + "；".join(info_summary))

        if detected_events:
            event_summary = []
            for event in detected_events[:3]:
                event_summary.append(f"{event.event_type}: {event.description}")
            if event_summary:
                parts.append("重要事件：" + "；".join(event_summary))

        if len(messages) > 0:
            last_msg = (
                messages[-1]["content"][:50]
                if len(messages[-1]["content"]) > 50
                else messages[-1]["content"]
            )
            parts.append(f"最近的话题：{last_msg}")

        if not parts:
            return "简单的日常对话"

        return "。".join(parts)


_memory_extractor: Optional[MemoryExtractor] = None


def get_memory_extractor() -> MemoryExtractor:
    """获取记忆提取器单例"""
    global _memory_extractor
    if _memory_extractor is None:
        _memory_extractor = MemoryExtractor()
    return _memory_extractor
