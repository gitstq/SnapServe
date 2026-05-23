<p align="center">
  <h1 align="center">📸 SnapServe</h1>
  <p align="center">
    <strong>轻量级自托管网页截图 & PDF & OG图片 API 服务</strong><br>
    Zero external dependencies · Pure Python + Playwright · One-command deployment
  </p>
  <p align="center">
    <a href="#简体中文--chinese-simplified">简体中文</a> ·
    <a href="#繁體中文--chinese-traditional">繁體中文</a> ·
    <a href="#english">English</a>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-0.104+-green.svg" alt="FastAPI">
    <img src="https://img.shields.io/badge/Playwright-1.40+-purple.svg" alt="Playwright">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT">
    <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen.svg" alt="PRs Welcome">
  </p>
</p>

---

## 简体中文 🇨🇳

### 🎉 项目介绍

**SnapServe** 是一款轻量级的自托管网页截图、PDF生成和OG图片生成API服务。灵感来源于开发者对网页截图API的强烈需求——现有商业服务（ScreenshotOne、Urlbox等）收费昂贵，而开源方案往往依赖PostgreSQL、Redis等外部服务，部署门槛高。

**SnapServe 的核心差异化亮点：**

- 🚫 **零外部依赖**：无需PostgreSQL、Redis、RabbitMQ等外部服务，纯Python实现
- ⚡ **一键部署**：单条命令即可启动服务，Docker也支持
- 🎯 **功能完整**：截图、PDF、OG图片、批量处理、元素截图全覆盖
- 🔐 **安全可靠**：内置API Key认证、速率限制、主机黑名单
- 🎨 **6种OG主题**：内置深色、浅色、蓝、绿、橙、日落渐变主题
- 📦 **轻量架构**：浏览器连接池管理，内存级任务队列，SQLite存储

### ✨ 核心特性

- 📸 **网页截图**：支持全页面截图、自定义视口、暗黑模式、广告拦截、元素隐藏/移除
- 🎯 **元素截图**：精准定位页面元素进行截图，支持自定义内边距
- 📄 **PDF生成**：URL转PDF、HTML转PDF，支持自定义纸张、边距、缩放、页码范围
- 🖼️ **OG图片生成**：6种精美渐变主题，支持自定义模板，也可从URL直接生成
- 🔄 **批量处理**：单次请求最多50个混合任务并发处理
- 🔐 **API Key认证**：可选的API密钥认证，支持Header和Query参数传递
- ⏱️ **速率限制**：内置滑动窗口速率限制器，防止滥用
- 🧹 **自动清理**：可配置的文件自动过期清理机制
- 📊 **Swagger文档**：自动生成交互式API文档（`/docs`）

### 🚀 快速开始

**环境要求：**
- Python 3.10+
- Chromium浏览器（通过Playwright安装）

**安装步骤：**

```bash
# 1. 克隆仓库
git clone https://github.com/gitstq/SnapServe.git
cd SnapServe

# 2. 安装依赖
pip install -e .

# 3. 安装浏览器
snapserve --install-browser

# 4. 启动服务
snapserve
```

**Docker部署：**

```bash
docker build -t snapserve .
docker run -p 8199:8199 snapserve
```

**带API Key启动：**

```bash
snapserve --api-key your-secret-key --port 8080
```

服务启动后访问 `http://localhost:8199/docs` 查看交互式API文档。

### 📖 详细使用指南

#### 截图示例

```bash
# 基础截图
curl -X POST http://localhost:8199/api/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "full_page": true, "format": "png"}' \
  --output screenshot.png

# 暗黑模式 + 广告拦截
curl -X POST http://localhost:8199/api/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "dark_mode": true, "no_ads": true, "width": 1920, "height": 1080}' \
  --output dark.png

# 元素截图
curl -X POST http://localhost:8199/api/screenshot/element \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "selector": "header", "padding": 10}' \
  --output element.png
```

#### PDF生成示例

