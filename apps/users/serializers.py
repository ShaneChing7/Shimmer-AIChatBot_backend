# apps/users/serializers.py

from rest_framework import serializers
from .models import CustomUser
from .utils.avatar_generator import generate_avatar
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import io

class AvatarUploadSerializer(serializers.Serializer):
    """
    头像上传序列化器（带验证和压缩）
    """
    avatar = serializers.ImageField(required=True)

    def validate_avatar(self, value):
        """验证头像文件"""
        # 1. 检查文件大小 (10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("头像文件大小不能超过10MB")
        
        # 2. 检查文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("只支持 JPG, PNG, GIF, WEBP 格式")
        
        # 3. 验证是否为有效图片
        try:
            img = Image.open(value)
            img.verify()
        except Exception:
            raise serializers.ValidationError("无效的图片文件")
        
        return value

    def compress_image(self, image_file, max_width=800, max_height=800, quality=85):
        """
        压缩图片
        - 限制最大尺寸
        - 压缩质量
        - 转换为RGB（避免透明通道问题）
        """
        try:
            img = Image.open(image_file)
            
            # 转换为RGB（处理PNG透明背景）
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # 等比例缩放
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # 保存到内存
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            # 创建新的上传文件对象
            compressed_file = InMemoryUploadedFile(
                output,
                'ImageField',
                f"{image_file.name.split('.')[0]}.jpg",
                'image/jpeg',
                output.getbuffer().nbytes,
                None
            )
            
            return compressed_file
        except Exception as e:
            raise serializers.ValidationError(f"图片压缩失败: {str(e)}")

class UserRegisterSerializer(serializers.ModelSerializer):
    """
    用户注册序列化器
    """
    password2 = serializers.CharField(label="确认密码", write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'password2', 'email', 'avatar']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("两次输入的密码不一致")
        
        # 验证密码长度
        if len(data['password']) < 6:
            raise serializers.ValidationError("密码长度至少为6位")
        
        data.pop('password2')
        return data
    

    def create(self, validated_data):
        username = validated_data['username']

        if not validated_data.get('avatar'):
            validated_data['avatar'] = generate_avatar(username)

        user = CustomUser.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """
    用户个人资料序列化器
    """

    avatar_url = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'avatar', 'avatar_url', 'uid']
        read_only_fields = ['username', 'uid', 'avatar_url']

    def get_avatar_url(self, obj):
        """返回完整的头像URL"""
        if obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class PasswordChangeSerializer(serializers.Serializer):
    """
    密码修改序列化器
    """
    old_password = serializers.CharField(label="旧密码", write_only=True, required=True)
    new_password = serializers.CharField(label="新密码", write_only=True, required=True)
    new_password2 = serializers.CharField(label="确认新密码", write_only=True, required=True)

    def validate_old_password(self, value):
        """验证旧密码是否正确"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("旧密码不正确")
        return value

    def validate(self, data):
        """验证两次新密码是否一致"""
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError("两次输入的新密码不一致")
        
        # 验证新密码长度（与注册保持一致）
        if len(data['new_password']) < 6:
            raise serializers.ValidationError("密码长度至少为6位")
        
        return data

    def save(self):
        """保存新密码"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class AccountDeleteSerializer(serializers.Serializer):
    """
    账号注销序列化器
    """
    password = serializers.CharField(label="密码确认", write_only=True, required=True)
    confirmation = serializers.CharField(label="确认文本", write_only=True, required=True)

    def validate_password(self, value):
        """验证密码是否正确"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("密码不正确")
        return value

    def validate_confirmation(self, value):
        """验证确认文本"""
        if value != "DELETE":
            raise serializers.ValidationError("请输入 'DELETE' 确认删除账号")
        return value