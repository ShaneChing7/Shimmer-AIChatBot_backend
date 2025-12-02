# apps/users/views.py

from rest_framework import generics, permissions, views, status, serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes # 新增导入

from .serializers import (
    UserRegisterSerializer, 
    UserProfileSerializer,
    PasswordChangeSerializer,
    AccountDeleteSerializer,
    AvatarUploadSerializer
)
from .models import CustomUser
from .utils.response import success_response, error_response


# -------------------- 用户注册 --------------------
@extend_schema(
    tags=["用户认证"],
    summary="用户注册",
    description="注册新用户，成功后返回用户信息。",
    responses={201: UserProfileSerializer}
)
class UserRegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success_response(
            data=UserProfileSerializer(user).data,
            message="注册成功"
        )


# -------------------- JWT 登录 --------------------
@extend_schema(
    tags=["用户认证"],
    summary="用户登录",
    description="获取 Access Token 和 Refresh Token",
    responses={200: TokenObtainPairSerializer}
)
class UserTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return success_response(
            data=data,
            message="登录成功"
        )


# -------------------- JWT 刷新 --------------------
@extend_schema(
    tags=["用户认证"],
    summary="刷新 Token",
    description="使用 Refresh Token 获取新的 Access Token"
)
class UserTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success_response(
            data=serializer.validated_data,
            message="刷新 token 成功"
        )


# -------------------- 用户信息 --------------------
@extend_schema(
    tags=["用户管理"],
    summary="获取/修改个人信息",
    description="获取当前登录用户的详细信息，或修改部分字段（如email, username等）。"
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return success_response(data=serializer.data, message="获取用户信息成功")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(data=serializer.data, message="用户信息更新成功")


# -------------------- 单独上传头像 --------------------
class AvatarUploadView(views.APIView):
    """
    单独上传头像（带压缩和验证）
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["用户管理"],
        summary="上传头像",
        description="支持 jpg/png/gif/webp 格式，最大10MB。上传后会自动压缩。",
        request=AvatarUploadSerializer,  # 关键：告诉文档这里接收一个文件
        responses={200: UserProfileSerializer} # 关键：告诉文档返回的是用户信息
    )
    def post(self, request):
        serializer = AvatarUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                message=str(serializer.errors),
                code=400
            )
        
        avatar = serializer.validated_data['avatar']
        
        # 压缩图片
        try:
            compressed_avatar = serializer.compress_image(avatar)
        except serializers.ValidationError as e:
            return error_response(message=str(e), code=400)
        
        # 保存头像（save方法会自动删除旧头像）
        user = request.user
        user.avatar = compressed_avatar
        user.save()
        
        # 返回用户信息
        profile_serializer = UserProfileSerializer(user, context={'request': request})
        return success_response(
            data=profile_serializer.data,
            message="头像上传成功"
        )


# -------------------- 修改密码 --------------------
class PasswordChangeView(views.APIView):
    """
    修改密码视图
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["用户安全"],
        summary="修改密码",
        description="需要提供旧密码进行验证。成功后建议重新登录。",
        request=PasswordChangeSerializer, # 关键：链接到 serializers.py 中的定义
        responses={
            200: OpenApiTypes.OBJECT, # 返回通用的 JSON 对象
        },
        examples=[
            # 可选：添加请求示例
        ]
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            try:
                refresh_token = request.data.get('refresh_token')
                if refresh_token:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
            except Exception:
                pass
            
            return success_response(
                data=None,
                message="密码修改成功，请重新登录"
            )
        
        return error_response(
            message=str(serializer.errors),
            code=400
        )


# -------------------- 注销账号（永久删除） --------------------
class AccountDeleteView(views.APIView):
    """
    注销账号视图（永久删除账号）
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["用户安全"],
        summary="注销/删除账号",
        description="永久删除当前账号。需要验证密码，并且 confirmation 字段必须输入 'DELETE'。",
        request=AccountDeleteSerializer, # 关键：链接到 serializers.py 中的定义
        responses={
            200: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        serializer = AccountDeleteSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            username = user.username
            user_id = user.id
            
            # 执行删除操作
            user.delete()
            
            try:
                refresh_token = request.data.get('refresh_token')
                if refresh_token:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
            except Exception:
                pass
            
            return success_response(
                data={'username': username, 'id': user_id},
                message="账号已成功注销"
            )
        
        return error_response(
            message=str(serializer.errors),
            code=400
        )