```bash
# URL转PDF
curl -X POST http://localhost:8199/api/pdf \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "format": "A4", "landscape": false}' \
  --output page.pdf

# HTML转PDF
curl -X POST http://localhost:8199/api/pdf/html \
  -H "Content-Type: application/json" \
  -d '{"html": "<h1>Hello World</h1><p>This is a test.</p>"}' \
  --output from_html.pdf
```

#### OG图片生成示例

```bash
# 使用主题生成OG图片
curl -X POST http://localhost:8199/api/og-image \
  -H "Content-Type: application/json" \
  -d '{"title": "SnapServe", "description": "轻量级截图API服务", "theme": "blue", "badge": "v1.0"}' \
  --output og.png

# 快速生成（无需浏览器）
curl "http://localhost:8199/api/og-image/simple?title=Hello&theme=green" \
  --output simple_og.png
```

#### 批量处理示例

```bash
curl -X POST http://localhost:8199/api/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"type": "screenshot", "url": "https://github.com"},
      {"type": "pdf", "url": "https://example.com"},
      {"type": "og_image", "title": "Batch Test", "theme": "sunset"}
    ]
  }'
```

### 💡 设计思路与迭代规划

**设计理念：**
- **极简主义**：不依赖任何外部数据库或消息队列，降低部署门槛
- **异步优先**：全异步架构，基于FastAPI + asyncio，高并发性能
- **安全内置**：认证、限流、主机黑名单等安全功能开箱即用

**技术选型原因：**
- **FastAPI**：高性能异步框架，自动生成API文档
- **Playwright**：最稳定的无头浏览器自动化库，支持Chromium
- **SQLite**：零配置嵌入式数据库，用于任务存储
- **Pillow**：纯Python图像处理，OG图片生成的轻量级备选方案

**后续迭代计划：**
- [ ] Webhook回调通知
- [ ] 视觉回归测试（像素级Diff对比）
- [ ] 签名URL（HMAC签名，安全嵌入HTML）
- [ ] Prometheus指标 + Grafana仪表盘
- [ ] 更多OG图片模板
- [ ] 视频录制功能

### 📦 打包与部署指南

**环境变量配置：**

复制 `.env.example` 为 `.env` 并按需修改：

```bash
SNAPSERVE_HOST=0.0.0.0
SNAPSERVE_PORT=8199
SNAPSERVE_API_KEY=your-secret-key
SNAPSERVE_OUTPUT_DIR=./snapserve_output
SNAPSERVE_CONCURRENT_BROWSERS=5
```

**兼容环境：**
- Python 3.10+
- Linux / macOS / Windows
- Docker

### 🤝 贡献指南

欢迎社区贡献！请遵循以下规范：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

提交规范遵循 Angular Convention：`feat:` / `fix:` / `docs:` / `refactor:` / `test:`

### 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

---

## 繁體中文 🇭🇰

### 🎉 專案介紹

**SnapServe** 是一款輕量級的自託管網頁截圖、PDF生成和OG圖片生成API服務。靈感來自於開發者對網頁截圖API的強烈需求——現有商業服務收費昂貴，而開源方案往往依賴PostgreSQL、Redis等外部服務，部署門檻高。

**SnapServe 的核心差異化亮點：**

- 🚫 **零外部依賴**：無需PostgreSQL、Redis、RabbitMQ等外部服務，純Python實現
- ⚡ **一鍵部署**：單條命令即可啟動服務，Docker也支援
- 🎯 **功能完整**：截圖、PDF、OG圖片、批次處理、元素截圖全覆蓋
- 🔐 **安全可靠**：內建API Key認證、速率限制、主機黑名單
- 🎨 **6種OG主題**：內建深色、淺色、藍、綠、橙、日落漸層主題
- 📦 **輕量架構**：瀏覽器連接池管理，記憶體級任務佇列

### ✨ 核心特性

- 📸 **網頁截圖**：支援全頁面截圖、自訂視窗、暗黑模式、廣告攔截、元素隱藏/移除
- 🎯 **元素截圖**：精準定位頁面元素進行截圖，支援自訂內邊距
- 📄 **PDF生成**：URL轉PDF、HTML轉PDF，支援自訂紙張、邊距、縮放、頁碼範圍
- 🖼️ **OG圖片生成**：6種精美漸層主題，支援自訂範本
- 🔄 **批次處理**：單次請求最多50個混合任務並發處理
- 🔐 **API Key認證**：可選的API金鑰認證
- ⏱️ **速率限制**：內建滑動視窗速率限制器
- 🧹 **自動清理**：可配置的檔案自動過期清理機制
- 📊 **Swagger文件**：自動生成交互式API文件

