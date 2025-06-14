#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Messenger Bot + ChatGPT 啟動腳本
執行這個檔案來啟動你的機器人
"""

import sys
import os
from app import app
from config import Config

def main():
    """主程式入口"""
    try:
        print(f"🚀 啟動 Messenger Bot + ChatGPT 服務...")
        print(f"📡 監聽端口: {Config.PORT}")
        print(f"🌐 Webhook URL: {Config.WEBHOOK_URL}")
        print(f"🤖 AI 模型: {Config.OPENAI_MODEL}")
        print("-" * 50)
        
        # 檢查關鍵環境變數
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️  警告: 未設定 OPENAI_API_KEY，ChatGPT 功能將無法使用")
        
        if not os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN'):
            print("⚠️  警告: 未設定 FACEBOOK_PAGE_ACCESS_TOKEN，無法發送訊息")
        
        if not os.getenv('FACEBOOK_VERIFY_TOKEN'):
            print("⚠️  警告: 未設定 FACEBOOK_VERIFY_TOKEN，Webhook 驗證將失敗")
        
        # 啟動 Flask 應用
        app.run(
            host='0.0.0.0', 
            port=Config.PORT, 
            debug=Config.DEBUG
        )
        
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n👋 程式已停止")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 