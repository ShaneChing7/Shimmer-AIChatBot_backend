from rest_framework.response import Response
from rest_framework import status

def success_response(data=None, message="请求成功", code=200):
    """
    成功返回的统一格式
    """
    return Response({
        "code": code,
        "message": message,
        "data": data
    }, status=status.HTTP_200_OK)

def error_response(message="请求失败", code=400, status_code=status.HTTP_400_BAD_REQUEST):
    """
    失败返回的统一格式
    """
    return Response({
        "code": code,
        "message": message,
        "data": None
    }, status=status_code)