### 🚀 快速開始

**環境要求：**
- Python 3.10+
- Chromium瀏覽器（透過Playwright安裝）

**安裝步驟：**

```bash
# 1. 克隆倉庫
git clone https://github.com/gitstq/SnapServe.git
cd SnapServe

# 2. 安裝依賴
pip install -e .

# 3. 安裝瀏覽器
snapserve --install-browser

# 4. 啟動服務
snapserve
```

**Docker部署：**

```bash
docker build -t snapserve .
docker run -p 8199:8199 snapserve
```

服務啟動後訪問 `http://localhost:8199/docs` 查看交互式API文件。

### 📖 詳細使用指南

#### 截圖範例

```bash
# 基礎截圖
curl -X POST http://localhost:8199/api/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "full_page": true, "format": "png"}' \
  --output screenshot.png

# 暗黑模式 + 廣告攔截
curl -X POST http://localhost:8199/api/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "dark_mode": true, "no_ads": true, "width": 1920}' \
  --output dark.png
```

#### PDF生成範例

```bash
# URL轉PDF
curl -X POST http://localhost:8199/api/pdf \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "format": "A4"}' \
  --output page.pdf
```

#### OG圖片生成範例

```bash
# 使用主題生成OG圖片
curl -X POST http://localhost:8199/api/og-image \
  -H "Content-Type: application/json" \
  -d '{"title": "SnapServe", "description": "輕量級截圖API服務", "theme": "blue"}' \
  --output og.png
```

### 💡 設計思路與迭代規劃

**設計理念：**
- **極簡主義**：不依賴任何外部資料庫或訊息佇列
- **非同步優先**：全非同步架構，高並發效能
- **安全內建**：認證、限流、主機黑名單等安全功能開箱即用

**後續迭代計畫：**
- [ ] Webhook回呼通知
- [ ] 視覺回歸測試
- [ ] 簽名URL
- [ ] Prometheus指標
- [ ] 影片錄製功能

### 🤝 貢獻指南

1. Fork 本倉庫
2. 建立特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 建立 Pull Request

### 📄 開源協議

本專案基於 [MIT License](LICENSE) 開源。

---

## English 🇺🇸

### 🎉 Introduction

**SnapServe** is a lightweight self-hosted web screenshot, PDF generation, and OG image generation API service. Inspired by the strong demand for web screenshot APIs — existing commercial services (ScreenshotOne, Urlbox, etc.) are expensive, while open-source solutions often depend on PostgreSQL, Redis, and other external services with high deployment barriers.

**Key Differentiators:**

- 🚫 **Zero External Dependencies**: No PostgreSQL, Redis, or RabbitMQ needed — pure Python
- ⚡ **One-Command Deployment**: Start the service with a single command, Docker supported
- 🎯 **Full-Featured**: Screenshots, PDFs, OG images, batch processing, element capture
- 🔐 **Secure by Default**: Built-in API Key auth, rate limiting, host blacklist
- 🎨 **6 OG Themes**: Dark, Light, Blue, Green, Orange, Sunset gradient themes
- 📦 **Lightweight Architecture**: Browser connection pooling, in-memory task queue

### ✨ Core Features

- 📸 **Web Screenshots**: Full page capture, custom viewport, dark mode, ad blocking, element hide/remove
- 🎯 **Element Screenshots**: Precisely capture specific page elements with custom padding
- 📄 **PDF Generation**: URL-to-PDF, HTML-to-PDF with custom paper, margins, scale, page ranges
- 🖼️ **OG Image Generation**: 6 beautiful gradient themes, custom template support
- 🔄 **Batch Processing**: Up to 50 mixed tasks per request with concurrent execution
- 🔐 **API Key Authentication**: Optional API key auth via Header or Query parameter
- ⏱️ **Rate Limiting**: Built-in sliding window rate limiter to prevent abuse
- 🧹 **Auto Cleanup**: Configurable file expiration and cleanup mechanism
- 📊 **Swagger Docs**: Auto-generated interactive API documentation (`/docs`)

