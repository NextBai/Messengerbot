import os
import json
import requests
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import logging
from video_processor import VideoProcessor
from sign_language_processor import SignLanguageVideoProcessor

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
        # 初始化影片處理器
        self.video_processor = VideoProcessor()
        # 初始化手語辨識處理器
        try:
            self.sign_language_processor = SignLanguageVideoProcessor()
            logger.info("手語辨識器初始化成功")
        except Exception as e:
            logger.error(f"手語辨識器初始化失敗: {e}")
            self.sign_language_processor = None
        
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
    
    def download_video(self, video_url):
        """下載影片檔案"""
        try:
            headers = {'Authorization': f'Bearer {PAGE_ACCESS_TOKEN}'}
            response = requests.get(video_url, headers=headers)
            response.raise_for_status()
            
            # 這裡可以儲存影片或進行處理
            logger.info(f"影片下載成功，大小: {len(response.content)} bytes")
            
            return response.content
        except Exception as e:
            logger.error(f"影片下載失敗: {e}")
            return None
    
    def process_video_message(self, sender_id, video_url):
        """處理影片訊息 - 手語辨識"""
        logger.info(f"收到來自 {sender_id} 的影片: {video_url}")
        
        # 先回應用戶，讓他知道我們收到了
        self.send_message(sender_id, "🤟 收到影片！正在進行手語辨識，請稍等...")
        
        # 下載影片
        video_data = self.download_video(video_url)
        
        if not video_data:
            self.send_message(sender_id, "❌ 抱歉，影片下載失敗，請檢查網路連線後再試。")
            return
        
        # 檢查是否有手語辨識器
        if not self.sign_language_processor:
            # 備用：使用原來的影片處理邏輯
            video_info = self.video_processor.analyze_video_local(video_data)
            success, message = self.video_processor.send_to_backend(
                video_data, sender_id, metadata=video_info
            )
            if success:
                response_text = f"✅ 影片處理完成！\n📊 檔案大小: {video_info.get('size_mb', 0)} MB\n📝 後端回應: {message}"
            else:
                response_text = f"❌ 影片處理失敗: {message}"
            self.send_message(sender_id, response_text)
            return
        
        # 進行手語辨識
        try:
            success, result = self.sign_language_processor.process_video(video_data, sender_id)
            
            if success:
                word_sequence = result['word_sequence']
                sentence = result['sentence'] 
                word_count = result['word_count']
                
                # 構建回應訊息
                response_text = f"🤟 手語辨識完成！\n\n"
                response_text += f"🔤 辨識到的手語詞彙：{', '.join(word_sequence)}\n"
                response_text += f"📝 完整句子：{sentence}\n"
                response_text += f"📊 共辨識出 {word_count} 個手語詞彙"
                
                logger.info(f"手語辨識成功 - 詞彙: {word_sequence}, 句子: {sentence}")
            else:
                response_text = f"❌ 手語辨識失敗：{result}\n\n"
                response_text += "💡 請確保：\n"
                response_text += "• 影片中有清晰的手語動作\n"
                response_text += "• 手部在畫面中清楚可見\n"
                response_text += "• 動作不要太快或太慢"
                
                logger.warning(f"手語辨識失敗: {result}")
            
        except Exception as e:
            response_text = f"❌ 處理影片時發生錯誤: {str(e)}\n🔧 請稍後再試或聯繫技術支援。"
            logger.error(f"手語辨識處理錯誤: {e}")
        
        self.send_message(sender_id, response_text)
    
    def process_message(self, sender_id, message_text):
        """處理文字訊息"""
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
                        message = messaging_event['message']
                        
                        # 檢查是否有文字訊息
                        if 'text' in message:
                            message_text = message['text']
                            bot.process_message(sender_id, message_text)
                        
                        # 檢查是否有影片附件
                        elif 'attachments' in message:
                            for attachment in message['attachments']:
                                if attachment['type'] == 'video':
                                    video_url = attachment['payload']['url']
                                    bot.process_video_message(sender_id, video_url)
                                elif attachment['type'] == 'image':
                                    # 也可以處理圖片
                                    image_url = attachment['payload']['url']
                                    bot.send_message(sender_id, "📸 收到圖片！目前只支援影片處理。")
                                elif attachment['type'] == 'audio':
                                    # 也可以處理語音
                                    audio_url = attachment['payload']['url']
                                    bot.send_message(sender_id, "🎵 收到語音！目前只支援影片處理。")
                                else:
                                    bot.send_message(sender_id, f"📎 收到 {attachment['type']} 附件，目前只支援影片處理。")
        
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