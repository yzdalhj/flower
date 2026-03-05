#!/usr/bin/env python3
"""
环境验证脚本
检查所有依赖和配置是否正确
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要 Python 3.10+")
        return False


def check_dependencies():
    """检查依赖包"""
    print("\n🔍 检查依赖包...")

    required = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "pydantic_settings",
        "chromadb",
        "openai",
        "aiosqlite",
        "pytest",
        "pytest_asyncio",
        "httpx",
    ]

    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (未安装)")
            missing.append(package)

    return len(missing) == 0


def check_project_structure():
    """检查项目结构"""
    print("\n🔍 检查项目结构...")

    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/config.py",
        "app/core/__init__.py",
        "app/core/database.py",
        "app/models/__init__.py",
        "app/models/base.py",
        "app/models/user.py",
        "app/models/account.py",
        "app/models/conversation.py",
        "app/models/memory.py",
        "app/services/__init__.py",
        "app/services/memory_store.py",
        "app/services/vector_store.py",
        "app/services/llm_client.py",
        "app/services/dialogue.py",
        "app/api/__init__.py",
        "app/api/chat.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_memory.py",
        "tests/test_api.py",
    ]

    all_exist = True
    for file in required_files:
        path = project_root / file
        if path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (缺失)")
            all_exist = False

    return all_exist


def check_database():
    """检查数据库配置"""
    print("\n🔍 检查数据库配置...")

    try:
        from app.config import get_settings

        settings = get_settings()
        print(f"   ✅ 数据库URL: {settings.DATABASE_URL}")
        print(f"   ✅ 向量数据库路径: {settings.CHROMA_DB_PATH}")
        return True
    except Exception as e:
        print(f"   ❌ 配置加载失败: {e}")
        return False


def check_models():
    """检查模型定义"""
    print("\n🔍 检查数据模型...")

    try:
        # 一次性导入所有模型
        from app.models import Account, Conversation, Memory, Message, User, WorkingMemory

        models = [Account, User, Conversation, Message, Memory, WorkingMemory]
        for model in models:
            print(f"   ✅ {model.__name__}")

        return True
    except Exception as e:
        print(f"   ❌ 模型加载失败: {e}")
        return False


def check_services():
    """检查服务"""
    print("\n🔍 检查服务...")

    try:
        from app.services import (
            DialogueProcessor,
            EmbeddingService,
            LLMRouter,
            MemoryStore,
            VectorStore,
        )

        services = [
            MemoryStore,
            VectorStore,
            EmbeddingService,
            LLMRouter,
            DialogueProcessor,
        ]
        for service in services:
            print(f"   ✅ {service.__name__}")

        return True
    except Exception as e:
        print(f"   ❌ 服务加载失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🌸 AI小花 环境验证")
    print("=" * 60)

    checks = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("项目结构", check_project_structure),
        ("数据库配置", check_database),
        ("数据模型", check_models),
        ("服务", check_services),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ 检查失败: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("📊 验证结果")
    print("=" * 60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有检查通过！环境配置正确。")
        print("\n可以运行以下命令启动应用:")
        print("  uvicorn app.main:app --reload")
        print("\n或运行测试:")
        print("  pytest tests/ -v")
    else:
        print("⚠️ 部分检查未通过，请修复上述问题。")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
