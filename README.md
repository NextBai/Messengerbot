# Messenger Bot for Render

這是一個可以部署到 Render 的 Facebook Messenger Bot 專案。

## 功能特色

- ✅ 支援基本訊息回應
- ✅ 處理 Webhook 驗證
- ✅ 支援快速回覆和按鈕互動
- ✅ 可直接部署到 Render

## 快速部署到 Render

### 1. 準備 Facebook 應用程式

1. 前往 [Facebook Developers](https://developers.facebook.com/)
2. 建立新應用程式，選擇「其他」→「商業」
3. 新增「Messenger」產品
4. 在 Messenger 設定中：
   - 建立或選擇一個 Facebook 專頁
   - 生成「頁面存取權杖」(PAGE_ACCESS_TOKEN)

### 2. 部署到 Render

1. Fork 這個專案到你的 GitHub
2. 前往 [Render](https://render.com/)，建立新的 Web Service
3. 連接你的 GitHub repository
4. 設定環境變數：
   ```
   VERIFY_TOKEN=你設定的驗證Token（自己決定一組密碼）
   PAGE_ACCESS_TOKEN=從Facebook取得的頁面存取權杖
   ```
5. 部署完成後，你會得到一個 URL，例如：`https://your-app.onrender.com`

### 3. 設定 Webhook

1. 回到 Facebook Messenger 設定頁面
2. 在「Webhooks」部分：
   - Callback URL: `https://your-app.onrender.com/webhook`
   - Verify Token: 輸入你在 Render 設定的 `VERIFY_TOKEN`
   - 勾選：`messages`, `messaging_postbacks`
3. 點擊「驗證並儲存」

### 4. 測試 Bot

1. 前往你的 Facebook 專頁
2. 點擊「訊息」按鈕開始對話
3. 試試發送：
   - "你好" 或 "hello"
   - "幫助" 或 "help" 
   - "時間"

## 本機開發

```bash
# 1. 複製專案
git clone <你的repository>
cd messenger-bot

# 2. 安裝套件
pip install -r requirements.txt

# 3. 設定環境變數 (參考 env_example.txt)
export VERIFY_TOKEN=your_verify_token
export PAGE_ACCESS_TOKEN=your_page_access_token

# 4. 執行
python3 app.py
```

## 檔案結構

```
├── app.py              # 主要應用程式
├── requirements.txt    # Python 套件依賴
├── Procfile           # Render 部署配置
├── env_example.txt    # 環境變數範例
└── README.md          # 說明文件
```

## 自訂回應邏輯

編輯 `app.py` 中的 `handle_message()` 函數來客製化你的 Bot 回應邏輯。

## 故障排除

- **Webhook 驗證失敗**：檢查 `VERIFY_TOKEN` 是否一致
- **Bot 不回應**：檢查 `PAGE_ACCESS_TOKEN` 是否正確
- **部署失敗**：檢查 `requirements.txt` 和 `Procfile` 格式

完成！你的 Messenger Bot 現在應該可以正常運作了 🚀 