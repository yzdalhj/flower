"""
提示优化服务
支持 Few-shot 示例管理、A/B 测试框架和效果追踪
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class PromptVariant(str, Enum):
    """提示变体标识"""

    A = "A"
    B = "B"
    CONTROL = "control"


@dataclass
class FewShotExample:
    """Few-shot 示例"""

    id: str
    category: str  # 示例类别（如：幽默回复、共情回复、吐槽回复）
    user_input: str
    ai_response: str
    context: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    quality_score: float = 1.0  # 质量评分 0-1
    usage_count: int = 0
    success_rate: float = 0.0  # 使用后的成功率
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "category": self.category,
            "user_input": self.user_input,
            "ai_response": self.ai_response,
            "context": self.context,
            "tags": self.tags,
            "quality_score": self.quality_score,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FewShotExample":
        """从字典创建"""
        data = data.copy()
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class PromptTemplate:
    """提示模板"""

    id: str
    name: str
    variant: PromptVariant
    template: str
    description: str = ""
    few_shot_categories: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "variant": self.variant.value,
            "template": self.template,
            "description": self.description,
            "few_shot_categories": self.few_shot_categories,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """从字典创建"""
        data = data.copy()
        if "variant" in data and isinstance(data["variant"], str):
            data["variant"] = PromptVariant(data["variant"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class ABTestResult:
    """A/B 测试结果"""

    id: str
    test_name: str
    variant: PromptVariant
    user_id: str
    user_message: str
    ai_response: str
    user_satisfaction: Optional[float] = None  # 0-1
    response_time: Optional[float] = None  # 秒
    conversation_length: int = 0
    emotional_resonance: Optional[float] = None  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "test_name": self.test_name,
            "variant": self.variant.value,
            "user_id": self.user_id,
            "user_message": self.user_message,
            "ai_response": self.ai_response,
            "user_satisfaction": self.user_satisfaction,
            "response_time": self.response_time,
            "conversation_length": self.conversation_length,
            "emotional_resonance": self.emotional_resonance,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ABTestResult":
        """从字典创建"""
        data = data.copy()
        if "variant" in data and isinstance(data["variant"], str):
            data["variant"] = PromptVariant(data["variant"])
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class ABTestStats:
    """A/B 测试统计"""

    test_name: str
    variant: PromptVariant
    sample_count: int
    avg_satisfaction: float
    avg_response_time: float
    avg_conversation_length: float
    avg_emotional_resonance: float
    success_rate: float  # 满意度 >= 0.7 的比例

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test_name": self.test_name,
            "variant": self.variant.value,
            "sample_count": self.sample_count,
            "avg_satisfaction": self.avg_satisfaction,
            "avg_response_time": self.avg_response_time,
            "avg_conversation_length": self.avg_conversation_length,
            "avg_emotional_resonance": self.avg_emotional_resonance,
            "success_rate": self.success_rate,
        }


class FewShotManager:
    """Few-shot 示例管理器"""

    def __init__(self, storage_dir: str = "./data/few_shot"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.examples: Dict[str, List[FewShotExample]] = {}
        self._load_examples()

    def _load_examples(self):
        """从文件加载示例"""
        examples_file = self.storage_dir / "examples.json"
        if examples_file.exists():
            with open(examples_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for category, examples_data in data.items():
                    self.examples[category] = [FewShotExample.from_dict(ex) for ex in examples_data]

    def _save_examples(self):
        """保存示例到文件"""
        examples_file = self.storage_dir / "examples.json"
        data = {
            category: [ex.to_dict() for ex in examples]
            for category, examples in self.examples.items()
        }
        with open(examples_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_example(
        self,
        category: str,
        user_input: str,
        ai_response: str,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None,
        quality_score: float = 1.0,
    ) -> FewShotExample:
        """添加 Few-shot 示例"""
        example = FewShotExample(
            id=str(uuid.uuid4()),
            category=category,
            user_input=user_input,
            ai_response=ai_response,
            context=context,
            tags=tags or [],
            quality_score=quality_score,
        )

        if category not in self.examples:
            self.examples[category] = []

        self.examples[category].append(example)
        self._save_examples()

        return example

    def get_examples(
        self, category: str, n: int = 3, min_quality: float = 0.7, tags: Optional[List[str]] = None
    ) -> List[FewShotExample]:
        """
        获取指定类别的示例

        Args:
            category: 示例类别
            n: 返回数量
            min_quality: 最低质量分数
            tags: 标签过滤

        Returns:
            示例列表
        """
        if category not in self.examples:
            return []

        # 过滤
        filtered = [ex for ex in self.examples[category] if ex.quality_score >= min_quality]

        # 标签过滤
        if tags:
            filtered = [ex for ex in filtered if any(tag in ex.tags for tag in tags)]

        # 按质量和成功率排序
        filtered.sort(key=lambda x: (x.quality_score * 0.5 + x.success_rate * 0.5), reverse=True)

        return filtered[:n]

    def update_example_stats(self, example_id: str, success: bool):
        """更新示例统计"""
        for category in self.examples:
            for example in self.examples[category]:
                if example.id == example_id:
                    example.usage_count += 1
                    # 更新成功率（指数移动平均）
                    alpha = 0.3
                    example.success_rate = (
                        alpha * (1.0 if success else 0.0) + (1 - alpha) * example.success_rate
                    )
                    self._save_examples()
                    return

    def format_examples_for_prompt(self, examples: List[FewShotExample]) -> str:
        """格式化示例用于 Prompt"""
        if not examples:
            return ""

        formatted = "\n【参考示例】\n"
        for i, ex in enumerate(examples, 1):
            formatted += f"\n示例 {i}:\n"
            if ex.context:
                formatted += f"场景: {ex.context}\n"
            formatted += f"用户: {ex.user_input}\n"
            formatted += f"小花: {ex.ai_response}\n"

        return formatted

    def get_all_categories(self) -> List[str]:
        """获取所有类别"""
        return list(self.examples.keys())

    def get_category_stats(self, category: str) -> Dict[str, Any]:
        """获取类别统计"""
        if category not in self.examples:
            return {}

        examples = self.examples[category]
        if not examples:
            return {}

        return {
            "category": category,
            "total_count": len(examples),
            "avg_quality": sum(ex.quality_score for ex in examples) / len(examples),
            "avg_success_rate": sum(ex.success_rate for ex in examples) / len(examples),
            "total_usage": sum(ex.usage_count for ex in examples),
        }


class ABTestManager:
    """A/B 测试管理器"""

    def __init__(self, storage_dir: str = "./data/ab_tests"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.templates: Dict[str, Dict[PromptVariant, PromptTemplate]] = {}
        self.results: Dict[str, List[ABTestResult]] = {}
        self.user_assignments: Dict[str, Dict[str, PromptVariant]] = {}
        self._load_data()

    def _load_data(self):
        """加载数据"""
        # 加载模板
        templates_file = self.storage_dir / "templates.json"
        if templates_file.exists():
            with open(templates_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for test_name, variants_data in data.items():
                    self.templates[test_name] = {
                        PromptVariant(variant): PromptTemplate.from_dict(template_data)
                        for variant, template_data in variants_data.items()
                    }

        # 加载结果
        results_file = self.storage_dir / "results.json"
        if results_file.exists():
            with open(results_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for test_name, results_data in data.items():
                    self.results[test_name] = [ABTestResult.from_dict(r) for r in results_data]

        # 加载用户分配
        assignments_file = self.storage_dir / "assignments.json"
        if assignments_file.exists():
            with open(assignments_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for user_id, tests in data.items():
                    self.user_assignments[user_id] = {
                        test_name: PromptVariant(variant) for test_name, variant in tests.items()
                    }

    def _save_templates(self):
        """保存模板"""
        templates_file = self.storage_dir / "templates.json"
        data = {
            test_name: {variant.value: template.to_dict() for variant, template in variants.items()}
            for test_name, variants in self.templates.items()
        }
        with open(templates_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_results(self):
        """保存结果"""
        results_file = self.storage_dir / "results.json"
        data = {
            test_name: [r.to_dict() for r in results] for test_name, results in self.results.items()
        }
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_assignments(self):
        """保存用户分配"""
        assignments_file = self.storage_dir / "assignments.json"
        data = {
            user_id: {test_name: variant.value for test_name, variant in tests.items()}
            for user_id, tests in self.user_assignments.items()
        }
        with open(assignments_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_test(
        self,
        test_name: str,
        template_a: PromptTemplate,
        template_b: PromptTemplate,
        control_template: Optional[PromptTemplate] = None,
    ):
        """创建 A/B 测试"""
        self.templates[test_name] = {PromptVariant.A: template_a, PromptVariant.B: template_b}

        if control_template:
            self.templates[test_name][PromptVariant.CONTROL] = control_template

        self.results[test_name] = []
        self._save_templates()

    def assign_variant(
        self, test_name: str, user_id: str, variant: Optional[PromptVariant] = None
    ) -> PromptVariant:
        """
        为用户分配变体

        Args:
            test_name: 测试名称
            user_id: 用户ID
            variant: 指定变体（None则随机分配）

        Returns:
            分配的变体
        """
        if test_name not in self.templates:
            raise ValueError(f"Test {test_name} not found")

        # 检查是否已分配
        if user_id in self.user_assignments:
            if test_name in self.user_assignments[user_id]:
                return self.user_assignments[user_id][test_name]

        # 分配新变体
        if variant is None:
            # 随机分配（50/50）
            import random

            available_variants = list(self.templates[test_name].keys())
            variant = random.choice(available_variants)

        if user_id not in self.user_assignments:
            self.user_assignments[user_id] = {}

        self.user_assignments[user_id][test_name] = variant
        self._save_assignments()

        return variant

    def get_template(self, test_name: str, user_id: str) -> Optional[PromptTemplate]:
        """获取用户对应的模板"""
        if test_name not in self.templates:
            return None

        variant = self.assign_variant(test_name, user_id)
        return self.templates[test_name].get(variant)

    def record_result(
        self,
        test_name: str,
        variant: PromptVariant,
        user_id: str,
        user_message: str,
        ai_response: str,
        user_satisfaction: Optional[float] = None,
        response_time: Optional[float] = None,
        conversation_length: int = 0,
        emotional_resonance: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ABTestResult:
        """记录测试结果"""
        result = ABTestResult(
            id=str(uuid.uuid4()),
            test_name=test_name,
            variant=variant,
            user_id=user_id,
            user_message=user_message,
            ai_response=ai_response,
            user_satisfaction=user_satisfaction,
            response_time=response_time,
            conversation_length=conversation_length,
            emotional_resonance=emotional_resonance,
            metadata=metadata or {},
        )

        if test_name not in self.results:
            self.results[test_name] = []

        self.results[test_name].append(result)
        self._save_results()

        return result

    def get_stats(self, test_name: str, min_samples: int = 10) -> Dict[PromptVariant, ABTestStats]:
        """
        获取测试统计

        Args:
            test_name: 测试名称
            min_samples: 最小样本数

        Returns:
            各变体的统计数据
        """
        if test_name not in self.results:
            return {}

        results = self.results[test_name]
        stats_by_variant: Dict[PromptVariant, ABTestStats] = {}

        for variant in PromptVariant:
            variant_results = [r for r in results if r.variant == variant]

            if len(variant_results) < min_samples:
                continue

            # 计算统计
            satisfactions = [
                r.user_satisfaction for r in variant_results if r.user_satisfaction is not None
            ]
            response_times = [
                r.response_time for r in variant_results if r.response_time is not None
            ]
            resonances = [
                r.emotional_resonance for r in variant_results if r.emotional_resonance is not None
            ]

            stats = ABTestStats(
                test_name=test_name,
                variant=variant,
                sample_count=len(variant_results),
                avg_satisfaction=sum(satisfactions) / len(satisfactions) if satisfactions else 0.0,
                avg_response_time=(
                    sum(response_times) / len(response_times) if response_times else 0.0
                ),
                avg_conversation_length=sum(r.conversation_length for r in variant_results)
                / len(variant_results),
                avg_emotional_resonance=sum(resonances) / len(resonances) if resonances else 0.0,
                success_rate=(
                    sum(1 for s in satisfactions if s >= 0.7) / len(satisfactions)
                    if satisfactions
                    else 0.0
                ),
            )

            stats_by_variant[variant] = stats

        return stats_by_variant

    def compare_variants(
        self,
        test_name: str,
        variant_a: PromptVariant,
        variant_b: PromptVariant,
        min_samples: int = 10,
    ) -> Dict[str, Any]:
        """
        比较两个变体

        Returns:
            比较结果，包括差异和显著性
        """
        stats = self.get_stats(test_name, min_samples)

        if variant_a not in stats or variant_b not in stats:
            return {"error": "Insufficient samples for comparison"}

        stats_a = stats[variant_a]
        stats_b = stats[variant_b]

        # 计算差异
        satisfaction_diff = stats_b.avg_satisfaction - stats_a.avg_satisfaction
        success_rate_diff = stats_b.success_rate - stats_a.success_rate
        response_time_diff = stats_b.avg_response_time - stats_a.avg_response_time

        # 判断胜者
        winner = None
        if abs(satisfaction_diff) > 0.05:  # 5% 差异阈值
            winner = variant_b if satisfaction_diff > 0 else variant_a

        return {
            "test_name": test_name,
            "variant_a": variant_a.value,
            "variant_b": variant_b.value,
            "stats_a": stats_a.to_dict(),
            "stats_b": stats_b.to_dict(),
            "differences": {
                "satisfaction": satisfaction_diff,
                "success_rate": success_rate_diff,
                "response_time": response_time_diff,
            },
            "winner": winner.value if winner else "tie",
            "confidence": (
                "high"
                if abs(satisfaction_diff) > 0.1
                else "medium" if abs(satisfaction_diff) > 0.05 else "low"
            ),
        }

    def get_all_tests(self) -> List[str]:
        """获取所有测试名称"""
        return list(self.templates.keys())


class PromptOptimizer:
    """提示优化服务 - 整合 Few-shot 和 A/B 测试"""

    def __init__(
        self,
        few_shot_manager: Optional[FewShotManager] = None,
        ab_test_manager: Optional[ABTestManager] = None,
    ):
        self.few_shot_manager = few_shot_manager or FewShotManager()
        self.ab_test_manager = ab_test_manager or ABTestManager()

    def enhance_prompt_with_examples(
        self,
        base_prompt: str,
        categories: List[str],
        n_per_category: int = 2,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        使用 Few-shot 示例增强提示

        Args:
            base_prompt: 基础提示
            categories: 示例类别列表
            n_per_category: 每个类别的示例数
            tags: 标签过滤

        Returns:
            增强后的提示
        """
        all_examples = []

        for category in categories:
            examples = self.few_shot_manager.get_examples(
                category=category, n=n_per_category, tags=tags
            )
            all_examples.extend(examples)

        if not all_examples:
            return base_prompt

        examples_text = self.few_shot_manager.format_examples_for_prompt(all_examples)

        return base_prompt + "\n" + examples_text

    def get_optimized_template(self, test_name: str, user_id: str) -> Optional[PromptTemplate]:
        """获取优化后的模板（通过 A/B 测试）"""
        return self.ab_test_manager.get_template(test_name, user_id)

    def track_prompt_effectiveness(
        self,
        test_name: str,
        variant: PromptVariant,
        user_id: str,
        user_message: str,
        ai_response: str,
        user_satisfaction: float,
        response_time: float,
        conversation_length: int,
        emotional_resonance: float,
        used_examples: Optional[List[str]] = None,
    ):
        """
        追踪提示效果

        Args:
            test_name: 测试名称
            variant: 变体
            user_id: 用户ID
            user_message: 用户消息
            ai_response: AI回复
            user_satisfaction: 用户满意度
            response_time: 响应时间
            conversation_length: 对话长度
            emotional_resonance: 情感共鸣度
            used_examples: 使用的示例ID列表
        """
        # 记录 A/B 测试结果
        self.ab_test_manager.record_result(
            test_name=test_name,
            variant=variant,
            user_id=user_id,
            user_message=user_message,
            ai_response=ai_response,
            user_satisfaction=user_satisfaction,
            response_time=response_time,
            conversation_length=conversation_length,
            emotional_resonance=emotional_resonance,
            metadata={"used_examples": used_examples or []},
        )

        # 更新 Few-shot 示例统计
        if used_examples:
            success = user_satisfaction >= 0.7
            for example_id in used_examples:
                self.few_shot_manager.update_example_stats(example_id, success)

    def get_optimization_report(self, test_name: str) -> Dict[str, Any]:
        """获取优化报告"""
        stats = self.ab_test_manager.get_stats(test_name)

        if not stats:
            return {"error": "No data available"}

        # 找出最佳变体
        best_variant = max(stats.items(), key=lambda x: x[1].avg_satisfaction)

        return {
            "test_name": test_name,
            "best_variant": best_variant[0].value,
            "best_stats": best_variant[1].to_dict(),
            "all_stats": {variant.value: stat.to_dict() for variant, stat in stats.items()},
            "recommendation": self._generate_recommendation(stats),
        }

    def _generate_recommendation(self, stats: Dict[PromptVariant, ABTestStats]) -> str:
        """生成优化建议"""
        if len(stats) < 2:
            return "需要更多数据进行比较"

        sorted_variants = sorted(stats.items(), key=lambda x: x[1].avg_satisfaction, reverse=True)

        best = sorted_variants[0]
        second = sorted_variants[1]

        diff = best[1].avg_satisfaction - second[1].avg_satisfaction

        if diff > 0.1:
            return f"强烈推荐使用变体 {best[0].value}，满意度显著更高（+{diff:.1%}）"
        elif diff > 0.05:
            return f"推荐使用变体 {best[0].value}，满意度略高（+{diff:.1%}）"
        else:
            return f"两个变体效果相近，可继续测试或选择 {best[0].value}"


# 全局实例
_prompt_optimizer: Optional[PromptOptimizer] = None


def get_prompt_optimizer() -> PromptOptimizer:
    """获取提示优化器单例"""
    global _prompt_optimizer
    if _prompt_optimizer is None:
        _prompt_optimizer = PromptOptimizer()
    return _prompt_optimizer
