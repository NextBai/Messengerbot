#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Messenger Bot + ChatGPT 啟動腳本
執行這個檔案來啟動你的機器人
"""

import sys
from app import app
from config import Config

def main():
    """主程式入口"""
    try:
        # 驗證配置
        Config.validate_config()
        print("✅ 配置驗證通過")
        
        print(f"🚀 啟動 Messenger Bot + ChatGPT 服務...")
        print(f"📡 監聽端口: {Config.PORT}")
        print(f"🌐 Webhook URL: {Config.WEBHOOK_URL}")
        print(f"🤖 AI 模型: {Config.OPENAI_MODEL}")
        print("-" * 50)
        
        # 啟動 Flask 應用
        app.run(
            host='0.0.0.0', 
            port=Config.PORT, 
            debug=Config.DEBUG
        )
        
    except ValueError as e:
        print(f"❌ 配置錯誤: {e}")
        print("💡 請檢查你的 .env 檔案設定")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n👋 程式已停止")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 