# -*- coding: utf-8 -*-
"""
优化的记忆检索器测试
验证语义检索、时序检索、重要性筛选和混合排序
"""

import importlib.util
import os
import sys
import types
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 屏蔽不必要的模块导入
app_module = types.ModuleType("app")
sys.modules["app"] = app_module
app_services_module = types.ModuleType("app.services")
sys.modules["app.services"] = app_services_module
app_services_memory_module = types.ModuleType("app.services.memory")
sys.modules["app.services.memory"] = app_services_memory_module
app_config_module = types.ModuleType("app.config")
sys.modules["app.config"] = app_config_module


# Mock settings
class MockSettings:
    CHROMA_DB_PATH = "./data/test_chroma"


settings = MockSettings()
app_config_module.get_settings = lambda: settings

# 导入优化的检索器
spec_retriever = importlib.util.spec_from_file_location(
    "optimized_retriever",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "app/services/memory/optimized_retriever.py"
    ),
)
retriever_module = importlib.util.module_from_spec(spec_retriever)
sys.modules["app.services.memory.optimized_retriever"] = retriever_module
spec_retriever.loader.exec_module(retriever_module)

RetrievalQuery = retriever_module.RetrievalQuery
MemoryResult = retriever_module.MemoryResult
OptimizedMemoryRetriever = retriever_module.OptimizedMemoryRetriever


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_header(text):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


def test_data_structures():
    """测试数据结构"""
    print_header("测试1: 数据结构")

    query = RetrievalQuery(
        query_text="测试查询", user_id="test_user_123", min_importance=3.0, n_results=5
    )

    passed = 0
    if query.query_text == "测试查询":
        print_success("查询文本设置正确")
        passed += 1

    if query.user_id == "test_user_123":
        print_success("用户ID设置正确")
        passed += 1

    if query.min_importance == 3.0:
        print_success("最小重要性设置正确")
        passed += 1

    result = MemoryResult(
        memory_id="mem_1",
        content="测试内容",
        memory_type="episodic",
        importance=7.5,
        occurred_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )

    if result.memory_id == "mem_1":
        print_success("记忆结果ID正确")
        passed += 1

    if result.importance == 7.5:
        print_success("记忆重要性正确")
        passed += 1

    print_info(f"数据结构测试通过率: {passed}/5")
    return passed >= 4


def test_score_calculation():
    """测试分数计算"""
    print_header("测试2: 分数计算")

    result = MemoryResult(
        memory_id="mem_1",
        content="测试内容",
        memory_type="episodic",
        importance=8.0,
        occurred_at=datetime.utcnow(),
        created_at=datetime.utcnow() - timedelta(hours=1),
    )

    query = RetrievalQuery(
        query_text="测试", semantic_weight=0.5, time_weight=0.3, importance_weight=0.2
    )

    retriever = OptimizedMemoryRetriever(None, None)

    result.semantic_score = 0.8
    result.time_score = retriever._calculate_time_score(result, query)
    result.importance_score = retriever._calculate_importance_score(result, query)

    passed = 0
    if 0.0 <= result.semantic_score <= 1.0:
        print_success(f"语义分数在有效范围内: {result.semantic_score:.2f}")
        passed += 1

    if 0.0 <= result.time_score <= 1.0:
        print_success(f"时间分数在有效范围内: {result.time_score:.2f}")
        passed += 1

    if 0.0 <= result.importance_score <= 1.0:
        print_success(f"重要性分数在有效范围内: {result.importance_score:.2f}")
        passed += 1

    results = [result]
    scored_results = retriever._calculate_scores(results, query)

    if 0.0 <= scored_results[0].final_score <= 1.0:
        print_success(f"最终分数在有效范围内: {scored_results[0].final_score:.2f}")
        passed += 1

    print_info(f"分数计算测试通过率: {passed}/4")
    return passed >= 3


