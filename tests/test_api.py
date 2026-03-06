"""
API 接口验证测试

验证内容:
1. 根路径访问
2. 健康检查接口
3. 对话历史查询

注意: 此测试直接导入实际实现模块进行验证
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============ 导入实际实现 ============

from httpx import AsyncClient  # noqa: E402

from app.main import app  # noqa: E402

# ============ 颜色输出 ============


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


# ============ 测试函数 ============


def test_root():
    """测试1: 根路径访问 - 使用实际实现"""
    print_header("测试1: 根路径访问 - 实际实现")

    async def run_test():
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/")

        checks = []

        # 检查状态码
        if response.status_code == 200:
            print_success(f"状态码正确: {response.status_code}")
            checks.append(True)
        else:
            print_error(f"状态码错误: {response.status_code}")
            checks.append(False)

        data = response.json()

        # 检查应用名称
        if data.get("name") == "AI小花":
            print_success(f"应用名称正确: {data.get('name')}")
            checks.append(True)
        else:
            print_error(f"应用名称错误: {data.get('name')}")
            checks.append(False)

        # 检查运行状态
        if data.get("status") == "running":
            print_success(f"运行状态正确: {data.get('status')}")
            checks.append(True)
        else:
            print_error(f"运行状态错误: {data.get('status')}")
            checks.append(False)

        print_info(f"响应数据: {data}")
        print_info(f"通过率: {sum(checks)}/{len(checks)}")
        return sum(checks) == len(checks)

    return asyncio.run(run_test())


def test_health_check():
    """测试2: 健康检查接口 - 使用实际实现"""
    print_header("测试2: 健康检查接口 - 实际实现")

    async def run_test():
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/health")

        checks = []

        # 检查状态码
        if response.status_code == 200:
            print_success(f"状态码正确: {response.status_code}")
            checks.append(True)
        else:
            print_error(f"状态码错误: {response.status_code}")
            checks.append(False)

        data = response.json()

        # 检查健康状态
        if data.get("status") == "healthy":
            print_success(f"健康状态正确: {data.get('status')}")
            checks.append(True)
        else:
            print_error(f"健康状态错误: {data.get('status')}")
            checks.append(False)

        # 检查是否包含时间戳
        if "timestamp" in data:
            print_success(f"包含时间戳: {data.get('timestamp')}")
            checks.append(True)
        else:
            print_info("未包含时间戳（可选）")
            checks.append(True)

        print_info(f"响应数据: {data}")
        print_info(f"通过率: {sum(checks)}/{len(checks)}")
        return sum(checks) >= len(checks) * 0.8

    return asyncio.run(run_test())


def test_chat_history_not_found():
    """测试3: 对话历史查询（不存在的会话） - 使用实际实现"""
    print_header("测试3: 对话历史查询（不存在的会话） - 实际实现")

    async def run_test():
        try:
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/chat/history/nonexistent_id")

            checks = []

            # 检查状态码
            if response.status_code == 200:
                print_success(f"状态码正确: {response.status_code}")
                checks.append(True)
            else:
                print_error(f"状态码错误: {response.status_code}")
                checks.append(False)

            data = response.json()

            # 检查会话ID
            if data.get("conversation_id") == "nonexistent_id":
                print_success(f"会话ID正确: {data.get('conversation_id')}")
                checks.append(True)
            else:
                print_error(f"会话ID错误: {data.get('conversation_id')}")
                checks.append(False)

            # 检查消息列表为空
            if data.get("messages") == []:
                print_success("消息列表为空（符合预期）")
                checks.append(True)
            else:
                print_error(f"消息列表不为空: {data.get('messages')}")
                checks.append(False)

            print_info(f"响应数据: {data}")
            print_info(f"通过率: {sum(checks)}/{len(checks)}")
            return sum(checks) == len(checks)

        except Exception as e:
            print_error(f"测试执行失败: {e}")
            print_info("提示: 此测试需要数据库表已创建")
            return False

    return asyncio.run(run_test())


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 AI小花 API 接口验证测试 🌸")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    try:
        results.append(("根路径访问", test_root()))
    except Exception as e:
        print_error(f"根路径访问测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("根路径访问", False))

    try:
        results.append(("健康检查接口", test_health_check()))
    except Exception as e:
        print_error(f"健康检查接口测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("健康检查接口", False))

    try:
        results.append(("对话历史查询", test_chat_history_not_found()))
    except Exception as e:
        print_error(f"对话历史查询测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("对话历史查询", False))

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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！API 接口验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
