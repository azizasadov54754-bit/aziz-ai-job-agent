from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_env:str='production'; database_url:str; secret_key:str='change-me'; admin_username:str='aziz'; admin_password:str='change-me'; telegram_bot_token:str=''; telegram_admin_id:int=0; gemini_api_key:str=''; gemini_model:str='gemini-2.5-flash'; google_client_id:str=''; google_client_secret:str=''; google_refresh_token:str=''; google_gmail_address:str=''; auto_apply_enabled:bool=False; auto_apply_min_score:int=85; auto_apply_daily_limit:int=10; daily_discovery_limit:int=50; discovery_hour:int=9; discovery_minute:int=0; reply_poll_minutes:int=3; timezone:str='Asia/Tashkent'; http_timeout_seconds:int=20
    model_config=SettingsConfigDict(env_file='.env',extra='ignore',case_sensitive=False)
settings=Settings()
