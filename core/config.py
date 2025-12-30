import os
from dataclasses import dataclass

@dataclass
class Config:
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "sk-bbc81b74efdc483f933a16ff1af24c45")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    MODEL_VISION: str = os.getenv("MODEL_VISION", "ui-tars")
    MODEL_BRAIN: str = os.getenv("MODEL_BRAIN", "deepseek-chat")
    PC_PASSWORD: str = os.getenv("PC_PASSWORD", "meraki")

    # Screen resolution (width, height) - will be updated by action module or env
    SCREEN_WIDTH: int = 1920
    SCREEN_HEIGHT: int = 1080

config = Config()
