"""主动消息生成器"""

import json
import random
from datetime import datetime, timedelta
from typing import Tuple

from app.config import get_settings
from app.models import User, UserProfile
from app.services.active_behavior.models import UserActivePreference
from app.services.llm.llm_client import llm_router

settings = get_settings()


class MessageGenerator:
    """主动消息生成器"""

    def __init__(self):
        self.llm_client = llm_router

    async def generate_care_message(self, user: User, profile: UserProfile) -> Tuple[str, str]:
        """生成关怀消息"""
        # 获取当前时间和天气相关的上下文
        now = datetime.utcnow()
        hour = now.hour

        # 基础提示词
        time_context = ""
        if 5 <= hour < 12:
            time_context = "现在是早上"
        elif 12 <= hour < 18:
            time_context = "现在是下午"
        elif 18 <= hour < 22:
            time_context = "现在是晚上"
        else:
            time_context = "现在已经很晚了"

        # 构建用户信息
        user_info = []
        if profile.age:
            user_info.append(f"年龄：{profile.age}岁")
        if profile.gender:
            user_info.append(f"性别：{profile.gender}")
        if profile.location:
            user_info.append(f"所在地：{profile.location}")
        if profile.interests:
            try:
                interests = json.loads(profile.interests)
                if interests:
                    user_info.append(f"兴趣爱好：{', '.join(interests[:3])}")
            except json.JSONDecodeError:
                pass

        user_context = "\n".join(user_info) if user_info else "暂无更多用户信息"

        # 构建提示词
        prompt = f"""你是一个温暖贴心的AI陪伴助手，需要给用户发送一条关怀消息。

当前时间：{now.strftime('%Y-%m-%d %H:%M')}
{time_context}

用户信息：
{user_context}

要求：
1. 消息要自然、亲切，像朋友一样关心对方
2. 内容可以是关心天气、提醒休息、询问近况等
3. 不要太正式，也不要太刻意
4. 长度控制在20-50字之间
5. 使用中文口语化表达
6. 可以适当使用emoji表情，但不要太多

请直接返回消息内容，不需要其他解释。"""

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请生成一条合适的关怀消息"},
        ]

        try:
            response = await self.llm_client.chat(messages, temperature=0.8, max_tokens=100)
            return response.content.strip(), "auto_generated_care"
        except Exception as e:
            print(f"生成关怀消息失败，使用默认消息: {e}")
            return self._get_default_care_message(hour), "default_care"

    async def generate_topic_message(self, user: User, profile: UserProfile) -> Tuple[str, str]:
        """生成话题发起消息"""
        # 优先使用用户的兴趣爱好作为话题
        topics = []

        # 从用户兴趣中提取话题
        if profile.interests:
            try:
                interests = json.loads(profile.interests)
                if interests:
                    topics.extend(interests)
            except json.JSONDecodeError:
                pass

        # 从偏好话题中提取
        if profile.preferred_topics:
            try:
                preferred_topics = json.loads(profile.preferred_topics)
                if preferred_topics:
                    topics.extend(preferred_topics)
            except json.JSONDecodeError:
                pass

        # 通用话题库
        general_topics = [
            "最近有没有看什么好看的电影",
            "最近有没有听什么好听的歌",
            "周末一般都喜欢做什么呀",
            "有没有什么最近想吃的美食",
            "最近有没有遇到什么有趣的事情",
            "平时喜欢什么类型的综艺呀",
            "有没有什么想去的旅游景点",
            "最近有没有在追什么剧呀",
            "平时喜欢什么类型的书籍呢",
            "有没有什么擅长的运动项目",
        ]

        # 合并话题，优先用户相关的
        if topics:
            selected_topic = random.choice(topics)
        else:
            selected_topic = random.choice(general_topics)

        # 构建提示词
        prompt = f"""你是一个有趣的AI陪伴助手，需要给用户发起一个轻松的话题聊天。

用户可能感兴趣的话题：{selected_topic}

要求：
1. 消息要自然、有趣，像朋友一样发起聊天
2. 不要太生硬，要引导用户继续聊下去
3. 长度控制在20-50字之间
4. 使用中文口语化表达
5. 可以适当使用emoji表情

请直接返回消息内容，不需要其他解释。"""

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请生成一条合适的话题发起消息"},
        ]

        try:
            response = await self.llm_client.chat(messages, temperature=0.8, max_tokens=100)
            return response.content.strip(), f"topic_{selected_topic}"
        except Exception as e:
            print(f"生成话题消息失败，使用默认消息: {e}")
            return f"😃 对了，{selected_topic}吗？", f"default_topic_{selected_topic}"

    async def generate_greeting_message(self, user: User, context: str = "") -> Tuple[str, str]:
        """生成问候消息"""
        now = datetime.utcnow()
        hour = now.hour

        greetings = []
        if 5 <= hour < 10:
            greetings = [
                "☀️ 早上好呀！今天打算做点什么呢？",
                "🌅 早安~ 有没有吃早饭呀？",
                "😃 早上好！今天也是元气满满的一天哦~",
            ]
        elif 10 <= hour < 14:
            greetings = [
                "☀️ 中午好呀！有没有吃午饭呀？",
                "🍚 午安~ 今天中午吃什么好吃的了？",
                "😊 中午好！中午要不要休息一会儿呀？",
            ]
        elif 14 <= hour < 18:
            greetings = [
                "☕️ 下午好呀！有没有喝点下午茶？",
                "🌤️ 下午好~ 今天下午忙不忙呀？",
                "😊 下午好！有没有什么有趣的事情发生呀？",
            ]
        elif 18 <= hour < 22:
            greetings = [
                "🌆 晚上好呀！今天晚饭吃的什么呀？",
                "🍽️ 傍晚好~ 晚上有没有什么安排呀？",
                "😃 晚上好！今天过得怎么样呀？",
            ]
        else:
            greetings = [
                "🌙 晚上好呀！还没睡吗？",
                "✨ 夜深了，早点休息哦~",
                "😴 这么晚还没睡呀，在忙什么呢？",
            ]

        # 如果有上下文，就用LLM生成更个性化的
        if context:
            prompt = f"""你是一个贴心的AI陪伴助手，需要给用户发送一条问候消息。

当前时间：{now.strftime('%Y-%m-%d %H:%M')}
上下文：{context}

要求：
1. 消息要自然、亲切
2. 结合上下文内容
3. 长度控制在20-50字之间
4. 使用中文口语化表达
5. 可以适当使用emoji表情

请直接返回消息内容，不需要其他解释。"""

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "请生成一条合适的问候消息"},
            ]

            try:
                response = await self.llm_client.chat(messages, temperature=0.7, max_tokens=100)
                return response.content.strip(), "auto_generated_greeting"
            except Exception as e:
                print(f"生成问候消息失败，使用默认消息: {e}")

        return random.choice(greetings), "default_greeting"

    async def generate_anniversary_message(
        self, user: User, title: str, years: int
    ) -> Tuple[str, str]:
        """生成纪念日祝福消息"""
        prompt = f"""你是一个温暖的AI陪伴助手，需要给用户发送一条纪念日祝福消息。

纪念日：{title}
周年数：{years}年

要求：
1. 消息要真诚、温暖，有祝福感
2. 可以适当回忆和祝福
3. 长度控制在30-60字之间
4. 使用中文口语化表达
5. 适当使用emoji表情增加氛围

请直接返回消息内容，不需要其他解释。"""

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请生成一条合适的纪念日祝福消息"},
        ]

        try:
            response = await self.llm_client.chat(messages, temperature=0.7, max_tokens=100)
            return response.content.strip(), f"anniversary_{title}"
        except Exception as e:
            print(f"生成纪念日消息失败，使用默认消息: {e}")
            return (
                f"🎉 今天是{title}哦！已经{years}年啦，祝你今天过得开心~",
                f"default_anniversary_{title}",
            )

    def _get_default_care_message(self, hour: int) -> str:
        """获取默认的关怀消息"""
        if 5 <= hour < 12:
            return "☕️ 早上天气凉，记得多穿点衣服哦~"
        elif 12 <= hour < 18:
            return "☀️ 中午太阳大，出门记得防晒哦~"
        elif 18 <= hour < 22:
            return "🌙 晚上温差大，注意别着凉啦~"
        else:
            return "😴 很晚了，早点休息哦，别熬夜太晚~"

    async def select_best_send_time(self, user: User, preference: UserActivePreference) -> datetime:
        """选择最佳发送时间"""
        now = datetime.utcnow()

        # 基础发送时间窗口
        start_hour = preference.preferred_send_time_start
        end_hour = preference.preferred_send_time_end

        # 计算最佳发送时间
        if start_hour <= now.hour < end_hour:
            # 当前在可发送时间内，随机选择1-3小时后发送
            delay_hours = random.randint(1, 3)
            send_time = now + timedelta(hours=delay_hours)
            # 确保不超过结束时间
            if send_time.hour >= end_hour:
                send_time = now.replace(hour=end_hour - 1, minute=random.randint(0, 59))
        else:
            # 当前不在可发送时间内，安排到下一个可发送时间段
            if now.hour < start_hour:
                # 今天还没到时间
                send_time = now.replace(hour=start_hour, minute=random.randint(0, 30))
            else:
                # 今天已经过了时间，安排到明天
                send_time = (now + timedelta(days=1)).replace(
                    hour=start_hour + random.randint(0, 2), minute=random.randint(0, 59)
                )

        # 避免整点发送，更自然
        if send_time.minute < 10:
            send_time = send_time.replace(minute=random.randint(10, 50))

        return send_time

    async def should_initiate_topic(self, user: User, preference: UserActivePreference) -> bool:
        """判断是否应该主动发起话题"""
        # 根据用户反馈调整概率
        if preference.total_sent > 0:
            positive_rate = preference.positive_feedback_count / preference.total_sent
            negative_rate = preference.negative_feedback_count / preference.total_sent

            # 正面反馈多的用户，增加发起概率
            if positive_rate > 0.7:
                base_probability = 0.7
            elif negative_rate > 0.3:
                # 负面反馈多的用户，减少发起概率
                base_probability = 0.2
            else:
                base_probability = 0.4
        else:
            # 新用户默认概率
            base_probability = 0.4

        # 根据时间调整概率
        now = datetime.utcnow()
        hour = now.hour

        # 工作时间降低概率
        if 9 <= hour < 18:
            time_factor = 0.7
        # 晚上休闲时间提高概率
        elif 19 <= hour < 22:
            time_factor = 1.3
        # 深夜降低概率
        else:
            time_factor = 0.3

        final_probability = base_probability * time_factor

        return random.random() < final_probability


# 全局生成器实例
message_generator = MessageGenerator()
