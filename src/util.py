import re


def extract_hashtags(content: str) -> list[str]:    
    if not content:
        return []
        
    return [tag.lower() for tag in re.findall(r'#(\w+)', content)]    