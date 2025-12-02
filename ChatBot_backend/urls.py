# aichat_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 将 chat 应用的路由包含进来，并添加 'api/' 前缀
    path('api/', include('apps.chat.urls')),
    
    # 将 users 应用的路由包含进来，并添加 'api/auth/' 前缀
    path('api/auth/', include('apps.users.urls')),

    # --- 接口文档路由 ---
    # 1. 下载 schema 文件 (JSON格式)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # 2. Swagger UI (最常用的界面)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # 3. Redoc UI (另一种风格，更适合阅读)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# 在开发模式下，让 Django 能够托管用户上传的媒体文件 (例如头像)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)