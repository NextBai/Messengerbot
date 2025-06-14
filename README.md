# Messenger Bot + ChatGPT + 動態手語辨識整合系統

這個專案整合了 Facebook Messenger Bot、OpenAI ChatGPT 和先進的動態適應性手語辨識系統，讓你可以在 Messenger 上透過文字聊天或上傳手語影片與 AI 互動。

## ✨ 功能特色

- 🤖 **ChatGPT 整合**: 使用 OpenAI GPT-4o-mini 模型進行自然對話
- 📱 **Messenger Bot**: 完整的 Facebook Messenger 整合，支援多媒體訊息
- 🔄 **MCP 協議**: 遵循 MCP 協議進行 AI 功能調用
- 🤟 **動態手語辨識**: AI 手語辨識 + ChatGPT 智慧句子生成
- 🎯 **適應性處理**: 自動判断影片中的手語詞彙數量並調整辨識策略
- 🚀 **即時回應**: 快速處理和回應用戶訊息
- 📝 **繁體中文**: 支援繁體中文對話
- ☁️ **Render 部署**: 一鍵部署到 Render 免費服務

## 🤟 動態適應性手語辨識系統

### 🧠 核心技術

我們的手語辨識系統採用**三階段動態適應性處理**，能夠智慧地處理 1-6 個手語詞彙的各種組合：

#### 🔍 階段一：快速活動分析
- **快速掃描**：每 5 幀取樣進行快速影片分析
- **活動強度計算**：分析每 2 秒區段的手語活動強度
- **詞彙數量估算**：根據高活動區段數量估算 1-6 個詞彙

#### ⚙️ 階段二：動態參數調整
根據估算的詞彙數量，自動調整辨識策略：

- **單詞模式** (1 個詞彙)：
  - 高穩定性閾值（8 次確認）
  - 長暫停檢測（20 幀）
  - 低信心閾值（0.55）
  - 適用：慢速、重複性動作

- **平衡模式** (2-3 個詞彙)：
  - 中等穩定性（5-6 次確認）
  - 中等暫停檢測（12-13 幀）
  - 標準信心閾值（0.65）
  - 適用：正常節奏的手語

- **多詞模式** (4+ 個詞彙)：
  - 快速回應（3 次確認）
  - 短暫停檢測（5 幀）
  - 高信心閾值（0.80）
  - 適用：快速、連續的手語動作

#### 🎯 階段三：精確辨識
- **投票機制**：累積信心分數確保準確性
- **智慧分段**：自動檢測不同手語動作間的間隔
- **時間戳記錄**：記錄每個詞彙的時間位置
- **GPT 增強**：將辨識的詞彙序列組成自然句子

### 🔤 支援的手語詞彙
- **eat** (吃) 🍽️
- **fish** (魚) 🐟
- **like** (喜歡) ❤️
- **want** (想要) 🙋‍♀️

### 📱 使用範例

**單詞重複**：
```
用戶影片: [慢速重複：吃-吃-吃]
系統判斷: 單詞模式，高穩定性策略
回應結果: 
🤟 手語辨識完成！
🔤 辨識到的手語詞彙：eat
📝 完整句子：我想吃東西
📊 共辨識出 1 個手語詞彙
```

**多詞組合**：
```
用戶影片: [快速連續：我-喜歡-吃-魚]
系統判斷: 多詞模式，快速回應策略
回應結果:
🤟 手語辨識完成！
🔤 辨識到的手語詞彙：like, eat, fish
📝 完整句子：我喜歡吃魚
📊 共辨識出 3 個手語詞彙
```

## 🏗️ 系統架構

### 📊 完整工作流程
```
1. 用戶發送訊息到 Messenger
      ↓
2. Facebook 轉發到 /webhook 端點
      ↓
3. app.py 解析訊息類型
      ↓
4a. 文字訊息 → ChatGPT → 回應用戶
4b. 影片訊息 → 手語辨識 → GPT 組句 → 回應用戶
```

