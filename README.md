<div align="center"> <img src="./public/logo.svg" alt="Shimmer AI ChatBot Logo" width="220" height="220" /> </div>

<h1 align="center">Shimmer AI ChatBot - Backend</h1>

<p align="center">
  <a href="https://www.djangoproject.com/">
    <img src="https://img.shields.io/badge/Django-5.0+-092E20?style=flat-square&logo=django" alt="Django" />
  </a>
  <a href="https://www.django-rest-framework.org/">
    <img src="https://img.shields.io/badge/DRF-3.14-A30000?style=flat-square&logo=django" alt="DRF" />
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python" alt="Python" />
  </a>
  <a href="https://www.mysql.com/">
    <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql" alt="MySQL" />
  </a>
  <a href="https://platform.deepseek.com/">
    <img src="https://img.shields.io/badge/DeepSeek-Integration-blue?style=flat-square" alt="DeepSeek" />
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License" />
  </a>
</p>


<p align="center"> 基于 Django REST Framework 构建，深度集成 DeepSeek 大模型能力，提供流式响应 (SSE)、多模态文件解析 (OCR/PDF) 及企业级权限管理体系。 </p>

## 📖 简介 | Introduction

本项目是 **Shimmer AIChatBot** 的后端服务，旨在为前端提供稳定、高效的数据接口与 AI 交互能力。

区别于传统的 CRUD 后端，本项目重度优化了 **LLM 交互体验**，实现了类似 OpenAI 的流式输出协议，并内置了强大的**文档解析引擎**，让 AI 能够“看懂”用户上传的图片与文档。同时，项目采用标准的 **OpenAPI 3.0** 规范，自动生成可交互的接口文档。

## 🚀 核心功能 | Features

### 🧠 深度 AI 编排 (DeepSeek Native)

- **SSE 流式响应**：基于 `StreamingHttpResponse` 实现 Server-Sent Events，支持毫秒级字符推送，完美适配打字机效果。
- **思维链透传**：完整支持 DeepSeek R1 (Reasoner) 模型，能够分离 `reasoning_content` (思考过程) 与最终回复。
- **上下文管理**：智能维护会话历史，支持“**重新生成**”与“**继续生成**” (Continue) 等高级指令。

### 👁️ 多模态文件解析 (Multi-modal)

后端内置了强大的 ETL 管道，能够将非结构化数据转化为 AI 可理解的文本：

- **OCR 文字识别**：集成 `Tesseract-OCR` 引擎，自动提取 **JPG/PNG** 图片中的文字信息。
- **文档解析**：基于 `pdfplumber` 精准解析 **PDF** 文档内容。
- **代码/文本读取**：原生支持 `.py`, `.js`, `.md`, `.txt` 等代码文件的解析与注入。

### 🔐 企业级用户体系

- **JWT 认证**：基于 `SimpleJWT` 的无状态认证机制，支持 Token 自动刷新与黑名单。
- **自定义用户模型**：使用 8 位随机 UID 替代传统自增 ID，提升安全性。
- **头像引擎**：支持头像上传、自动压缩 (Pillow)、格式校验及旧文件自动清理。

## 🛠 技术栈 | Tech Stack

