import json
import os
import random
from nonebot import on_message
from nonebot.adapters.onebot.v11 import (
    Bot, MessageEvent, GroupMessageEvent, PrivateMessageEvent,
    MessageSegment
)
from pathlib import Path
from plugins.bread.bread_manager import handle_bread_command
from plugins.plugin_control.__init__ import (
    check_plugin_control_command
)
import time
from plugins.plugin_control import is_plugin_enabled
from plugins.AIImage import PollinationsAIWrapper
from plugins.nnmVoice.tts_client import run_tts

msg_handler = on_message()
ai_generator = PollinationsAIWrapper(
    save_dir="plugins/AIImage/generated_images"
)

# 路径和全局常量配置
PLUGIN_DIR = Path(__file__).parent
CONFIG_PATH = PLUGIN_DIR / "reply_config.json"
IMG_PATH = PLUGIN_DIR / "image"
AUDIO_PATH = PLUGIN_DIR / "audio"
MAX_QUEUE = 5
MAX_LENGTH = 25
VOICE_DIR = "plugins/nnmVoice/voice"
last_image_request_time = 0
last_voice_request_time = 0

# 加载 JSON 规则
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    reply_rules = json.load(f)


@msg_handler.handle()
async def handle(event: MessageEvent, bot: Bot):
    msg = str(event.get_message()).strip()
    user_id = int(event.get_user_id())
    group_id = None
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id

    if await check_plugin_control_command(bot, event, msg):
        return

    for rule in reply_rules:
        if match_message(rule["type"], rule["message"], msg):
            selected = random.choice(rule["reply"])
            await send_reply(bot, event, selected)
            return

    # 甜点功能
    if msg == "买甜点" or msg == "查甜点" or msg == "吃甜点" or msg.startswith("抢甜点") or \
            msg.startswith("送甜点"):
        at = next((seg for seg in event.message if seg.type == "at"), None)
        target_id = int(at.data["qq"]) if at else None
        result = await handle_bread_command(user_id, msg, group_id, target_id)
        if result:
            await send_reply(bot, event, result)

    if msg.startswith("nnm画图"):
        if group_id and not is_plugin_enabled(group_id, "imageGeneration"):
            return

        global last_image_request_time
        now = time.time()
        if now - last_image_request_time < 5:
            await send_reply(bot, event, "请求过于频繁，nnm画累啦，请稍后再试~")
            return

        prompt = msg[5:].strip()
        if not prompt or not prompt.isprintable():
            await send_reply(bot, event, "你想让nnm画什么呢？")
            return

        last_image_request_time = now
        await send_reply(bot, event, "稍等，nnm正在画图中...")

        image_path = await ai_generator.generate_image(prompt)
        if image_path and os.path.exists(image_path):
            await send_message(bot, event, MessageSegment.at(user_id) +
                               MessageSegment.image(f"file:///{os.path.abspath(image_path)}"))
        else:
            await send_reply(bot, event, f"呜呜，nnm画失败了")
        return

    # 语音
    if msg.startswith("nnm说"):
        if group_id and not is_plugin_enabled(group_id, "nnmVoice"):
            return

        content = msg.removeprefix("nnm说").strip()
        if not content:
            await send_reply(bot, event, "想让nnm说什么呢？")
            return
        if len(content) > MAX_LENGTH:
            await send_reply(bot, event, "太长啦，nnm最多只能说25个字哦")
            return

        global last_voice_request_time
        now = time.time()
        if now - last_voice_request_time < 5:
            await send_reply(bot, event, "nnm说太多话啦，稍后再来吧~")
            return

        last_voice_request_time = now

        await bot.send(event, MessageSegment.text(f"nnm正在酝酿情感准备说：{content}"))

        path = await run_tts(content)
        if path and os.path.exists(path):
            await send_message(bot, event, MessageSegment.record(f"file:///{os.path.abspath(path)}"))
        else:
            await bot.send(event, MessageSegment.text("出错了！nnm出不了声了..."))
        return


# 判断匹配规则
def match_message(match_type: str, rule_keywords, msg: str) -> bool:
    # 支持 message 为 str 或 list[str]
    if isinstance(rule_keywords, str):
        rule_keywords = [rule_keywords]

    for keyword in rule_keywords:
        if match_type == "prefix" and msg.startswith(keyword):
            return True
        elif match_type == "suffix" and msg.endswith(keyword):
            return True
        elif match_type == "fullMatch" and msg == keyword:
            return True
        elif match_type == "inMessage" and keyword in msg:
            return True
    return False


# 回复封装：自动识别文本/图片/音频
async def send_reply(bot: Bot, event: MessageEvent, content: str):
    msg = build_message_segment(content)
    await send_message(bot, event, msg)


# 构造 MessageSegment
def build_message_segment(content: str) -> MessageSegment:
    if content.lower().endswith((".jpg", ".png", ".jpeg", ".gif")):
        path = (IMG_PATH / content).resolve()
        return MessageSegment.image(f"file:///{path.resolve()}")
    elif content.lower().endswith(".mp3"):
        path = (AUDIO_PATH / content).resolve()
        return MessageSegment.record(f"file:///{path.resolve()}")
    else:
        return MessageSegment.text(content)


# 发送私聊/群聊消息
async def send_message(bot: Bot, event: MessageEvent, msg: MessageSegment):
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_msg(group_id=event.group_id, message=msg)
    elif isinstance(event, PrivateMessageEvent):
        await bot.send_private_msg(user_id=event.user_id, message=msg)