### 🔧 技術棧
- **後端**: Flask + Python 3
- **AI 模型**: PyTorch LSTM + Attention Mechanism  
- **影像處理**: OpenCV + MediaPipe
- **特徵提取**: 21個手部關鍵點 × 2維座標 = 42維特徵向量
- **自然語言處理**: OpenAI GPT-4o-mini
- **部署**: Render Cloud Platform

### 📁 專案結構
```
Messenger-bot測試/
├── app.py                          # 主應用程式
├── sign_language_processor.py      # 動態手語辨識處理器
├── video_processor.py              # 影片處理器
├── config.py                       # 配置檔
├── run.py                          # 啟動腳本
├── requirements.txt                # Python 依賴套件
├── labels.csv                      # 手語標籤映射
├── models/
│   └── sign_language_model.pth     # 預訓練手語辨識模型
├── test_architecture.py            # 系統架構驗證腳本
└── facebook_setup.md               # Facebook 設定指南
```

## 🚀 快速部署到 Render

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

## 🔧 Facebook Webhook 設定

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

## 🔌 API 端點

- `GET /` - 首頁，顯示服務狀態
- `GET /webhook` - Webhook 驗證
- `POST /webhook` - 處理 Messenger 事件（文字、影片）
- `GET /health` - 健康檢查

## 📱 支援的訊息類型

- 💬 **文字訊息**: 透過 ChatGPT 生成回應
- 🤟 **手語影片**: 動態適應性 AI 手語辨識 + 自動生成完整句子
- 📸 **圖片檔案**: 目前提示不支援（可擴展）
- 🎵 **語音檔案**: 目前提示不支援（可擴展）

## 🧪 系統測試與驗證

### 運行架構驗證
```bash
python3 test_architecture.py
```

測試項目包括：
- ✅ 基本模組導入
- ✅ 手語辨識組件
- ✅ 影片處理器
- ✅ Flask 應用架構  
- ✅ 檔案結構完整性
- ✅ 模型架構兼容性
- ✅ 整合工作流程

### 部署前檢查清單
- ✅ 所有 Python 模組正常導入
- ✅ Flask 應用架構完整
- ✅ 手語辨識組件就緒
- ✅ 影片處理流程正常
- ✅ Webhook 端點配置正確
- ✅ 模型檔案存在且架構匹配
- ⚠️ 需要設定 OPENAI_API_KEY
- ⚠️ 需要設定 FACEBOOK_PAGE_ACCESS_TOKEN
- ⚠️ 需要設定 FACEBOOK_VERIFY_TOKEN

## 💻 本地開發

如果想要本地測試：

```bash
# 1. 安裝依賴套件
pip3 install -r requirements.txt

# 2. 複製並設定環境變數
cp env_example .env
# 編輯 .env 檔案填入你的 API 金鑰

# 3. 運行系統測試
python3 test_architecture.py

# 4. 啟動應用程式
python3 run.py
```

## ⚠️ 注意事項

- ✅ Render 自動提供 HTTPS (Facebook 要求)
- ✅ 支援動態手語詞彙數量辨識（1-6 個詞彙）
- ✅ 自動調整辨識策略提高準確率
- ⚠️ 定期更新 API 金鑰和權杖
- ⚠️ 監控 OpenAI API 使用量避免超額
- ⚠️ Render 免費方案服務閒置會睡眠

## 🔧 疑難排解

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

4. **手語辨識失敗**
   - 確保影片中手部清楚可見
   - 檢查動作不要太快或太慢  
   - 確認是支援的手語詞彙 (eat, fish, like, want)

5. **Render 服務睡眠**
   - 免費方案閒置 15 分鐘會睡眠
   - 第一次喚醒可能需要 30 秒

## 🚀 開始使用

現在就去 Render 部署你的智慧手語辨識機器人吧！ 🤖🤟✨

---

**技術特色**: 動態適應性手語辨識 | 三階段智慧處理 | GPT 增強句子生成 | 即時 Messenger 整合 