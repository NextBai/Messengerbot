import os
import json
import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# 從環境變數取得設定
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'your_verify_token')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN', 'your_page_access_token')
LOCAL_RECEIVER_URL = os.environ.get('LOCAL_RECEIVER_URL', 'http://localhost:5001')

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

@app.route('/receive_recognition_result', methods=['POST'])
def receive_recognition_result():
    """接收來自本地手語辨識服務的結果"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "沒有收到資料"}), 400
        
        sender_id = data.get('sender_id')
        recognition_result = data.get('recognition_result', '無法辨識')
        confidence = data.get('confidence', 0)
        timestamp = data.get('timestamp', '')
        
        if not sender_id:
            return jsonify({"status": "error", "message": "缺少 sender_id"}), 400
        
        print(f"📝 收到手語辨識結果 - 用戶：{sender_id}")
        print(f"🎯 辨識結果：{recognition_result}")
        print(f"📊 信心度：{confidence}")
        
        # 發送辨識結果給用戶
        result_message = f"🤖 手語辨識完成！\n\n✨ 辨識結果：{recognition_result}"
        if confidence > 0:
            result_message += f"\n📊 信心度：{confidence:.0%}"
        
        send_message(sender_id, result_message)
        
        return jsonify({
            "status": "success", 
            "message": "辨識結果已發送給用戶"
        })
        
    except Exception as e:
        print(f"處理辨識結果時發生錯誤：{e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def handle_message(messaging_event):
    """處理一般訊息"""
    sender_id = messaging_event['sender']['id']
    message = messaging_event.get('message', {})
    message_text = message.get('text', '')
    attachments = message.get('attachments', [])
    
    print(f"收到訊息 from {sender_id}: {message_text}")
    
    # 檢查是否有附件
    if attachments:
        for attachment in attachments:
            if attachment.get('type') == 'video':
                video_url = attachment.get('payload', {}).get('url')
                if video_url:
                    # 下載影片到本地
                    success = download_video(video_url, sender_id)
                    if success:
                        send_message(sender_id, "📥 影片已收到！正在進行手語辨識，請稍候...")
                    else:
                        send_message(sender_id, "❌ 影片處理失敗，請重新傳送")
                    return
            else:
                send_message(sender_id, f"收到 {attachment.get('type')} 附件")
                return
    
    # 處理文字訊息
    if message_text:
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

def download_video(video_url, sender_id):
    """推送影片到本地接收服務"""
    try:
        print(f"推送影片到本地服務：{video_url}")
        
        # 取得目前的部署 URL (Render 會自動設定這些環境變數)
        render_url = os.environ.get('RENDER_EXTERNAL_URL')
        if not render_url:
            # 如果沒有 RENDER_EXTERNAL_URL，嘗試建構 URL
            app_name = os.environ.get('RENDER_SERVICE_NAME', 'your-app')
            render_url = f"https://{app_name}.onrender.com"
        
        # 準備要推送的資料
        data = {
            'video_url': video_url,
            'sender_id': sender_id,
            'timestamp': datetime.now().isoformat(),
            'messenger_webhook_url': f"{render_url}/receive_recognition_result"
        }
        
        print(f"🔗 回傳結果的 webhook URL: {data['messenger_webhook_url']}")
        
        # 推送到本地接收服務
        response = requests.post(
            f"{LOCAL_RECEIVER_URL}/receive_video",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ 成功推送影片到本地服務")
            return True
        else:
            print(f"❌ 推送失敗：{response.status_code} - {response.text}")
            return False
        
    except Exception as e:
        print(f"推送影片到本地失敗：{e}")
        return False

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 