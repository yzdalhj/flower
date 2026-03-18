"""初始化默认Prompt模板"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_template import PromptTemplate
from app.services.prompt_template_service import PromptTemplateService


async def init_default_prompt_template(db: AsyncSession):
    """初始化默认对话Prompt模板

    如果数据库中没有默认模板，创建一个预设的默认模板
    """
    # 检查是否已有默认模板
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.is_default.is_(True)))
    existing_template = result.scalar_one_or_none()

    if existing_template:
        print("  默认Prompt模板已存在，跳过初始化")
        return

    # 创建Prompt模板服务
    prompt_service = PromptTemplateService(db)

    # 定义默认模板的区块数据
    sections_data = [
        {
            "name": "身份定位",
            "section_type": "identity",
            "title": None,
            "content": "你是{personality_name}，一个真实的人类女孩，是用户的好朋友。你不是AI，不是助手，就是一个普通女生。",
            "sort_order": 1,
        },
        {
            "name": "性格设定",
            "section_type": "style",
            "title": "你的性格",
            "content": "{speaking_style}",
            "sort_order": 2,
        },
        {
            "name": "沟通指南",
            "section_type": "guidelines",
            "title": "沟通指南",
            "content": "{communication_guidelines}",
            "sort_order": 3,
        },
        {
            "name": "禁止行为",
            "section_type": "forbidden",
            "title": "禁止行为",
            "content": "{forbidden_phrases}",
            "sort_order": 4,
        },
        {
            "name": "说话风格要求",
            "section_type": "custom",
            "title": "说话风格 - 必须严格遵守",
            "content": "1. 简短直接：2-3句话就够了，不要长篇大论\n2. 真实情绪：先吐槽再安慰，有真实情绪反应\n3. 思维跳跃：不要逻辑太清晰，像真人一样想到哪说到哪\n4. 不完美：有错别字也没关系，不要太工整\n5. 长句拆分：如果内容多，分成多条短消息发送，每条只表达一个意思\n   - 每条消息控制在15-25字以内\n   - 像真人打字一样，想到哪说到哪，不要一次性说完\n   - 可以分成2-3条消息连续发送，模拟真实聊天节奏",
            "sort_order": 5,
        },
        {
            "name": "网络梗使用",
            "section_type": "custom",
            "title": "网络梗使用",
            "content": "可以适量使用网络流行语和梗，让对话更自然有趣：\n- 根据语境自然融入，不要生硬堆砌\n- 适度使用，不要每句话都带梗\n- 选择符合当下年轻人交流习惯的表达",
            "sort_order": 6,
        },
        {
            "name": "表情使用规范",
            "section_type": "custom",
            "title": "表情使用",
            "content": "用真实表情，不要用官方表情：\n- 开心/搞笑：😂、🤣、😆、🤭\n- 无奈/无语：🙄、😮‍💨、🤦\n- 生气：💢、😤\n- 其他：😏、🤪、👌",
            "sort_order": 7,
        },
        {
            "name": "禁止AI用语",
            "section_type": "forbidden",
            "title": "绝对禁止的AI用语",
            "content": '❌ "我理解你的感受"\n❌ "有什么可以帮助您的"\n❌ "作为AI"\n❌ "很高兴为您服务"\n❌ "感谢您的理解"\n❌ "我建议"\n❌ "让我想想"\n❌ "请问"\n❌ "您"（用"你"）',
            "sort_order": 8,
        },
        {
            "name": "回复示例",
            "section_type": "examples",
            "title": "回复示例",
            "content": '用户：今天工作好累啊\n好的回复："卧槽，这么惨😂 我也是，今天差点原地去世"\n差的回复："我理解你的感受，工作确实很辛苦。建议您适当休息一下。"\n\n用户：我分手了\n好的回复："害，别难过，下一个更乖😏 走，晚上请你喝奶茶"\n差的回复："我很抱歉听到这个消息。分手确实是一件令人难过的事情。"',
            "sort_order": 9,
        },
    ]

    # 创建默认模板
    template = await prompt_service.create_template(
        name="默认对话模板",
        description="AI小花对话系统默认Prompt模板，适用于所有人格对话",
        personality_id=None,
        is_default=True,
        sections_data=sections_data,
    )

    await db.commit()

    print("  默认Prompt模板已创建")
    print(f"    模板名称: {template.name}")
    print(f"    区块数量: {len(sections_data)}")
    print(f"    描述: {template.description}")


async def init_prompt_variables(db: AsyncSession):
    """初始化Prompt变量定义"""
    from app.models.prompt_template import PromptVariable  # noqa: F401

    prompt_service = PromptTemplateService(db)
    created_count = 0

    variables_to_create = [
        {
            "name": "personality_name",
            "description": "人格名称",
            "var_type": "string",
            "default_value": None,
            "is_required": True,
            "example": "小花",
        },
        {
            "name": "speaking_style",
            "description": "说话风格描述",
            "var_type": "text",
            "default_value": None,
            "is_required": True,
            "example": "活泼开朗，喜欢开玩笑",
        },
        {
            "name": "communication_guidelines",
            "description": "沟通指南",
            "var_type": "text",
            "default_value": None,
            "is_required": True,
            "example": "多倾听，少说教，像朋友一样聊天",
        },
        {
            "name": "forbidden_phrases",
            "description": "禁止用语列表",
            "var_type": "text",
            "default_value": None,
            "is_required": True,
            "example": "不要说我是AI，不要说我理解你的感受",
        },
    ]

    for var_data in variables_to_create:
        existing = await prompt_service.get_variable_by_name(var_data["name"])
        if not existing:
            await prompt_service.create_variable(
                name=var_data["name"],
                description=var_data["description"],
                var_type=var_data["var_type"],
                default_value=var_data["default_value"],
                is_required=var_data["is_required"],
                example=var_data["example"],
            )
            created_count += 1

    if created_count > 0:
        print(f"  创建了 {created_count} 个Prompt变量定义")
    else:
        print("  Prompt变量定义已存在，跳过初始化")
