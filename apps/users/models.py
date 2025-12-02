# apps/users/models.py
import uuid
import os
import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator

def generate_uid():
    # 生成一个8位的随机字符UID，也可以使用 uuid.uuid4().hex[:8]
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
def user_avatar_path(instance, filename):
    """
    动态生成头像保存路径
    格式: avatars/user_{uid}/{uuid}.{ext}
    好处：
    1. 按用户分组，方便管理
    2. 使用UUID避免文件名冲突
    3. 保留原始文件扩展名
    """
    ext = os.path.splitext(filename)[1].lower()
    new_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('avatars', f'user_{instance.uid}', new_filename)


class CustomUser(AbstractUser):
    # Django 自带 username, password, email, first_name, last_name等字段

    uid = models.CharField(
        max_length=12, 
        unique=True, 
        editable=False, 
        verbose_name="用户UID",
        default=generate_uid # 数据库迁移时会用到
    )


    avatar = models.ImageField(
        upload_to=user_avatar_path,  # 使用动态路径函数
        null=True,
        blank=True,
        verbose_name="用户头像",
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp']
            )
        ],
        help_text="支持格式: JPG, PNG, GIF, WEBP，最大10MB"
    )

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = generate_uid()
            while CustomUser.objects.filter(uid=self.uid).exists():
                self.uid = generate_uid()
        
        # 删除旧头像（如果更新头像）
        if self.pk:  # 如果是更新操作
            try:
                old_user = CustomUser.objects.get(pk=self.pk)
                if old_user.avatar and old_user.avatar != self.avatar:
                    # 如果旧头像不是默认头像，则删除
                    if old_user.avatar.name and 'default' not in old_user.avatar.name:
                        if os.path.isfile(old_user.avatar.path):
                            os.remove(old_user.avatar.path)
            except CustomUser.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

    def get_avatar_url(self):
        """
        获取头像URL，如果没有头像返回默认头像
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/media/avatars/default/user.png'  # 默认头像路径

    def __str__(self):
        return self.username