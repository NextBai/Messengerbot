# Railway 部署指南

## 為什麼選擇 Railway？
- **更多記憶體**：Railway 提供更多記憶體配額，適合 PyTorch + MediaPipe 應用
- **更好的效能**：更快的 CPU 和更穩定的網路
- **簡單部署**：直接連接 GitHub 自動部署

## 部署步驟

### 1. 準備 Railway 帳號
1. 前往 [Railway.app](https://railway.app)
2. 使用 GitHub 帳號登入
3. 連接你的 GitHub repository

### 2. 建立新專案
1. 點擊 "New Project"
2. 選擇 "Deploy from GitHub repo"
3. 選擇你的 Messenger bot repository

### 3. 設定環境變數
在 Railway 專案設定中新增以下環境變數：

```
VERIFY_TOKEN=你的驗證token
PAGE_ACCESS_TOKEN=你的Facebook頁面存取token
OPENAI_API_KEY=你的OpenAI API金鑰
PORT=10000
```

### 4. 部署配置
Railway 會自動偵測到：
- `railway.json` - Railway 專案配置
- `nixpacks.toml` - 建置配置
- `requirements.txt` - Python 依賴

### 5. 取得部署網址
部署完成後，Railway 會提供一個網址，格式類似：
```
https://your-app-name.up.railway.app
```

### 6. 更新 Facebook Webhook
1. 前往 Facebook 開發者控制台
2. 更新 Webhook URL 為：`https://your-app-name.up.railway.app/webhook`
3. 驗證 token 保持不變

## 記憶體優化設定

### Gunicorn 配置
- `--workers 1`：單一 worker 避免記憶體重複載入
- `--max-requests 100`：定期重啟 worker 釋放記憶體
- `--timeout 120`：給手語辨識足夠時間
- `--preload`：預載入應用程式

### 模型載入優化
- 延遲載入：只在需要時載入 PyTorch 模型
- 記憶體清理：處理完影片後清理暫存
- 錯誤處理：MediaPipe 失敗時優雅降級

## 監控與除錯

### 健康檢查
Railway 會定期檢查 `/health` 端點確保服務正常

### 日誌查看
在 Railway 控制台可以即時查看應用程式日誌

### 常見問題
1. **記憶體不足**：調整 worker 數量或升級方案
2. **載入超時**：增加 `healthcheckTimeout` 設定
3. **模型載入失敗**：檢查 PyTorch 版本相容性

## 成本考量
- Railway 免費方案：每月 $5 額度
- 升級方案：更多記憶體和 CPU 資源
- 按使用量計費：適合測試和小規模使用

## 下一步
部署成功後，你的手語辨識 Messenger bot 就能處理：
- 文字訊息 → ChatGPT 對話
- 影片訊息 → 手語辨識 + 智慧回應

記得測試所有功能確保正常運作！ 