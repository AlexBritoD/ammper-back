from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    BELVO_CLIENT_ID: str
    BELVO_SECRET: str
    BELVO_BASE_URL: str = "https://sandbox.belvo.com/api"
    AMMPER_USER: str 
    AMMPER_PASSWORD: str 

    class Config:
        env_file = ".env"

settings = Settings()
