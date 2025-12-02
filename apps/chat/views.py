from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser 
import json
from django.http import StreamingHttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, inline_serializer, OpenApiExample

from .models import ChatSession, ChatMessage, MessageFile
from .serializers import ChatSessionListSerializer, ChatSessionDetailSerializer, ChatMessageSerializer
from .utils import success_response, error_response  
from .services import get_deepseek_response_stream, extract_text_from_file, check_deepseek_balance

@extend_schema(tags=["DeepSeek 工具"])
class DeepSeekViewSet(viewsets.ViewSet):
    """
    DeepSeek API 相关设置与检测接口
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="查询余额",
        description="检查 DeepSeek API Key 的余额和有效性。Key 仅从前端传入，不在后端存储。",
        request=inline_serializer(
            name='CheckUsageRequest',
            fields={
                'api_key': serializers.CharField(help_text="DeepSeek API Key，如果不填则使用系统默认", required=True)
            }
        ),
        responses={
            200: inline_serializer(
                name='CheckUsageResponse',
                fields={
                    'is_available': serializers.BooleanField(),
                    'balance_infos': serializers.ListField(),
                    'currency': serializers.CharField()
                }
            )
        }
    )
    @action(detail=False, methods=['post'], url_path='check-usage')
    def check_usage(self, request):
        api_key = request.data.get('api_key')
        if not api_key:
            return error_response("API Key 不能为空", status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = check_deepseek_balance(api_key)
            return success_response(data, message="余额查询成功")
        except Exception as e:
            return error_response(f"查询失败: {str(e)}", code=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["会话管理"])
class ChatSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser] 

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionListSerializer
        return ChatSessionDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="获取会话列表",
        description="获取当前用户的所有会话，按时间倒序排列。支持分页。",
        responses={200: ChatSessionListSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return success_response(
                data=paginated_response.data,
                message="会话列表获取成功 (已分页)",
                code=status.HTTP_200_OK
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="会话列表获取成功",
            code=status.HTTP_200_OK
        )

    @extend_schema(
        summary="获取会话详情",
        description="获取单个会话的详细信息，包含该会话下的所有历史消息。",
        responses={200: ChatSessionDetailSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="会话详情获取成功",
            code=status.HTTP_200_OK
        )

    @extend_schema(
        summary="创建新会话",
        description="创建一个新的空会话。",
        responses={201: ChatSessionDetailSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer) 
        session_instance = serializer.instance 
        detail_serializer = ChatSessionDetailSerializer(session_instance)
        return success_response(
            data=detail_serializer.data,
            message="会话创建成功",
            code=status.HTTP_201_CREATED
        )

    @extend_schema(summary="删除会话")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(
            data=None, 
            message="会话删除成功",
            code=status.HTTP_200_OK 
        )

    @extend_schema(summary="修改会话标题")
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(
            data=serializer.data,
            message="会话标题修改成功",
            code=status.HTTP_200_OK
        )
    
    @extend_schema(
        summary="清空所有会话",
        description="危险操作：删除当前用户的所有会话记录。",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['delete'], url_path='delete-all')
    def delete_all_sessions(self, request):
        count, _ = self.get_queryset().delete()
        return success_response(
            data={'count': count}, 
            message=f"成功删除 {count} 个会话",
            code=status.HTTP_200_OK
        )

    @extend_schema(
        summary="导出数据",
        description="导出当前用户所有会话的完整 JSON 数据。",
        responses={200: ChatSessionDetailSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='export-data')
    def export_data(self, request):
        queryset = self.get_queryset().order_by('created_at')
        serializer = ChatSessionDetailSerializer(queryset, many=True, context={'request': request})
        return success_response(
            data=serializer.data,
            message="数据导出成功",
            code=status.HTTP_200_OK
        )

    # --------------------------------------------------------------------------------
    # 核心：流式对话接口文档
    # --------------------------------------------------------------------------------
    @extend_schema(
        tags=["对话核心"],
        summary="发送消息 (流式 SSE)",
        description="""
        **核心对话接口**。
        - **Content-Type**: 支持 `multipart/form-data` (用于发文件) 或 `application/json` (仅纯文本)。
        - **响应**: `text/event-stream` (SSE 流)。
        
        **流式事件类型 (Event Types)**:
        1. `event: message` (默认): 数据在 `data` 字段中。
           - `{"type": "reasoning", "content": "..."}`: 模型思考过程 (DeepSeek R1)。
           - `{"type": "content", "content": "..."}`: 模型正式回复。
        2. `event: done`: 对话结束，返回完整的消息对象。
        3. `event: error`: 发生错误。
        """,
        request=inline_serializer(
            name='StreamChatRequest',
            fields={
                'content': serializers.CharField(required=False, help_text="用户消息内容"),
                'model': serializers.CharField(default='deepseek-chat', help_text="模型名称，如 deepseek-reasoner"),
                'files': serializers.ListField(
                    child=serializers.FileField(), 
                    required=False, 
                    help_text="上传附件 (支持多文件上传)"
                ),
                'api_key': serializers.CharField(required=False, help_text="本次对话使用的自定义 API Key")
            }
        ),
        responses={
            200: {"description": "SSE 数据流", "content": {"text/event-stream": {}}}
        }
    )
    @action(detail=True, methods=['post'], url_path='messages-stream')
    def create_message_stream(self, request, pk=None):
        session = self.get_object()
        model = request.data.get('model', 'deepseek-chat')

        # 提取用户传入的 API Key
        api_key = request.data.get('api_key') 
        if not api_key:
            api_key = request.headers.get('X-DeepSeek-API-Key')

        # 保存用户消息
        user_message_data = request.data.dict()
        user_message_data['session'] = session.id
        user_message_data['sender'] = 'user'
        user_message_data['status'] = 'completed'

        if 'api_key' in user_message_data:
            del user_message_data['api_key']

        files = request.FILES.getlist('files')
        if not user_message_data.get('content') and files:
            user_message_data['content_type'] = 'file'

        user_serializer = ChatMessageSerializer(data=user_message_data)
        if not user_serializer.is_valid():
            return StreamingHttpResponse(
                json.dumps({"error": "用户消息验证失败", "details": user_serializer.errors}),
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json"
            )
        
        user_message = user_serializer.save(session=session)

        # 处理多文件逻辑
        all_parsed_text = ""
        if files:
            for file_obj in files:
                try:
                    msg_file = MessageFile.objects.create(message=user_message, file=file_obj)
                    parsed_text = extract_text_from_file(msg_file.file.path)
                    msg_file.parsed_content = parsed_text
                    msg_file.save()
                    all_parsed_text += f"\n\n--- 附件 [{file_obj.name}] 内容 ---\n{parsed_text}\n--- 结束 ---\n"
                except Exception as e:
                    print(f"File processing error: {e}")
                    all_parsed_text += f"\n[系统提示: 文件 {file_obj.name} 解析失败: {str(e)}]\n"
        
        elif request.FILES.get('file'):
             file_obj = request.FILES.get('file')
             msg_file = MessageFile.objects.create(message=user_message, file=file_obj)
             parsed_text = extract_text_from_file(msg_file.file.path)
             msg_file.parsed_content = parsed_text
             msg_file.save()
             all_parsed_text += f"\n\n--- 附件 [{file_obj.name}] 内容 ---\n{parsed_text}\n--- 结束 ---\n"

        # 构建历史消息
        history = session.messages.order_by('created_at')
        history_for_api = []
        for msg in history:
            role = "assistant" if msg.sender == 'ai' else "user"
            content = msg.content
            related_files = msg.files.all()
            if related_files:
                for f in related_files:
                    if f.parsed_content:
                        content += f"\n\n--- 附件 [{f.file.name}] 内容 ---\n{f.parsed_content}\n--- 结束 ---\n"
            elif msg.parsed_content:
                content += f"\n\n--- 附件内容 ---\n{msg.parsed_content}\n----------------"
            
            if not content.strip():
                content = "[空消息或仅文件]"
            history_for_api.append({"role": role, "content": content})

        # 流式生成器
        def stream_response_generator():
            full_ai_content = ""
            full_reasoning_content = ""
            completion_status = 'interrupted' 
            
            try:
                for chunk_data in get_deepseek_response_stream(history_for_api, model, api_key=api_key):
                    chunk_type = chunk_data.get("type")
                    chunk_content = chunk_data.get("content", "")
                    
                    if chunk_type == "reasoning":
                        full_reasoning_content += chunk_content
                        event_data = {"type": "reasoning", "content": chunk_content}
                        yield f"data: {json.dumps(event_data)}\n\n"
                    
                    elif chunk_type == "content":
                        full_ai_content += chunk_content
                        event_data = {"type": "content", "content": chunk_content}
                        yield f"data: {json.dumps(event_data)}\n\n"
                
                completion_status = 'completed'
            
            except Exception as e:
                completion_status = 'error'
                error_data = {"event": "error", "detail": f"AI 调用失败: {str(e)}"}
                yield f"data: {json.dumps(error_data)}\n\n"
            
            finally:
                if full_ai_content or full_reasoning_content:
                    ai_message_data = {
                        'session': session.id,
                        'sender': 'ai',
                        'content_type': 'markdown',
                        'content': full_ai_content,
                        'reasoning_content': full_reasoning_content,
                        'status': completion_status
                    }
                    ai_serializer = ChatMessageSerializer(data=ai_message_data)
                    if ai_serializer.is_valid():
                        ai_serializer.save(session=session)
                        if completion_status == 'completed':
                            done_data = {
                                "event": "done",
                                "message": ai_serializer.data,
                                "reasoning": full_reasoning_content
                            }
                            yield f"data: {json.dumps(done_data)}\n\n"
        
        response = StreamingHttpResponse(stream_response_generator(), content_type="text/event-stream")
        response['Cache-Control'] = 'no-cache'
        return response
    
    # --------------------------------------------------------------------------------
    # 核心：重新生成接口文档
    # --------------------------------------------------------------------------------
    @extend_schema(
        tags=["对话核心"],
        summary="重新生成 / 继续生成",
        description="让 AI 重新回答某条消息，或者接着上一条消息继续写 (Continue)。返回格式同流式接口。",
        request=inline_serializer(
            name='RegenerateRequest',
            fields={
                'message_id': serializers.IntegerField(help_text="需要重写的 AI 消息 ID"),
                'model': serializers.CharField(default='deepseek-chat'),
                'type': serializers.ChoiceField(
                    choices=['regenerate', 'continue'], 
                    default='regenerate',
                    help_text="`regenerate`: 此时会清空原消息内容重写; `continue`: 保留原内容，在后面续写"
                ),
                'api_key': serializers.CharField(required=False)
            }
        ),
        responses={
            200: {"description": "SSE 数据流", "content": {"text/event-stream": {}}}
        }
    )
    @action(detail=True, methods=['post'], url_path='regenerate')
    def regenerate_message(self, request, pk=None):
        session = self.get_object()
        message_id = request.data.get('message_id')
        model = request.data.get('model', 'deepseek-chat')
        action_type = request.data.get('type') 
        api_key = request.data.get('api_key') or request.headers.get('X-DeepSeek-API-Key')

        if not message_id:
            return error_response("请求体中缺少 'message_id'", status=status.HTTP_400_BAD_REQUEST)

        try:
            ai_message_to_regenerate = session.messages.get(id=message_id, sender='ai')
        except ChatMessage.DoesNotExist:
            return error_response("Not found", code=status.HTTP_404_NOT_FOUND)

        # 获取历史记录
        history = session.messages.filter(
            created_at__lte=ai_message_to_regenerate.created_at
        ).exclude(
            id=ai_message_to_regenerate.id
        ).order_by('created_at')

        history_for_api = []
        for msg in history:
            role = "assistant" if msg.sender == 'ai' else "user"
            content = msg.content
            related_files = msg.files.all()
            if related_files:
                for f in related_files:
                    if f.parsed_content:
                        content += f"\n\n--- 附件 [{f.file.name}] 内容 ---\n{f.parsed_content}\n--- 结束 ---\n"
            elif msg.parsed_content:
                content += f"\n\n--- 附件内容 ---\n{msg.parsed_content}\n----------------"
            
            if not content.strip():
                content = "[空消息或仅文件]"
            history_for_api.append({"role": role, "content": content})

        existing_content = ""
        existing_reasoning = ""
        is_continue = action_type == 'continue'

        if is_continue:
            existing_content = ai_message_to_regenerate.content or ""
            existing_reasoning = ai_message_to_regenerate.reasoning_content or ""
            if existing_content:
                history_for_api.append({"role": "assistant", "content": existing_content})
                history_for_api.append({
                    "role": "user", 
                    "content": "请接着上文的最后一句继续生成。注意：直接输出后续内容即可，绝不要重复上文已经输出的内容，也不要包含“好的”、“接着写”等客套话。"
                })

        def stream_regenerate_generator():
            full_ai_content = "" 
            full_reasoning_content = ""
            completion_status = 'interrupted'
            
            try:
                for chunk_data in get_deepseek_response_stream(history_for_api, model, api_key=api_key):
                    chunk_type = chunk_data.get("type")
                    chunk_content = chunk_data.get("content", "")
                    
                    event_data = {}
                    if chunk_type == "reasoning":
                        full_reasoning_content += chunk_content
                        event_data = {"type": "reasoning", "content": chunk_content}
                    
                    elif chunk_type == "content":
                        full_ai_content += chunk_content
                        event_data = {"type": "content", "content": chunk_content}

                    if event_data:
                        yield f"data: {json.dumps(event_data)}\n\n"

                completion_status = 'completed'

            except Exception as e:
                completion_status = 'error'
                error_data = {"event": "error", "detail": f"AI 调用失败: {str(e)}"}
                yield f"data: {json.dumps(error_data)}\n\n"
            
            finally:
                if is_continue:
                    ai_message_to_regenerate.content = existing_content + full_ai_content
                    ai_message_to_regenerate.reasoning_content = existing_reasoning + full_reasoning_content
                else:
                    ai_message_to_regenerate.content = full_ai_content
                    if hasattr(ai_message_to_regenerate, 'reasoning_content'):
                        ai_message_to_regenerate.reasoning_content = full_reasoning_content
                
                ai_message_to_regenerate.status = completion_status
                ai_message_to_regenerate.save() 

                if completion_status == 'completed':
                    serializer = ChatMessageSerializer(ai_message_to_regenerate)
                    done_data = {
                        "event": "done",
                        "message": serializer.data, 
                        "reasoning": full_reasoning_content
                    }
                    yield f"data: {json.dumps(done_data)}\n\n"

        response = StreamingHttpResponse(stream_regenerate_generator(), content_type="text/event-stream")
        response['Cache-Control'] = 'no-cache'
        return response