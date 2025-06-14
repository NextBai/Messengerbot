# 🤖 Messenger Bot + 手語辨識 + ChatGPT

一個整合 Facebook Messenger、手語辨識和 ChatGPT 的智慧聊天機器人，部署在 Railway 平台。

## ✨ 功能特色

### 🤟 手語辨識
- **動態適應性辨識**：根據影片內容自動調整辨識策略
- **多詞彙支援**：可辨識 1-6 個手語詞彙的組合
- **高準確度**：使用 PyTorch LSTM + 注意力機制
- **支援詞彙**：eat（吃）、fish（魚）、like（喜歡）、want（想要）

### 💬 智慧對話
- **ChatGPT 整合**：使用 GPT-4o-mini 模型
- **繁體中文**：完整支援繁體中文對話
- **上下文理解**：結合手語辨識結果生成自然回應

### 🚀 Railway 部署
- **高效能**：更多記憶體和 CPU 資源
- **自動擴展**：根據流量自動調整
- **即時監控**：完整的日誌和健康檢查

## 🏗️ 系統架構

```
用戶影片 → Messenger → Webhook → 手語辨識 → ChatGPT → 回應
用戶文字 → Messenger → Webhook → ChatGPT → 回應
```

### 核心組件
- **Flask App** (`app.py`)：主要應用程式
- **手語處理器** (`sign_language_processor.py`)：PyTorch + MediaPipe
- **影片處理器** (`video_processor.py`)：影片下載和基本處理
- **配置管理** (`config.py`)：環境變數和設定

## 🚀 Railway 部署

### 1. 準備工作
```bash
# 複製專案
git clone <your-repo>
cd messenger-bot-sign-language

# 檢查檔案
ls -la
```

### 2. Railway 部署
1. 前往 [Railway.app](https://railway.app)
2. 使用 GitHub 帳號登入
3. 選擇 "Deploy from GitHub repo"
4. 選擇你的 repository

### 3. 環境變數設定
在 Railway 專案設定中新增：

```
VERIFY_TOKEN=你的驗證token
PAGE_ACCESS_TOKEN=你的Facebook頁面token
OPENAI_API_KEY=你的OpenAI_API金鑰
PORT=10000
```

### 4. 自動部署
Railway 會自動偵測：
- `railway.json` - 專案配置
- `nixpacks.toml` - 建置設定
- `requirements.txt` - Python 依賴

### 5. 更新 Facebook Webhook
部署完成後，更新 Facebook 開發者控制台的 Webhook URL：
```
https://your-app-name.up.railway.app/webhook
```

## 📱 Facebook Messenger 設定

### 1. 建立 Facebook 應用程式
1. 前往 [Facebook 開發者控制台](https://developers.facebook.com/)
2. 建立新應用程式
3. 新增 Messenger 產品

### 2. 設定 Webhook
- **Webhook URL**: `https://your-app-name.up.railway.app/webhook`
- **驗證 Token**: 你設定的 `VERIFY_TOKEN`
- **訂閱欄位**: `messages`, `messaging_postbacks`

### 3. 取得 Page Access Token
1. 選擇你的 Facebook 粉絲專頁
2. 生成 Page Access Token
3. 設定為 `PAGE_ACCESS_TOKEN` 環境變數

## 🔧 本地開發

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 設定環境變數
```bash
cp env_example .env
# 編輯 .env 檔案，填入你的 API 金鑰
```

### 3. 啟動應用
```bash
python3 app.py
```

### 4. 測試 Webhook
使用 ngrok 建立公開 URL：
```bash
ngrok http 10000
```

## 🤟 手語辨識技術

### 支援的手語詞彙
- **eat** (吃)：雙手做進食動作
- **fish** (魚)：手做游泳動作
- **like** (喜歡)：拇指向上
- **want** (想要)：雙手向前伸展

### 辨識流程
1. **影片預處理**：MediaPipe 提取手部關鍵點
2. **特徵提取**：21個手部關鍵點的3D座標
3. **序列分析**：LSTM 網路處理時間序列
4. **注意力機制**：聚焦重要的時間段
5. **多詞彙組合**：智慧組合多個手語詞彙

### 動態適應性
- **單詞模式**：高穩定性，適合單一手語
- **平衡模式**：2-3個詞彙的組合
- **多詞模式**：4+詞彙，快速回應

## 📊 系統監控

### 健康檢查
- **端點**: `/health`
- **回應**: JSON 格式的系統狀態

### 日誌監控
Railway 控制台提供即時日誌查看：
- 手語辨識結果
- ChatGPT API 調用
- 錯誤和警告訊息

## 🔍 故障排除

### 常見問題

**1. 記憶體不足**
- 檢查影片檔案大小（限制10MB）
- 升級 Railway 方案

**2. 手語辨識失敗**
- 確保手部清晰可見
- 檢查 PyTorch 模型載入
- 查看日誌中的錯誤訊息

**3. ChatGPT 無回應**
- 檢查 `OPENAI_API_KEY` 設定
- 確認 API 額度充足

**4. Webhook 驗證失敗**
- 檢查 `VERIFY_TOKEN` 設定
- 確認 Facebook 設定正確

### 日誌分析
```bash
# Railway 控制台查看即時日誌
# 或使用 Railway CLI
railway logs
```

## 🚀 效能優化

### Railway 特定優化
- **延遲載入**：只在需要時載入 PyTorch 模型
- **記憶體清理**：處理完影片後自動清理
- **單一 Worker**：避免記憶體重複載入
- **超時設定**：防止長時間等待

### 建議配置
- **記憶體**：至少 1GB（推薦 2GB）
- **CPU**：2 核心以上
- **網路**：穩定的網路連線

## 📈 未來發展

### 計劃功能
- [ ] 更多手語詞彙支援
- [ ] 即時手語辨識（WebRTC）
- [ ] 多語言支援
- [ ] 語音合成回應
- [ ] 手語學習模式

### 技術升級
- [ ] 更先進的深度學習模型
- [ ] 邊緣運算優化
- [ ] 分散式處理架構

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

### 開發流程
1. Fork 專案
2. 建立功能分支
3. 提交變更
4. 建立 Pull Request

## 📄 授權

MIT License - 詳見 LICENSE 檔案

## 📞 支援

如有問題，請：
1. 查看 [故障排除](#故障排除) 章節
2. 檢查 Railway 日誌
3. 提交 GitHub Issue

---

**🎯 讓手語溝通更簡單，讓 AI 更貼近生活！** 