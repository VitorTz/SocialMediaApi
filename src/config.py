import os
from dotenv import load_dotenv


load_dotenv('.env')


class Config:

    @staticmethod
    def get_env(key: str) -> str:
        return os.environ.get(key)

