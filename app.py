import os
import json
import requests
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import logging

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Facebook 相關設定
PAGE_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('FACEBOOK_VERIFY_TOKEN')

class MessengerBot:
    def __init__(self):
        # 在類別內部初始化 OpenAI 客戶端
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def send_message(self, recipient_id, message_text):
        """發送訊息到 Facebook Messenger"""
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            logger.info(f"訊息發送成功給用戶 {recipient_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"發送訊息失敗: {e}")
            return False
    
    def get_chatgpt_response(self, user_message, user_id):
        """使用 ChatGPT 生成回應"""
        try:
            # 使用 MCP 協議的概念，將用戶訊息作為工具調用
            messages = [
                {
                    "role": "system", 
                    "content": "你是一個友善的聊天機器人，請用繁體中文回應用戶。保持對話自然且有趣。"
                },
                {
                    "role": "user", 
                    "content": user_message
                }
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"ChatGPT API 錯誤: {e}")
            return "抱歉，我現在無法處理你的訊息，請稍後再試。"
    
    def process_message(self, sender_id, message_text):
        """處理接收到的訊息"""
        logger.info(f"收到來自 {sender_id} 的訊息: {message_text}")
        
        # 獲取 ChatGPT 回應
        response = self.get_chatgpt_response(message_text, sender_id)
        
        # 發送回應
        self.send_message(sender_id, response)

# 初始化機器人
bot = MessengerBot()

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """驗證 Facebook Webhook"""
    if request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge')
    return '驗證失敗', 403

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """處理 Facebook Webhook 事件"""
    try:
        data = request.get_json()
        
        if data['object'] == 'page':
            for entry in data['entry']:
                for messaging_event in entry['messaging']:
                    
                    # 處理訊息事件
                    if 'message' in messaging_event:
                        sender_id = messaging_event['sender']['id']
                        
                        # 檢查是否有文字訊息
                        if 'text' in messaging_event['message']:
                            message_text = messaging_event['message']['text']
                            bot.process_message(sender_id, message_text)
        
        return 'OK', 200
        
    except Exception as e:
        logger.error(f"Webhook 處理錯誤: {e}")
        return 'Error', 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'message': 'Messenger Bot 運行正常'
    })

@app.route('/', methods=['GET'])
def home():
    """首頁"""
    return jsonify({
        'message': '🤖 Messenger Bot + ChatGPT 已啟動！',
        'status': 'running',
        'endpoints': {
            'webhook': '/webhook',
            'health': '/health'
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 