### 🚀 Quick Start

**Requirements:**
- Python 3.10+
- Chromium browser (installed via Playwright)

**Installation:**

```bash
# 1. Clone the repository
git clone https://github.com/gitstq/SnapServe.git
cd SnapServe

# 2. Install dependencies
pip install -e .

# 3. Install browser
snapserve --install-browser

# 4. Start the service
snapserve
```

**Docker Deployment:**

```bash
docker build -t snapserve .
docker run -p 8199:8199 snapserve
```

**With API Key:**

```bash
snapserve --api-key your-secret-key --port 8080
```

Visit `http://localhost:8199/docs` for interactive API documentation after starting.

### 📖 Usage Guide

#### Screenshot Examples

```bash
# Basic screenshot
curl -X POST http://localhost:8199/api/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "full_page": true, "format": "png"}' \
  --output screenshot.png

# Dark mode + ad blocking
curl -X POST http://localhost:8199/api/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "dark_mode": true, "no_ads": true, "width": 1920, "height": 1080}' \
  --output dark.png

# Element screenshot
curl -X POST http://localhost:8199/api/screenshot/element \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "selector": "header", "padding": 10}' \
  --output element.png
```

#### PDF Generation Examples

```bash
# URL to PDF
curl -X POST http://localhost:8199/api/pdf \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "format": "A4", "landscape": false}' \
  --output page.pdf

# HTML to PDF
curl -X POST http://localhost:8199/api/pdf/html \
  -H "Content-Type: application/json" \
  -d '{"html": "<h1>Hello World</h1><p>This is a test.</p>"}' \
  --output from_html.pdf
```

#### OG Image Generation Examples

```bash
# Generate with theme
curl -X POST http://localhost:8199/api/og-image \
  -H "Content-Type: application/json" \
  -d '{"title": "SnapServe", "description": "Lightweight Screenshot API", "theme": "blue", "badge": "v1.0"}' \
  --output og.png

# Quick generation (no browser needed)
curl "http://localhost:8199/api/og-image/simple?title=Hello&theme=green" \
  --output simple_og.png
```

#### Batch Processing Examples

```bash
curl -X POST http://localhost:8199/api/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"type": "screenshot", "url": "https://github.com"},
      {"type": "pdf", "url": "https://example.com"},
      {"type": "og_image", "title": "Batch Test", "theme": "sunset"}
    ]
  }'
```

### 💡 Design Philosophy & Roadmap

**Design Principles:**
- **Minimalism**: No external databases or message queues required
- **Async-First**: Fully async architecture with FastAPI + asyncio
- **Security Built-in**: Auth, rate limiting, host blacklist out of the box

**Technology Choices:**
- **FastAPI**: High-performance async framework with auto-generated API docs
- **Playwright**: Most reliable headless browser automation library
- **SQLite**: Zero-config embedded database for task storage
- **Pillow**: Pure Python image processing for lightweight OG image generation

**Roadmap:**
- [ ] Webhook callback notifications
- [ ] Visual regression testing (pixel-level diff comparison)
- [ ] Signed URLs (HMAC signing for secure HTML embedding)
- [ ] Prometheus metrics + Grafana dashboard
- [ ] More OG image templates
- [ ] Video recording capability

### 📦 Deployment Guide

**Environment Variables:**

Copy `.env.example` to `.env` and customize:

```bash
SNAPSERVE_HOST=0.0.0.0
SNAPSERVE_PORT=8199
SNAPSERVE_API_KEY=your-secret-key
SNAPSERVE_OUTPUT_DIR=./snapserve_output
SNAPSERVE_CONCURRENT_BROWSERS=5
```

**Compatible Environments:**
- Python 3.10+
- Linux / macOS / Windows
- Docker

### 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

Commit convention follows Angular Convention: `feat:` / `fix:` / `docs:` / `refactor:` / `test:`

### 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>
