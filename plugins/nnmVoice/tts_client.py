import websockets
import json
import requests
import os
from datetime import datetime
from pathlib import Path

# git clone https://huggingface.co/spaces/Mahiruoshi/BangDream-Bert-VITS2
# cd BangDream-Bert-VITS2
# pip install -r requirements.txt
# python app.py
# 字数限制 玩家等待 插件控制 如果队列里发的语音超过5就不发 判断是否为text

VOICE_DIR = Path("voice")
VOICE_DIR.mkdir(parents=True, exist_ok=True)

# WebSocket 地址
WEBSOCKET_URL = "wss://mahiruoshi-mygo-vits-bert.hf.space/queue/join"
AUDIO_BASE_URL = "https://mahiruoshi-mygo-vits-bert.hf.space/file="
HEADERS = {
    "Origin": "https://mahiruoshi-mygo-vits-bert.hf.space"
}


async def run_tts(text):
    # 构造请求参数
    full_data = [
        None, 50, "D:/audiobook/book1", 0.5,
        "ましろ|天音\n七深|七深\n透子|透子\nつくし|筑紫\n瑠唯|瑠唯\nそよ|素世\n祥子|祥子",
        f"七深|{text}",
        0.5, 0.6, 0.667, 1,
        "七深", "", 0.7,
        "Auto", "pyopenjtalk-V2.3", "paragraph",
        False, False
    ]

    # 连接 WebSocket 并发送消息
    async with websockets.connect(WEBSOCKET_URL) as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "fn_index": 101,
            "session_hash": "4v0j6i9uce9"
        }))
        await ws.recv()
        await ws.send(json.dumps({
            "data": full_data,
            "event_data": None,
            "fn_index": 101,
            "session_hash": "4v0j6i9uce9"
        }))

        while True:
            msg = await ws.recv()
            msg_json = json.loads(msg)
            print("收到：", msg_json.get("msg"))

            if msg_json.get("msg") == "process_completed":
                try:
                    filename = msg_json["output"]["data"][0]["name"]
                    audio_url = AUDIO_BASE_URL + filename

                    # 下载音频
                    r = requests.get(audio_url)

                    # ✅ 使用 timestamp 命名文件
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    save_path = VOICE_DIR / f"output_{timestamp}.wav"
                    with open(save_path, "wb") as f:
                        f.write(r.content)
                    print(f"✅ 音频保存成功：{save_path}")

                    # ✅ 清理 voice 目录，保留最近 1000 个 .wav 文件
                    wav_files = sorted(VOICE_DIR.glob("*.wav"), key=os.path.getctime)
                    if len(wav_files) > 1000:
                        for f in wav_files[:-1000]:
                            os.remove(f)
                            print(f"🧹 已删除多余语音文件：{f}")
                    return save_path

                except Exception as e:
                    print("❌ 解析或下载失败：", e)
                    print("完整响应数据：", msg_json)
                    break
