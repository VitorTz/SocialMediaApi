import bcrypt
import re


def extract_hashtags(content: str) -> list[str]:    
    if not content:
        return []
        
    return [tag.lower() for tag in re.findall(r'#(\w+)', content)]    


def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt)


def check_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)


