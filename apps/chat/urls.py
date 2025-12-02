# apps/chat/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatSessionViewSet,DeepSeekViewSet

router = DefaultRouter()
router.register(r'sessions', ChatSessionViewSet, basename='session')
router.register(r'deepseek', DeepSeekViewSet, basename='deepseek')
urlpatterns = [
    path('', include(router.urls)),
]