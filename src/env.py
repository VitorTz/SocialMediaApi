from dotenv import load_dotenv
import os


load_dotenv(".env")


def getenv(key: str) -> str:
    return os.getenv(key)