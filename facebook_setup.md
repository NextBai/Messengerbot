# Facebook Webhook 設定指南 🔧

## 第一步：準備驗證權杖

**驗證權杖**是你自己設定的密碼，用來驗證 Facebook 的請求。

範例：`my_super_secret_verify_token_2024`

⚠️ **重要**：這個權杖要在 Facebook 和 Render 中設定成**完全一樣**的值！

---

## 第二步：Facebook 開發者控制台設定

### 1. 建立 Facebook 應用程式

1. 前往 [Facebook for Developers](https://developers.facebook.com/)
2. 點擊「建立應用程式」
3. 選擇「商業」類型
4. 填入應用程式名稱，例如：`我的聊天機器人`

### 2. 新增 Messenger 產品

1. 在應用程式控制台中
2. 點擊「新增產品」
3. 找到「Messenger」，點擊「設定」

### 3. 設定 Webhook

在 Messenger 設定頁面中：

1. **找到「Webhook」區塊**
2. **點擊「新增回呼網址」**
3. **填入設定**：

   ```
   回呼網址: https://你的應用名.onrender.com/webhook
   驗證權杖: my_super_secret_verify_token_2024
   ```

   ⚠️ **注意**：
   - 回呼網址必須是 HTTPS
   - 驗證權杖要和你在 Render 設定的一模一樣

4. **選擇事件**：
   - ✅ `messages`
   - ✅ `messaging_postbacks`

5. **點擊「驗證並儲存」**

### 4. 取得頁面存取權杖

1. **在「存取權杖」區塊**
2. **選擇你的 Facebook 頁面**
3. **點擊「產生權杖」**
4. **複製產生的權杖**（很長的一串）

---

## 第三步：Render 環境變數設定

在 Render 的環境變數中設定：

```
FACEBOOK_PAGE_ACCESS_TOKEN=EAAxxxxxx（你剛複製的長權杖）
FACEBOOK_VERIFY_TOKEN=my_super_secret_verify_token_2024
OPENAI_API_KEY=sk-xxxxx（你的 OpenAI 金鑰）
```

⚠️ **重要檢查**：
- `FACEBOOK_VERIFY_TOKEN` 必須和 Facebook Webhook 設定中的**完全一樣**
- `FACEBOOK_PAGE_ACCESS_TOKEN` 是從 Facebook 複製的長權杖

---

## 第四步：測試連接

1. **確認 Render 服務正在運行**
2. **在 Facebook Webhook 設定中點擊「測試」**
3. **如果出現綠色勾勾 ✅，表示設定成功！**

---

## 常見問題排解

### ❌ Webhook 驗證失敗

**可能原因**：
- Render 服務沒有啟動
- `FACEBOOK_VERIFY_TOKEN` 在 Facebook 和 Render 中不一致
- 回呼網址錯誤

**解決方法**：
1. 檢查 Render 服務狀態
2. 確認兩邊的驗證權杖完全一樣
3. 確認回呼網址格式：`https://你的應用名.onrender.com/webhook`

### ❌ 訊息收不到回應

**可能原因**：
- `FACEBOOK_PAGE_ACCESS_TOKEN` 錯誤或過期
- OpenAI API 金鑰問題
- 頁面沒有連結到應用程式

**解決方法**：
1. 重新產生頁面存取權杖
2. 檢查 OpenAI API 金鑰
3. 確認 Facebook 頁面已連結到應用程式

---

## 設定完成後

✅ Facebook Webhook 驗證通過  
✅ Render 服務正常運行  
✅ 所有環境變數都設定正確  

🎉 **現在可以開始在 Messenger 上和你的 AI 機器人聊天了！** 