import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class Config:
    """應用程式配置類別"""
    
    # Facebook 設定
    FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')  # 統一變數名稱
    FACEBOOK_VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')  # 統一變數名稱
    
    # OpenAI 設定
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-4o-mini'
    OPENAI_MAX_TOKENS = 1000
    OPENAI_TEMPERATURE = 0.7
    
    # 伺服器設定 - Railway 預設使用動態端口
    PORT = int(os.getenv('PORT', 10000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Railway 環境設定
    RAILWAY_ENVIRONMENT = os.getenv('RAILWAY_ENVIRONMENT', 'development')
    
    # 日誌設定
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate_config(cls):
        """驗證必要的配置是否存在"""
        required_configs = [
            'PAGE_ACCESS_TOKEN',  # 統一變數名稱
            'VERIFY_TOKEN',       # 統一變數名稱
            'OPENAI_API_KEY'
        ]
        
        missing_configs = []
        for config in required_configs:
            if not os.getenv(config):
                missing_configs.append(config)
        
        if missing_configs:
            raise ValueError(f"缺少必要的環境變數: {', '.join(missing_configs)}")
        
        return True
    
    @classmethod
    def get_webhook_url(cls):
        """動態取得 Railway 部署的 Webhook URL"""
        railway_url = os.getenv('RAILWAY_STATIC_URL')
        if railway_url:
            return f"{railway_url}/webhook"
        return None 