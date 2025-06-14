#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
影片處理模組
處理 Messenger 收到的影片檔案
"""

import os
import requests
import json
import tempfile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.backend_url = os.getenv('BACKEND_API_URL', 'https://your-backend-api.com')
        self.temp_dir = tempfile.gettempdir()
    
    def save_video_temp(self, video_data, sender_id):
        """暫時儲存影片檔案"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"video_{sender_id}_{timestamp}.mp4"
            filepath = os.path.join(self.temp_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(video_data)
            
            logger.info(f"影片已儲存至: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"儲存影片失敗: {e}")
            return None
    
    def send_to_backend(self, video_data, sender_id, metadata=None):
        """傳送影片到後端 API"""
        try:
            # 先儲存到暫存檔案
            temp_file = self.save_video_temp(video_data, sender_id)
            if not temp_file:
                return False, "儲存影片失敗"
            
            # 準備上傳的資料
            files = {
                'video': ('video.mp4', open(temp_file, 'rb'), 'video/mp4')
            }
            
            data = {
                'sender_id': sender_id,
                'timestamp': datetime.now().isoformat(),
                'metadata': json.dumps(metadata or {})
            }
            
            # 傳送到後端
            response = requests.post(
                f"{self.backend_url}/api/videos/upload",
                files=files,
                data=data,
                timeout=30
            )
            
            # 清理暫存檔案
            files['video'][1].close()
            os.remove(temp_file)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"影片上傳成功: {result}")
                return True, result.get('message', '上傳成功')
            else:
                logger.error(f"後端回應錯誤: {response.status_code} - {response.text}")
                return False, f"後端處理失敗: {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.error("後端請求逾時")
            return False, "後端處理逾時，請稍後再試"
        except Exception as e:
            logger.error(f"傳送到後端失敗: {e}")
            return False, f"處理失敗: {str(e)}"
    
    def analyze_video_local(self, video_data):
        """本地簡單分析影片資訊"""
        try:
            info = {
                'size_bytes': len(video_data),
                'size_mb': round(len(video_data) / (1024 * 1024), 2),
                'timestamp': datetime.now().isoformat()
            }
            
            # 可以加入更多分析，如：
            # - 影片長度
            # - 解析度
            # - 編碼格式等
            
            return info
        except Exception as e:
            logger.error(f"影片分析失敗: {e}")
            return {}

# 範例後端 API 格式
"""
後端 API 應該接收：
POST /api/videos/upload

FormData:
- video: 影片檔案
- sender_id: 發送者 ID
- timestamp: 時間戳記
- metadata: 額外資訊 (JSON 字串)

回應格式:
{
    "success": true,
    "message": "影片處理完成",
    "video_id": "12345",
    "analysis_result": {...}
}
""" 