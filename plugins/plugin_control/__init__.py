from pathlib import Path
import json
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, MessageSegment

PLUGIN_STATUS_PATH = Path(__file__).resolve().parent / "plugin_status.json"

# key: 英文标识  name: 中文名称
PLUGIN_KEYS = {
    "bread": "甜点功能",
    "imageGeneration": "AI画图",
    "nnmVoice": "语音",
}
PLUGIN_ALIASES = {v: k for k, v in PLUGIN_KEYS.items()}  # 中文 → 英文反查


def _ensure_status_file():
    PLUGIN_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not PLUGIN_STATUS_PATH.exists():
        with open(PLUGIN_STATUS_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)


def load_plugin_status():
    _ensure_status_file()
    with open(PLUGIN_STATUS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_plugin_status(data):
    with open(PLUGIN_STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_plugin_enabled(group_id: int, plugin_name: str) -> bool:
    data = load_plugin_status()
    return data.get(str(group_id), {}).get(plugin_name, True)


def set_plugin_enabled(group_id: int, plugin_name: str, enabled: bool):
    data = load_plugin_status()
    group_str = str(group_id)
    if group_str not in data:
        data[group_str] = {}
    data[group_str][plugin_name] = enabled
    save_plugin_status(data)


# ✅ 插件控制入口
async def check_plugin_control_command(bot: Bot, event: MessageEvent, msg: str) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False

    group_id = event.group_id
    user_id = int(event.get_user_id())

    # 权限判断
    info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
    if info.get("role") not in ["admin", "owner"]:
        if msg.startswith("nnm启用插件") or msg.startswith("nnm禁用插件"):
            await bot.send(event, "只有群管理员可以控制插件开关哦！")
        return msg.startswith("nnm启用插件") or msg.startswith("nnm禁用插件")

    # /插件状态
    if msg.strip() == "nnm插件状态":
        status = load_plugin_status()
        group_status = status.get(str(group_id), {})
        text = "nnm当前插件状态：\n"
        for key, name in PLUGIN_KEYS.items():
            enabled = group_status.get(key, True)
            text += f"- {name}：{'✅ 开启' if enabled else '❌ 关闭'}\n"
        await bot.send(event, MessageSegment.text(text))
        return True

    # /启用插件 xxx 或 /禁用插件 xxx
    if msg.startswith("nnm启用插件") or msg.startswith("nnm禁用插件"):
        parts = msg.split()
        if len(parts) != 2:
            print(len(parts))
            await bot.send(event, "❗格式错误，用法：nnm启用插件 插件名")
            return True

        plugin_input = parts[1].strip()
        plugin_key = plugin_input

        # 支持中文名转 key
        if plugin_key not in PLUGIN_KEYS:
            plugin_key = PLUGIN_ALIASES.get(plugin_input)

        if plugin_key not in PLUGIN_KEYS:
            await bot.send(event, f"❗未找到：{plugin_key}")
            await bot.send(event, f"❗未找到插件：{plugin_input}")
            return True

        enabled = msg.startswith("nnm启用插件")
        set_plugin_enabled(group_id, plugin_key, enabled)
        await bot.send(event, f"插件【{PLUGIN_KEYS[plugin_key]}】已{'✅ 启用' if enabled else '❌ 禁用'}")
        return True

    # 原指令支持（开启甜点系统 / 关闭签到系统 等）
    for key, name in PLUGIN_KEYS.items():
        if msg in [f"开启{name}", f"关闭{name}"]:
            enabled = msg.startswith("开启")
            set_plugin_enabled(group_id, key, enabled)
            await bot.send(event, f"{name} 已 {'✅ 开启' if enabled else '❌ 关闭'}")
            return True

    return False
