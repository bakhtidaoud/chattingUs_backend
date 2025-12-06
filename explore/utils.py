import re

def extract_hashtags(text):
    """
    Extracts hashtags from a text string.
    Returns a list of unique lowercase hashtags without the # symbol.
    """
    if not text:
        return []
    
    # Regex to find hashtags: # followed by alphanumeric characters
    hashtags = re.findall(r"#(\w+)", text)
    return list(set(tag.lower() for tag in hashtags))
