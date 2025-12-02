# apps/chat/services.py
import json
import requests
import os
import pytesseract
import pdfplumber
from PIL import Image
from django.conf import settings
# 手动指定 Tesseract 的路径
pytesseract.pytesseract.tesseract_cmd = r"E:\Tesseract-OCR\tesseract.exe"

# ------------------------------------------------------------------
# 配置 Tesseract OCR 路径 (从 settings 读取)
# ------------------------------------------------------------------
tesseract_cmd_path = getattr(settings, "TESSERACT_CMD", None)
if tesseract_cmd_path:
    # 只有当 settings 中配置了路径时才设置
    # 这兼容了 Linux 环境（通常在 PATH 中，无需指定）
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path

# 获取 API Key 配置
DEEPSEEK_API_KEY = getattr(settings, "DEEPSEEK_API_KEY", None)
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_BALANCE_URL = "https://api.deepseek.com/user/balance"

# ------------------------------------------------------------------
# 辅助函数：API Key 获取逻辑
# ------------------------------------------------------------------
def get_api_key(provided_key=None):
    """
    获取有效的 API Key。
    1. 优先使用前端请求中携带的 provided_key (用户自定义 Key)。
    2. 如果未提供，则使用后端 Settings 中配置的全局 DEEPSEEK_API_KEY。
    3. 如果都没有，抛出异常。
    """
    if provided_key and provided_key.strip():
        return provided_key.strip()
    
    if DEEPSEEK_API_KEY:
        return DEEPSEEK_API_KEY
        
    raise ValueError("未提供 DeepSeek API Key，且后端未配置默认 Key")

# ------------------------------------------------------------------
# OCR 与 文档解析服务
# ------------------------------------------------------------------

def extract_text_from_file(file_path):
    """
    根据文件扩展名自动选择解析方法
    支持: .png, .jpg, .jpeg, .pdf, .txt, .md
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext in ['.png', '.jpg', '.jpeg', '.bmp']:
            return _ocr_image(file_path)
        elif ext == '.pdf':
            return _extract_pdf(file_path)
        elif ext in ['.txt', '.md', '.py', '.js', '.json', '.html']:
            return _read_text_file(file_path)
        else:
            return f"[系统提示: 不支持的文件格式 {ext}，仅作为附件上传]"
    except Exception as e:
        return f"[系统提示: 文件解析失败 - {str(e)}]"

def _ocr_image(image_path):
    """使用 Tesseract 进行图片 OCR"""
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        return text.strip() if text.strip() else "[OCR提示: 未识别到文字]"
    except Exception as e:
        raise Exception(f"OCR 识别错误: {str(e)}")

def _extract_pdf(pdf_path):
    """使用 pdfplumber 提取 PDF 文本"""
    text_content = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
    return "\n".join(text_content) if text_content else "[PDF提示: 未提取到文本，可能是纯图片PDF]"

def _read_text_file(file_path):
    """读取普通文本文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# ------------------------------------------------------------------
# DeepSeek 服务
# ------------------------------------------------------------------

def check_deepseek_balance(api_key):
    """
    透传查询 DeepSeek 账户余额。
    前端传入 API Key，后端仅做转发请求，不存储 Key。
    """
    if not api_key:
         raise ValueError("查询余额需要提供 API Key")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    try:
        # 尝试调用余额接口
        response = requests.get(DEEPSEEK_BALANCE_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise Exception("API Key 无效或已过期")
        else:
             # 如果余额接口不可用，尝试访问 Models 接口验证 Key 是否有效作为 Fallback
             models_url = "https://api.deepseek.com/models"
             model_resp = requests.get(models_url, headers=headers, timeout=5)
             if model_resp.status_code == 200:
                 # Key 有效但无法获取余额
                 return {
                     "is_available": True, 
                     "balance_infos": [{"currency": "CNY", "total_balance": "未知(接口限制)"}],
                     "note": "Key有效，但无法获取精确余额"
                 }
             
             raise Exception(f"DeepSeek API Error: {response.status_code} - {response.text}")
             
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求失败: {str(e)}")

def get_deepseek_response(messages, api_key=None):
    """
    调用 DeepSeek API 获取回复。
    :param messages: 消息列表
    :param api_key: (Optional) 用户自定义的 API Key
    """
    final_key = get_api_key(api_key)

    headers = {
        "Authorization": f"Bearer {final_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": messages
    }

    response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=60)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

def get_deepseek_response_stream(messages, model="deepseek-chat", api_key=None):
    """
    调用 DeepSeek API 获取流式回复。
    :param messages: 消息历史
    :param model: 要使用的模型
    :param api_key: (Optional) 用户自定义的 API Key
    """
    final_key = get_api_key(api_key)

    headers = {
        "Authorization": f"Bearer {final_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "stream": True
    }

    response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=60, stream=True)

    if response.status_code != 200:
        error_detail = f"{response.status_code} {response.reason} - {response.text[:200]}"
        raise Exception(error_detail)

    # 处理流
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            
            if decoded_line.startswith('data: '):
                data_str = decoded_line[len('data: '):].strip()
                
                if data_str == '[DONE]':
                    break
                
                try:
                    data_json = json.loads(data_str)
                    if not data_json.get('choices'):
                        continue
                        
                    delta = data_json['choices'][0].get('delta', {})
                    
                    # 处理推理内容 (deepseek-reasoner 特有)
                    reasoning_chunk = delta.get('reasoning_content')
                    if reasoning_chunk:
                        yield {
                            "type": "reasoning",
                            "content": reasoning_chunk
                        }
                    
                    # 处理正常回复内容
                    content_chunk = delta.get('content')
                    if content_chunk:
                        yield {
                            "type": "content",
                            "content": content_chunk
                        }
                        
                except json.JSONDecodeError:
                    pass