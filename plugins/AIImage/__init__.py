import httpx
from typing import Optional
from urllib.parse import quote
import os
from datetime import datetime
import random
import asyncio
from googletrans import Translator


class PollinationsAIWrapper:
    def __init__(self, save_dir: str = "pollinations_images", max_images: int = 1000):
        self.base_url = "https://image.pollinations.ai/prompt/"
        self.save_dir = save_dir
        self.max_images = max_images
        os.makedirs(self.save_dir, exist_ok=True)

        # 默认正向提示词（风格和画质）
        self.default_prompt_prefix = (
            "{{masterpiece}},{{best quality}},{{highres}},illustration,"
            "extremely detailed CG unity 8k wallpaper,"
            "finely full body anime illustration"
        )

        # 默认负向提示词（常见问题）
        self.default_negative_prompt = (
            "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, "
            "cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, "
            "watermark, username, blurry, multiple breasts, multiple legs, "
            "multiple arms, (mutate hands and fingers:1:5), text, 3d"
        )

        self.translator = Translator()

    def _cleanup_old_images(self):
        """如果图片超过上限，自动删除最旧的一张"""
        image_files = sorted(
            [f for f in os.listdir(self.save_dir) if f.lower().endswith(".jpg")],
            key=lambda x: os.path.getctime(os.path.join(self.save_dir, x))
        )
        while len(image_files) >= self.max_images:
            oldest = image_files.pop(0)
            try:
                os.remove(os.path.join(self.save_dir, oldest))
            except Exception as e:
                print(f"删除旧图片出错: {e}")

    async def _translate_prompt(self, user_message: str) -> str:
        """异步封装同步翻译"""
        try:
            result = await self.translator.translate(user_message, src='auto', dest='en')
            return result.text
        except Exception as e:
            raise RuntimeError(f"翻译失败: {e}")

    async def generate_image(
            self,
            user_message: str,
            seed: Optional[int] = None,
            style: str = "japanese anime style",
            extra_negative_prompt: Optional[str] = None,
    ) -> str:
        """自动翻译 + 图像生成 + 本地保存 + 自动清理老图"""
        if seed is None:
            seed = random.randint(10000, 99999)

        try:
            translated = await self._translate_prompt(user_message)
        except Exception as e:
            return str(e)

        # 正向 & 负向提示词拼接
        full_prompt = f"{self.default_prompt_prefix}, {translated}, {style}"
        full_negative = self.default_negative_prompt
        if extra_negative_prompt:
            full_negative += f", {extra_negative_prompt}"
        full_prompt += f", --no {full_negative}"

        encoded_prompt = quote(full_prompt)
        image_url = f"{self.base_url}{encoded_prompt}?seed={seed}"

        # 自动清理旧图（超 1000）
        self._cleanup_old_images()

        # 下载图像并保存
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.get(image_url)
                if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"pollinations_{seed}_{timestamp}.jpg"
                    image_path = os.path.join(self.save_dir, file_name)
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    return image_path
                else:
                    return f"生成失败，状态码: {response.status_code}"
            except Exception as e:
                return f"请求错误: {str(e)}"
