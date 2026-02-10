from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    arm_db_path: str = "/home/arm/db/arm.db"
    arm_log_path: str = "/home/arm/logs"
    arm_url: str = "http://localhost:8080"
    transcoder_url: str = "http://localhost:5000"
    transcoder_api_key: str = ""
    port: int = 8888

    model_config = {"env_prefix": "ARM_UI_"}


settings = Settings()
