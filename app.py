import os
import json
import requests
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import logging
from video_processor import VideoProcessor
from sign_language_processor import SignLanguageVideoProcessor
from datetime import datetime

# 載入環境變數
load_dotenv()

# 初始化 Flask 應用
app = Flask(__name__)

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 從環境變數讀取設定 - 統一變數名稱
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 檢查必要環境變數
if not all([VERIFY_TOKEN, PAGE_ACCESS_TOKEN, OPENAI_API_KEY]):
    logger.error("缺少必要的環境變數")
    missing = []
    if not VERIFY_TOKEN: missing.append('VERIFY_TOKEN')
    if not PAGE_ACCESS_TOKEN: missing.append('PAGE_ACCESS_TOKEN')
    if not OPENAI_API_KEY: missing.append('OPENAI_API_KEY')
    logger.error(f"缺少: {', '.join(missing)}")

# 初始化 OpenAI 客戶端
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# 延遲載入處理器以節省記憶體
video_processor = None
sign_language_processor = None

def get_video_processor():
    """延遲載入影片處理器"""
    global video_processor
    if video_processor is None:
        video_processor = VideoProcessor()
    return video_processor

def get_sign_language_processor():
    """延遲載入手語辨識處理器"""
    global sign_language_processor
    if sign_language_processor is None:
        try:
            sign_language_processor = SignLanguageVideoProcessor()
            logger.info("手語辨識處理器載入成功")
        except Exception as e:
            logger.warning(f"手語辨識處理器載入失敗: {e}")
            sign_language_processor = None
    return sign_language_processor

class MessengerBot:
    def __init__(self):
        # 在類別內部初始化 OpenAI 客戶端
        self.client = client
        # 初始化影片處理器
        self.video_processor = get_video_processor()
        # 初始化手語辨識處理器
        self.sign_language_processor = get_sign_language_processor()
        
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
        """下載影片檔案 - Railway 優化版本"""
        try:
            headers = {'Authorization': f'Bearer {PAGE_ACCESS_TOKEN}'}
            # 加入超時設定，避免長時間等待
            response = requests.get(video_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 檢查檔案大小
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > 10:  # 限制 10MB
                    logger.warning(f"影片檔案太大: {size_mb:.2f}MB")
                    return None
            
            logger.info(f"影片下載成功，大小: {len(response.content)} bytes")
            return response.content
            
        except requests.exceptions.Timeout:
            logger.error("影片下載超時")
            return None
        except Exception as e:
            logger.error(f"影片下載失敗: {e}")
            return None
    
    def process_video_message(self, sender_id, video_url):
        """處理影片訊息 - Railway 優化版本"""
        logger.info(f"收到來自 {sender_id} 的影片: {video_url}")
        
        # 先回應用戶，讓他知道我們收到了
        self.send_message(sender_id, "🤟 收到影片！正在進行手語辨識，請稍等...")
        
        try:
            # 下載影片（加入超時和大小限制）
            video_data = self.download_video(video_url)
            
            if not video_data:
                self.send_message(sender_id, "❌ 抱歉，影片下載失敗，請檢查網路連線後再試。")
                return
            
            # 檢查影片大小（Railway 記憶體優化）
            video_size_mb = len(video_data) / (1024 * 1024)
            if video_size_mb > 10:  # 限制 10MB
                self.send_message(sender_id, "影片檔案太大（超過10MB），請傳送較小的影片檔案。")
                return
            
            # 檢查是否有手語辨識器
            if not self.sign_language_processor:
                # 備用：使用原來的影片處理邏輯
                video_info = self.video_processor.analyze_video_local(video_data)
                success, message = self.video_processor.send_to_backend(
                    video_data, sender_id, metadata=video_info
                )
                if success:
                    response_text = f"✅ 影片處理完成！\n📊 檔案大小: {video_info.get('size_mb', 0)} MB"
                    if self.client:
                        # 使用 ChatGPT 生成友善回應
                        chatgpt_response = self.get_chatgpt_response(
                            "用戶發送了影片但手語辨識功能暫時無法使用。請用繁體中文友善地說明收到了影片，並鼓勵用戶用文字描述想表達的內容。", 
                            sender_id
                        )
                        response_text += f"\n\n{chatgpt_response}"
                else:
                    response_text = f"❌ 影片處理失敗: {message}"
                self.send_message(sender_id, response_text)
                return
            
            # 進行手語辨識
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
                
                # 如果有 ChatGPT，生成更自然的回應
                if self.client and sentence:
                    chatgpt_response = self.get_chatgpt_response(
                        f"用戶透過手語表達了：{sentence}。請用繁體中文自然地回應這個內容。", 
                        sender_id
                    )
                    response_text += f"\n\n💬 AI 回應：{chatgpt_response}"
                
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
        finally:
            # 清理記憶體（Railway 優化）
            try:
                del video_data
                import gc
                gc.collect()
            except:
                pass
        
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
        'timestamp': datetime.now().isoformat(),
        'service': 'messenger-sign-language-bot'
    }), 200

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
    # Railway 部署時不會執行這段，但保留給本地測試
    port = int(os.getenv('PORT', 10000))
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 本地測試模式啟動")
    logger.info(f"📡 監聽端口: {port}")
    logger.info(f"🔧 除錯模式: {debug_mode}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode) 