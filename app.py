import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 從環境變數取得設定
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'your_verify_token')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN', 'your_page_access_token')

# Messenger API 網址
FACEBOOK_API_URL = 'https://graph.facebook.com/v18.0/me/messages'

@app.route('/', methods=['GET'])
def home():
    return "Messenger Bot 正在運行中！🚀"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """驗證 Webhook - Facebook 會呼叫這個來驗證你的服務"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("Webhook 驗證成功！")
            return challenge
        else:
            print("驗證失敗 - token 不正確")
            return "驗證失敗", 403
    
    return "需要驗證參數", 400

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """處理從 Messenger 來的訊息"""
    try:
        data = request.get_json()
        
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for messaging_event in entry.get('messaging', []):
                    if messaging_event.get('message'):
                        handle_message(messaging_event)
                    elif messaging_event.get('postback'):
                        handle_postback(messaging_event)
        
        return "EVENT_RECEIVED", 200
    
    except Exception as e:
        print(f"處理 webhook 時發生錯誤: {e}")
        return "錯誤", 500

def handle_message(messaging_event):
    """處理一般訊息"""
    sender_id = messaging_event['sender']['id']
    message_text = messaging_event.get('message', {}).get('text', '')
    
    print(f"收到訊息 from {sender_id}: {message_text}")
    
    # 簡單的回應邏輯
    response_text = f"收到訊息：{message_text}"
    
    send_message(sender_id, response_text)

def handle_postback(messaging_event):
    """處理 postback 事件（按鈕點擊等）"""
    sender_id = messaging_event['sender']['id']
    postback_payload = messaging_event['postback']['payload']
    
    print(f"收到 postback from {sender_id}: {postback_payload}")
    
    send_message(sender_id, f"收到 postback：{postback_payload}")

def send_message(recipient_id, message_text):
    """發送訊息給使用者"""
    headers = {
        'Content-Type': 'application/json'
    }
    
    data = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    
    params = {
        'access_token': PAGE_ACCESS_TOKEN
    }
    
    response = requests.post(
        FACEBOOK_API_URL,
        headers=headers,
        params=params,
        json=data
    )
    
    if response.status_code != 200:
        print(f"發送訊息失敗: {response.status_code} - {response.text}")
    else:
        print(f"訊息發送成功給 {recipient_id}")

def send_quick_reply(recipient_id, message_text, quick_replies):
    """發送快速回覆選項"""
    headers = {
        'Content-Type': 'application/json'
    }
    
    data = {
        'recipient': {'id': recipient_id},
        'message': {
            'text': message_text,
            'quick_replies': quick_replies
        }
    }
    
    params = {
        'access_token': PAGE_ACCESS_TOKEN
    }
    
    requests.post(
        FACEBOOK_API_URL,
        headers=headers,
        params=params,
        json=data
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 