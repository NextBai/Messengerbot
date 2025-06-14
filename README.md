# Messenger Bot + ChatGPT 整合工具

這個專案整合了 Facebook Messenger Bot 和 OpenAI ChatGPT，讓你可以在 Messenger 上直接與 AI 聊天。

## 功能特色

- 🤖 **ChatGPT 整合**: 使用 OpenAI GPT-4o-mini 模型
- 📱 **Messenger Bot**: 完整的 Facebook Messenger 整合
- 🔄 **MCP 協議**: 遵循 MCP 協議進行 AI 功能調用
- 🚀 **即時回應**: 快速處理和回應用戶訊息
- 📝 **繁體中文**: 支援繁體中文對話
- ☁️ **Render 部署**: 一鍵部署到 Render 免費服務

## 快速部署到 Render 🚀

### 1. 上傳到 GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/NextBai/messengerbot.git
git push -u origin main
```

### 2. 部署到 Render

1. 前往 [render.com](https://render.com)
2. 用 GitHub 帳號登入
3. 點擊 "New Web Service"
4. 連接你的 GitHub 倉庫
5. 設定：
   - **Build Command**: `pip3 install -r requirements.txt`
   - **Start Command**: `python3 run.py`
6. 在環境變數中設定：
   - `FACEBOOK_PAGE_ACCESS_TOKEN`
   - `FACEBOOK_VERIFY_TOKEN`
   - `OPENAI_API_KEY`

### 3. 獲取你的 Webhook URL

部署完成後會得到：`https://你的應用名.onrender.com/webhook`

## Facebook Webhook 設定 🔧

### 重要概念
- **回呼網址**: `https://你的應用名.onrender.com/webhook`
- **驗證權杖**: 你自己設定的密碼（兩邊要一樣）

### 詳細設定步驟

1. **前往 [Facebook for Developers](https://developers.facebook.com/)**
   - 建立應用程式
   - 新增 "Messenger" 產品

2. **設定 Webhook**
   ```
   回呼網址: https://你的應用名.onrender.com/webhook
   驗證權杖: my_super_secret_verify_token_2024
   訂閱事件: messages, messaging_postbacks
   ```

3. **取得頁面存取權杖**
   - 選擇你的 Facebook 頁面
   - 產生頁面存取權杖（很長的一串）

4. **在 Render 設定環境變數**
   ```
   FACEBOOK_PAGE_ACCESS_TOKEN=EAAxxxxxx（長權杖）
   FACEBOOK_VERIFY_TOKEN=my_super_secret_verify_token_2024
   OPENAI_API_KEY=sk-xxxxx
   ```

⚠️ **重點**：`FACEBOOK_VERIFY_TOKEN` 在 Facebook 和 Render 中必須**完全一樣**！

📋 **詳細步驟請參考**: [facebook_setup.md](facebook_setup.md)

## API 端點

- `GET /` - 首頁，顯示服務狀態
- `GET /webhook` - Webhook 驗證
- `POST /webhook` - 處理 Messenger 事件
- `GET /health` - 健康檢查

## 本地開發

如果想要本地測試：

```bash
# 1. 安裝依賴套件
pip3 install -r requirements.txt

# 2. 複製並設定環境變數
cp env_example .env
# 編輯 .env 檔案填入你的 API 金鑰

# 3. 啟動應用程式
python3 run.py
```

## 注意事項

- ✅ Render 自動提供 HTTPS (Facebook 要求)
- ⚠️ 定期更新 API 金鑰和權杖
- ⚠️ 監控 OpenAI API 使用量避免超額
- ⚠️ Render 免費方案服務閒置會睡眠

## 疑難排解

### 常見問題

1. **Webhook 驗證失敗**
   - 檢查 Render 環境變數中的 `FACEBOOK_VERIFY_TOKEN`
   - 確認 Render 服務正在運行

2. **訊息發送失敗**
   - 檢查 `FACEBOOK_PAGE_ACCESS_TOKEN` 權限
   - 確認 Facebook 頁面已連結到應用程式

3. **ChatGPT 回應錯誤**
   - 檢查 `OPENAI_API_KEY` 是否有效
   - 確認 API 配額是否足夠

4. **Render 服務睡眠**
   - 免費方案閒置 15 分鐘會睡眠
   - 第一次喚醒可能需要 30 秒

## 開始使用

現在就去 Render 部署你的機器人吧！ 🤖✨ 