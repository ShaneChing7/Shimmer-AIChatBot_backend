# apps/chat/models.py
from django.db import models
from django.conf import settings # 引入 settings 来获取 AUTH_USER_MODEL

class ChatSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # 当用户删除时，关联的会话也一并删除
        related_name='chat_sessions', # 方便从 user 对象反向查询
        verbose_name="用户"
    )
    title = models.CharField(max_length=255, verbose_name="会话标题") # e.g., "Django 模型设计", "周末去哪玩"
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        ordering = ['-created_at'] # 通常我们希望最新的会话显示在最前面
        verbose_name = "聊天会话"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
class ChatMessage(models.Model):
    # 定义发送者类型
    class SenderChoices(models.TextChoices):
        USER = 'user', '用户'
        AI = 'ai', 'AI'

    # 定义消息内容类型
    class ContentTypeChoices(models.TextChoices):
        TEXT = 'text', '纯文本'
        MARKDOWN = 'markdown', 'Markdown'
        IMAGE_URL = 'image_url', '图片链接' # 存储图片的URL
        FILE = 'file', '文件上传'
    
    # 定义消息状态 
    class StatusChoices(models.TextChoices):
        COMPLETED = 'completed', '已完成'
        GENERATING = 'generating', '生成中'
        INTERRUPTED = 'interrupted', '已中断'
        ERROR = 'error', '错误'

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE, # 当会话删除时，消息也一并删除
        related_name='messages', # 方便从 session 对象反向查询
        verbose_name="会话"
    )
    sender = models.CharField(
        max_length=10,
        choices=SenderChoices.choices,
        verbose_name="发送者"
    )
    content_type = models.CharField(
        max_length=20,
        choices=ContentTypeChoices.choices,
        default=ContentTypeChoices.TEXT,
        verbose_name="内容类型"
    )
    content = models.TextField(verbose_name="消息内容", blank=True, default="")  # 存储文本、Markdown或图片URL
    
    # --- 旧字段 (为了兼容保留，主要使用 MessageFile) ---
    file = models.FileField(
        upload_to='chat_files/%Y/%m/', 
        blank=True, 
        null=True, 
        verbose_name="上传文件"
    )
    # 存储OCR或文档解析后的文本，避免重复解析
    parsed_content = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="文件解析内容"
    )
    # ---------------------------------------------------

    # 存储 DeepSeek Reasoner 的推理过程
    reasoning_content = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="推理过程",
        help_text="DeepSeek Reasoner 模型的思考过程"
    )
    
    # 状态字段，默认为完成 (兼容旧数据)
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.COMPLETED,
        verbose_name="状态"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="发送时间")

    class Meta:
        ordering = ['created_at'] # 消息按时间顺序排列
        verbose_name = "聊天消息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"[{self.get_sender_display()}] {self.id}"
    # 支持多文件上传的模型
class MessageFile(models.Model):
    message = models.ForeignKey(
        ChatMessage, 
        related_name='files', # 反向查询字段名
        on_delete=models.CASCADE,
        verbose_name="所属消息"
    )
    file = models.FileField(
        upload_to='chat_files/%Y/%m/', 
        verbose_name="文件"
    )
    parsed_content = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="解析内容"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "消息附件"
        verbose_name_plural = verbose_name