from rest_framework.response import Response

def success_response(data=None, message="成功", code=200):
    """
    统一成功响应格式
    """
    return Response({
        "code": code,
        "message": message,
        "data": data
    }, status=code)


def error_response(message="失败", code=400, data=None):
    """
    统一错误响应格式
    """
    return Response({
        "code": code,
        "message": message,
        "data": data
    }, status=code)