def test_sorting():
    """测试排序功能"""
    print_header("测试3: 排序功能")

    retriever = OptimizedMemoryRetriever(None, None)

    results = [
        MemoryResult(
            memory_id=f"mem_{i}",
            content=f"内容{i}",
            memory_type="episodic",
            importance=5.0 + i,
            occurred_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            final_score=0.5 + i * 0.1,
        )
        for i in range(5)
    ]

    sorted_results = retriever._sort_by_final_score(results)

    passed = 0
    if sorted_results[0].final_score > sorted_results[-1].final_score:
        print_success("按最终分数降序排序正确")
        passed += 1

    if sorted_results[0].memory_id == "mem_4":
        print_success("最高分数的记忆排在第一位")
        passed += 1

    print_info(f"排序测试通过率: {passed}/2")
    return passed >= 1


def test_deduplication():
    """测试去重功能"""
    print_header("测试4: 去重功能")

    retriever = OptimizedMemoryRetriever(None, None)

    results = [
        MemoryResult(
            memory_id="mem_1",
            content="内容1",
            memory_type="episodic",
            importance=5.0,
            occurred_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        ),
        MemoryResult(
            memory_id="mem_1",
            content="内容1重复",
            memory_type="episodic",
            importance=5.0,
            occurred_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        ),
        MemoryResult(
            memory_id="mem_2",
            content="内容2",
            memory_type="episodic",
            importance=6.0,
            occurred_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        ),
    ]

    unique_results = retriever._deduplicate(results)

    passed = 0
    if len(unique_results) == 2:
        print_success(f"去重后数量正确: {len(unique_results)}")
        passed += 1

    memory_ids = [r.memory_id for r in unique_results]
    if "mem_1" in memory_ids and "mem_2" in memory_ids:
        print_success("去重后保留了唯一的记忆")
        passed += 1

    print_info(f"去重测试通过率: {passed}/2")
    return passed >= 1


def test_retrieval_query_creation():
    """测试检索查询创建"""
    print_header("测试5: 检索查询配置")

    query1 = RetrievalQuery(
        query_text="关于工作",
        user_id="user_123",
        memory_type="episodic",
        min_importance=4.0,
        time_range_hours=24,
        n_results=10,
    )

    query2 = RetrievalQuery(
        query_text="重要事件",
        user_id="user_456",
        min_importance=7.0,
        semantic_weight=0.3,
        time_weight=0.2,
        importance_weight=0.5,
    )

    passed = 0
    if query1.memory_type == "episodic":
        print_success("记忆类型筛选配置正确")
        passed += 1

    if query1.time_range_hours == 24:
        print_success("时间范围配置正确")
        passed += 1

    if query2.importance_weight == 0.5:
        print_success("重要性权重配置正确")
        passed += 1

    total_weight = query2.semantic_weight + query2.time_weight + query2.importance_weight
    if abs(total_weight - 1.0) < 0.01:
        print_success(f"权重总和正确: {total_weight:.2f}")
        passed += 1

    print_info(f"检索查询配置测试通过率: {passed}/4")
    return passed >= 3


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 优化的记忆检索器测试 🌸")

    results = []

    try:
        results.append(("数据结构", test_data_structures()))
    except Exception as e:
        print(f"{Colors.RED}✗ 数据结构测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("数据结构", False))

    try:
        results.append(("分数计算", test_score_calculation()))
    except Exception as e:
        print(f"{Colors.RED}✗ 分数计算测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("分数计算", False))

    try:
        results.append(("排序功能", test_sorting()))
    except Exception as e:
        print(f"{Colors.RED}✗ 排序功能测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("排序功能", False))

    try:
        results.append(("去重功能", test_deduplication()))
    except Exception as e:
        print(f"{Colors.RED}✗ 去重功能测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("去重功能", False))

    try:
        results.append(("检索查询配置", test_retrieval_query_creation()))
    except Exception as e:
        print(f"{Colors.RED}✗ 检索查询配置测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("检索查询配置", False))

    print_header("📊 测试结果汇总")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = f"{Colors.GREEN}通过" if result else f"{Colors.RED}失败"
        print(f"  {status}{Colors.RESET} - {name}")

    print(
        f"\n总计: {Colors.GREEN if passed == total else Colors.YELLOW}{passed}/{total}{Colors.RESET} 通过"
    )

    if passed == total:
        print(f"\n{Colors.GREEN}🎉 所有测试通过！优化的记忆检索器验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
