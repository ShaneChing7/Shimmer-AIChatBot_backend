# apps/chat/serializers.py
from rest_framework import serializers
from .models import ChatSession, ChatMessage,MessageFile
from apps.users.models import CustomUser

# 附件序列化器
class MessageFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = MessageFile
        fields = ['id', 'file', 'file_url', 'parsed_content']

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


# 用于消息列表显示
class ChatMessageSerializer(serializers.ModelSerializer):
    # 包含多个文件
    files = MessageFileSerializer(many=True, read_only=True)
    
    # 兼容旧字段
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'sender', 'content_type', 'content', 'file', 'file_url', 'parsed_content', 'reasoning_content', 'created_at', 'files', 'status']
        read_only_fields = ['parsed_content', 'file_url', 'files', 'status'] # 状态由后端控制
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
# 用于会话列表显示
class ChatSessionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'created_at']

# 用于获取单个会话及其所有消息
class ChatSessionDetailSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'user', 'created_at', 'messages']
        read_only_fields = ['user'] # user 字段在创建时自动设置，不允许前端直接指定