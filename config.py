import os
from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- API Keys (from environment) ---
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_SHEETS_CRED_PATH = os.getenv("GOOGLE_SHEETS_CRED_PATH", "credentials.json")
GOOGLE_SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "")

# --- Apify Actors ---
ACTOR_HASHTAG_ANALYTICS = "apify/instagram-hashtag-analytics-scraper"
ACTOR_HASHTAG_SCRAPER = "apify/instagram-hashtag-scraper"

# --- Hashtags & Categories ---
HASHTAG_CONFIG = {
    "AI": {
        "category": "AI_일반",
        "description": "AI 전반 트렌드",
        "related_keywords": ["인공지능", "머신러닝", "딥러닝"],
    },
    "클로드": {
        "category": "AI_툴",
        "description": "Anthropic Claude 관련",
        "related_keywords": ["Claude", "앤트로픽", "클로드AI"],
    },
    "AI대학원": {
        "category": "AI_교육",
        "description": "AI 교육/학습 콘텐츠",
        "related_keywords": ["AI공부", "AI강의", "AI학습"],
    },
}

# --- Content Type Mapping ---
CONTENT_TYPE_MAP = {
    "Video": "reel",
    "Reel": "reel",
    "GraphVideo": "reel",
    "GraphSidecar": "carousel",
    "GraphImage": "image",
    "Image": "image",
    "Sidecar": "carousel",
}
TARGET_CONTENT_TYPES = {"reel", "image", "carousel"}  # 릴스 없을 시 전체 포함

# --- Field Aliases (Apify output normalization) ---
FIELD_ALIASES = {
    "videoPlayCount": ["videoPlayCount", "playCount", "videoViewCount", "viewCount", "plays"],
    "likesCount": ["likesCount", "likeCount", "likes"],
    "commentsCount": ["commentsCount", "commentCount", "comments"],
    "ownerUsername": ["ownerUsername", "ownerName", "username", "owner"],
    "caption": ["caption", "text", "description"],
    "url": ["url", "postUrl", "link"],
    "shortCode": ["shortCode", "code", "id"],
    "type": ["type", "contentType", "mediaType", "productType"],
    "timestamp": ["timestamp", "takenAt", "taken_at", "date", "createdAt"],
    "musicInfo": ["musicInfo", "music", "audio", "audioInfo"],
    "videoUrl": ["videoUrl", "video_url", "videoSrc"],
    "transcript": ["transcript", "transcription", "subtitles"],
    "latestComments": ["latestComments", "comments", "lastComments", "topComments"],
}

# --- Erica Profile (for Step 7) ---
ERICA_PROFILE = {
    "positioning": (
        "곧 4천만원 쓰게 될 AI 대학원 학비로 3천만원 태운 기획자. "
        "최연소 팀장. 비개발자. "
        "가뜩이나 할 것도 많은데 일일이 한땀한땀 손으로 일하기 싫어하는 극도의 효율 추구."
    ),
    "role": "일본 뷰티/코스메틱 시장 대상 비즈니스 기획 (kmongjapan)",
    "strengths": "AI 자동화 도구 활용, 바이브코딩으로 비개발자가 자동화 파이프라인 구축",
    "killer_keywords": ["AI 대학원 3천만원", "최연소 팀장", "비개발자", "극도의 효율"],
    "tone": "솔직하고 날 것 그대로, 허세 없이 리얼한 경험담",
    "target": "AI에 관심 있는 직장인, 마케터, 1인 사업자",
}

# --- Filtering ---
MIN_VIEWS = 1000