- **核心框架**: [Django 5.x](https://www.djangoproject.com/) + [Django REST Framework](https://www.django-rest-framework.org/)
- **数据库**: MySQL 8.0+
- **认证鉴权**: SimpleJWT (Access/Refresh Token)
- **AI 交互**: Requests + SSE (Server-Sent Events)
- **文档处理**:
  - `pytesseract` (OCR 引擎)
  - `pdfplumber` (PDF 解析)
  - `Pillow` (图像处理)
- **API 文档**: `drf-spectacular` (Swagger/Redoc)
- **配置管理**: `python-dotenv`

## 📂 项目结构 | Project Structure

```
ChatBot_backend/
├── apps/
│   ├── chat/           # 核心聊天模块 (DeepSeek集成, 会话管理, OCR服务)
│   └── users/          # 用户模块 (JWT认证, 个人中心, 头像处理)
├── ChatBot_backend/    # 项目核心配置 (Settings, URL路由)
├── media/              # 用户上传文件存储 (头像, 聊天附件)
├── .env                # [重要] 环境变量配置文件 (勿提交)
├── manage.py           # Django 命令行入口
└── requirements.txt    # 依赖列表
```

## 🏁 快速开始 | Getting Started

### 环境要求

- Python >= 3.10
- MySQL >= 8.0
- **Tesseract-OCR** (必须安装，用于图片识别)
  - [Windows 下载](https://www-d-google-d-com-s-gmn.tga.wuaicha.cc/search?q=https://github.com/UB-Mannheim/tesseract/wiki)
  - Linux: `sudo apt-get install tesseract-ocr`

### 1. 克隆项目

```
git clone [https://github.com/ShaneChing7/ChatBot_backend.git](https://github.com/ShaneChing7/ChatBot_backend.git)
cd ChatBot_backend
```

### 2. 环境配置 (Critical)

在项目根目录创建 `.env` 文件（**不要**直接修改 `settings.py`），填入你的本地配置：

```
# .env 示例配置

# 核心安全
SECRET_KEY=your-secret-key
DEBUG=True

# 数据库
DB_NAME=aichat_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306

# AI 服务 (必填)
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# OCR 引擎路径 (Windows 必填，Linux 通常留空)
TESSERACT_CMD=E:/Tesseract-OCR/tesseract.exe
```

### 3. 创建并激活虚拟环境

```
# 创建虚拟环境
python -m venv venv
# 激活 (Windows)
venv\Scripts\activate
# 激活 (Mac/Linux)
source venv/bin/activate
```

### 4. 安装依赖

```
pip install -r requirements.txt
```

### 5. 数据库初始化

```
# 请确保 MySQL 中已创建 aichat_db 数据库 (utf8mb4)
# 生成迁移文件
python manage.py makemigrations
# 执行迁移
python manage.py migrate
# 创建超级管理员 (可选)
python manage.py createsuperuser
```

### 6. 启动服务

```
python manage.py runserver
```

后端服务将在 `http://127.0.0.1:8000` 启动。

## 📖 接口文档 | API Documentation

项目集成了 Swagger UI，启动服务后访问：

- **Swagger UI (交互式)**: http://127.0.0.1:8000/api/docs/
- **ReDoc (阅读模式)**: [http://127.0.0.1:8000/api/redoc/](https://www-d-google-d-com-s-gmn.tga.wuaicha.cc/search?q=http://127.0.0.1:8000/api/redoc/)

<div align="center"> <img src="https://www-d-google-d-com-s-gmn.tga.wuaicha.cc/search?q=https://drf-spectacular.readthedocs.io/en/latest/_images/swagger_ui.png" alt="Swagger UI" width="90%" /> </div>

## ⚙️ 常见问题 | FAQ

**Q: 上传图片时提示 "OCR Engine not found"?** 

A: 请检查 `.env` 文件中的 `TESSERACT_CMD` 路径是否正确指向了 `tesseract.exe` 可执行文件。

**Q: DeepSeek 余额查询失败？** 

A: 确保你的 API Key 有效。余额查询是透传请求，如果官方接口变动或 Key 欠费，可能会导致查询失败。

**Q: 跨域问题 (CORS)?** 

A: `settings.py` 已默认放行 `localhost:5173` 和 `5174`。如前端端口不同，请在 `.env` 或 `settings.py` 中添加。

## 🤝 贡献 | Contributing

欢迎提交 Pull Request 或 Issue 共同改进！

## 📄 许可证 | License

本项目遵循 [MIT License](https://www-d-google-d-com-s-gmn.tga.wuaicha.cc/search?q=LICENSE) 许可证。

Designed with ❤️ by [Shane](https://github.com/ShaneChing7)