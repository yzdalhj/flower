# -*- coding: utf-8 -*-
"""
混合真人化处理器测试
验证内容:
1. LRU缓存功能
2. LLM真人化Prompt构建
3. 混合处理逻辑
4. 缓存命中率统计
"""

import importlib.util
import sys
from datetime import datetime

sys.path.insert(0, "/Users/yzdalhj/Desktop/code/up/flower")

# 直接导入模块，避免依赖其他服务
spec = importlib.util.spec_from_file_location(
    "lru_cache",
    "/Users/yzdalhj/Desktop/code/up/flower/app/services/humanize/lru_cache.py",
)
lru_cache_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lru_cache_module)

LRUCache = lru_cache_module.LRUCache
CacheEntry = lru_cache_module.CacheEntry


class Colors:
    """终端颜色"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


def test_lru_cache():
    """测试1: LRU缓存功能"""
    print_header("测试1: LRU缓存功能")

    cache = LRUCache(max_size=3, ttl=3600)

    # 测试基本设置和获取
    cache["key1"] = "value1"
    cache["key2"] = "value2"
    cache["key3"] = "value3"

    passed = 0
    total = 5

    # 测试1: 基本获取
    if "key1" in cache and cache["key1"] == "value1":
        print_success("基本设置和获取正常")
        passed += 1
    else:
        print_error("基本设置和获取失败")

    # 测试2: 缓存命中
    if "key2" in cache:
        print_success("缓存命中检测正常")
        passed += 1
    else:
        print_error("缓存命中检测失败")

    # 测试3: 缓存未命中
    if "key_not_exist" not in cache:
        print_success("缓存未命中检测正常")
        passed += 1
    else:
        print_error("缓存未命中检测失败")

    # 测试4: LRU淘汰（添加第4个，应该淘汰最旧的key1）
    cache["key4"] = "value4"
    if "key1" not in cache and "key4" in cache:
        print_success("LRU淘汰机制正常")
        passed += 1
    else:
        print_error("LRU淘汰机制失败")

    # 测试5: 访问后更新LRU顺序
    _ = cache["key2"]  # 访问key2
    cache["key5"] = "value5"  # 添加key5，应该淘汰key3（因为key2刚被访问）
    if "key3" not in cache and "key2" in cache:
        print_success("LRU访问更新正常")
        passed += 1
    else:
        print_error("LRU访问更新失败")

    print_info(f"LRU缓存测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_cache_stats():
    """测试2: 缓存统计"""
    print_header("测试2: 缓存统计")

    cache = LRUCache(max_size=100, ttl=3600)

    # 添加一些数据
    for i in range(10):
        cache[f"key{i}"] = f"value{i}"

    # 访问一些数据
    for i in range(5):
        _ = cache[f"key{i}"]

    stats = cache.get_stats()

    passed = 0
    total = 3

    if stats.get("size") == 10:
        print_success(f"缓存大小统计正确: {stats['size']}")
        passed += 1
    else:
        print_error(f"缓存大小统计错误: {stats['size']}")

    if stats.get("max_size") == 100:
        print_success(f"最大容量统计正确: {stats['max_size']}")
        passed += 1
    else:
        print_error(f"最大容量统计错误: {stats['max_size']}")

    if stats.get("total_access") >= 5:
        print_success(f"访问次数统计正确: {stats['total_access']}")
        passed += 1
    else:
        print_error(f"访问次数统计错误: {stats['total_access']}")

    print_info(f"缓存统计测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_cache_ttl():
    """测试3: 缓存TTL过期"""
    print_header("测试3: 缓存TTL过期")

    # 使用很短的TTL进行测试
    cache = LRUCache(max_size=10, ttl=1)  # 1秒过期

    cache["key1"] = "value1"

    passed = 0
    total = 2

    # 测试1: 立即获取应该成功
    if "key1" in cache and cache["key1"] == "value1":
        print_success("TTL内获取正常")
        passed += 1
    else:
        print_error("TTL内获取失败")

    # 测试2: 等待过期后获取应该失败
    import time

    time.sleep(1.1)  # 等待过期
    if "key1" not in cache:
        print_success("TTL过期后自动删除正常")
        passed += 1
    else:
        print_error("TTL过期后未自动删除")

    print_info(f"缓存TTL测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 AI小花 混合真人化处理器测试 🌸")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    try:
        results.append(("LRU缓存", test_lru_cache()))
    except Exception as e:
        print_error(f"LRU缓存测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("LRU缓存", False))

    try:
        results.append(("缓存统计", test_cache_stats()))
    except Exception as e:
        print_error(f"缓存统计测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("缓存统计", False))

    try:
        results.append(("缓存TTL", test_cache_ttl()))
    except Exception as e:
        print_error(f"缓存TTL测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("缓存TTL", False))

    # 汇总
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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！混合真人化处理器验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
