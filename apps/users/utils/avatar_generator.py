# apps/users/utils/avatar_generator.py

from PIL import Image, ImageDraw, ImageFont
import random, os
from django.conf import settings


def generate_avatar(username: str) -> str:
    """
    根据用户名生成随机颜色背景 + 首字母头像图片
    返回：头像相对路径（相对于 MEDIA_ROOT）
    """
    # 文件名与路径
    avatar_filename = f"{username}_avatar.png"
    avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
    avatar_path = os.path.join(avatar_dir, avatar_filename)

    # 确保目录存在
    os.makedirs(avatar_dir, exist_ok=True)

    # 随机背景色
    bg_color = tuple(random.randint(100, 255) for _ in range(3))
    img = Image.new('RGB', (256, 256), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 用户名首字母
    text = username[0].upper()
    font_size = 120
    try:
        font = ImageFont.truetype("arial.ttf", font_size)  # Windows 可用
    except:
        font = ImageFont.load_default()

    # ---- 计算文字大小并居中 ----
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # bbox[1] 是字体顶部相对于基线的偏移
    # 这段计算可以让文字在垂直方向上真正居中
    x = (256 - text_width) / 2 - bbox[0]
    y = (256 - text_height) / 2 - bbox[1]

    draw.text((x, y), text, fill='white', font=font)

    # 保存文件
    img.save(avatar_path)

    # 返回相对路径（用于存入数据库）
    return f"avatars/{avatar_filename}"
