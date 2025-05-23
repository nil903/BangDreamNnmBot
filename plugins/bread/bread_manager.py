import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from plugins.plugin_control import is_plugin_enabled

DATA_PATH = Path(__file__).resolve().parent / "data.json"


async def load_data():
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


async def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_time(last_time_str: str) -> int:
    now = datetime.now()
    try:
        last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return 1
    minutes = (now - last_time).seconds / 60
    days = (now - last_time).days
    if days >= 1:
        return 1
    elif minutes >= 60:
        return 2
    return int(60 - minutes)


async def buy_bread(user_id: int) -> str:
    data = await load_data()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for user in data:
        if user["user_id"] == user_id:
            status = check_time(user["time"])
            if status == 1:
                amount = random.randint(1, 10) * 2
                user["bread"] += amount
                user["time"] = now_str
                await save_data(data)
                return f"本日首次！甜点数×2，买了 {amount} 个甜点，你已拥有 {user['bread']} 个甜点"
            elif status == 2:
                amount = random.randint(1, 10)
                user["bread"] += amount
                user["time"] = now_str
                await save_data(data)
                return f"你已成功购买 {amount} 个甜点，你已拥有 {user['bread']} 个甜点"
            else:
                return f"还要再等 {status} 分钟才可以买甜点哦"

    amount = random.randint(1, 10) * 5
    new_user = {
        "user_id": user_id,
        "bread": float(amount),
        "time": now_str
    }
    data.append(new_user)
    await save_data(data)
    return f"首次买甜品！甜点数×5，你已拥有 {amount} 个甜点，记得每小时都来一次哦"


async def my_bread(user_id: int) -> str:
    data = await load_data()
    for user in data:
        if user["user_id"] == user_id:
            return f"你现在有 {user['bread']} 个甜点"
    return "你还没有买过甜点哦，发送“买甜点”试试看吧~"


async def eat_bread(user_id: int) -> str:
    data = await load_data()
    for user in data:
        if user["user_id"] == user_id:
            if user["bread"] <= 0:
                if user["bread"] == 0:
                    return "你没有甜点可以吃哦~"
                else:
                    return f"不可以吃霸王餐哦！你还要帮七深刷 {abs(user['bread'])} 个盘子才可以吃甜点"
            amount = random.randint(1, 10)
            eat = min(amount, user["bread"])
            user["bread"] -= eat
            await save_data(data)
            return f"你吃掉了 {eat} 个甜点，还剩 {user['bread']} 个~\n诶？你问nnm有什么用吗？nnm也不知道哦。"
    return "你还没有买过甜点哦，发送“买甜点”试试看吧~"


async def grab_bread(host_id: int, target_id: int) -> str:
    if host_id == target_id:
        return "不可以抢自己！"

    data = await load_data()
    host = next((u for u in data if u["user_id"] == host_id), None)
    target = next((u for u in data if u["user_id"] == target_id), None)

    if not host or not target:
        return "自己或对方还没有买过甜点哦~"

    dice = random.randint(1, 100)
    amount = random.randint(1, 10)

    if dice > 50:
        if target["bread"] < 0:
            return f"TA还要帮七深打工还债卖出{abs(target['bread'])}份甜品才可以抢甜品哦"
        target["bread"] -= amount
        host["bread"] += amount
        result = f"1D100={dice} > 50，判定成功！你抢走了对方 {amount} 个甜点"
    else:
        if host["bread"] < 0:
            return f"你还要帮七深卖出{abs(host['bread'])}份甜品才可以抢甜品哦"
        host["bread"] -= amount
        target["bread"] += amount
        result = f"1D100={dice} ≤ 50，判定失败，被对方抢走{amount} 个甜点"

    await save_data(data)
    return result


async def send_bread(host_id: int, target_id: int) -> str:
    if host_id == target_id:
        return "不能送给自己啦，nnm会失业的！"

    data = await load_data()
    host = next((u for u in data if u["user_id"] == host_id), None)
    target = next((u for u in data if u["user_id"] == target_id), None)

    if not host or not target:
        return "自己或对方还没有买过甜点哦~"

    now = datetime.now()

    # 判断是否在1小时内送过
    last_send_time_str = host.get("send_time")
    if last_send_time_str:
        last_send_time = datetime.strptime(last_send_time_str, "%Y-%m-%d %H:%M:%S")
        if now - last_send_time < timedelta(hours=1):
            remaining = timedelta(hours=1) - (now - last_send_time)
            minutes = remaining.seconds // 60
            return f"你已经送过甜点了，请 {minutes} 分钟后再试~"

    amount = random.randint(1, 10)
    if host["bread"] < amount:
        return f"你还要帮七深卖出 {amount - host['bread']} 份甜品才可以送甜品哦"

    host["bread"] -= amount
    target["bread"] += amount
    host["send_time"] = now.strftime("%Y-%m-%d %H:%M:%S")

    await save_data(data)
    return f"你成功送给 ta {amount} 个甜点！你还剩 {host['bread']} 个"


async def handle_bread_command(user_id: int, msg: str, group_id: int = None, target_id: int = None) -> str:
    # 插件启用判断
    print(f"[debug] group_id={group_id}, 插件是否启用={is_plugin_enabled(group_id, 'bread') if group_id else 'N/A'}")
    if group_id and not is_plugin_enabled(group_id, "bread"):
        return ""  # 插件被禁用时不响应

    if msg == "买甜点":
        return await buy_bread(user_id)
    elif msg == "查甜点":
        return await my_bread(user_id)
    elif msg == "吃甜点":
        return await eat_bread(user_id)
    elif msg.startswith("抢甜点"):
        if not target_id:
            return "请@一个群友才能抢甜点哦！"
        return await grab_bread(user_id, target_id)
    elif msg.startswith("送甜点"):
        if not target_id:
            return "请@一个群友来送甜点哦！"
        return await send_bread(user_id, target_id)
    return ""
