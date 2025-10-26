from fastapi import Request
from .constants import CONFIG

def retrieve_language_quality(encoding):
    try: return float(encoding.split("=")[1])
    except: return 1.0

def select_accept_language(request: Request):
    accept_language = request.headers.get("Accept-Language", "")
    
    qualities = {}
    for encoding in accept_language.split(","):
        # Ignore location 
        language = encoding.split(";")[0].split("-")[0]
        if language not in CONFIG["LANGUAGES"]:
            continue
        quality = retrieve_language_quality(encoding)
        if language not in qualities or qualities[language] < quality:
            qualities[language] = quality
     
    return max(qualities, key=qualities.__getitem__) if qualities else "en"
