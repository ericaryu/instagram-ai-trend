"""
Step 1 (릴스 전용): apify/instagram-scraper로 해시태그 릴스만 수집
출력: data/01_reels_raw.json

apify/instagram-hashtag-scraper와 달리 이 Actor는:
  - videoViewCount(실제 조회수) 포함
  - type 필터링으로 Video(릴스)만 선택 가능
  - 더 많은 포스트 수집 가능 (유료 플랜 시)
"""
import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

import config
from utils import setup_logging, save_json

ACTOR_ID = "apify/instagram-scraper"

# --- Dry-run dummy data ---
DUMMY_REELS = [
    {
        "shortCode": "REEL001",
        "url": "https://www.instagram.com/reel/REEL001/",
        "caption": "AI 자동화로 업무 50% 줄인 비결 #AI #자동화 #비개발자",
        "likesCount": 3400,
        "commentsCount": 89,
        "videoViewCount": 120000,
        "ownerUsername": "ai_power_user",
        "type": "Video",
        "timestamp": "2024-03-01T10:00:00Z",
        "musicInfo": {"artistName": "trending", "songName": "vibe"},
        "videoUrl": "https://example.com/reel1.mp4",
        "latestComments": [
            {"text": "어떤 툴 쓰셨어요?", "username": "user1", "likesCount": 30},
            {"text": "비개발자도 가능한가요?", "username": "user2", "likesCount": 25},
        ],
        "transcript": "오늘은 AI로 업무를 50% 줄인 방법을 공유해드릴게요.",
        "hashtag_source": "AI",
        "hashtag_category": "AI_일반",
    },
    {
        "shortCode": "REEL002",
        "url": "https://www.instagram.com/reel/REEL002/",
        "caption": "클로드 AI 실무 활용 꿀팁 #클로드 #Claude #AI툴",
        "likesCount": 1800,
        "commentsCount": 54,
        "videoViewCount": 67000,
        "ownerUsername": "claude_master",
        "type": "Video",
        "timestamp": "2024-03-02T14:00:00Z",
        "musicInfo": None,
        "videoUrl": "https://example.com/reel2.mp4",
        "latestComments": [
            {"text": "클로드가 챗GPT보다 낫네요", "username": "user3", "likesCount": 18},
        ],
        "transcript": "",
        "hashtag_source": "클로드",
        "hashtag_category": "AI_툴",
    },
]

# Instagram 해시태그 탐색 URL (Instagram Scraper가 인식하는 형식)
HASHTAG_URL_TEMPLATES = [
    "https://www.instagram.com/explore/tags/{hashtag}/",
]


def build_actor_input(hashtag: str, results_limit: int = 50) -> dict:
    """apify/instagram-scraper 입력 파라미터 생성."""
    return {
        "directUrls": [f"https://www.instagram.com/explore/tags/{hashtag}/"],
        "resultsType": "posts",
        "resultsLimit": results_limit,
        "addParentData": False,
        "enhanceUserMinFollowers": 0,
    }


def scrape_hashtag_reels(client, hashtag: str, category: str, results_limit: int, log) -> list:
    """hashtag에서 Video 타입 포스트(릴스)만 수집."""
    log.info(f"[{hashtag}] Instagram Scraper 실행 중...")
    actor_input = build_actor_input(hashtag, results_limit)

    run = client.actor(ACTOR_ID).call(run_input=actor_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    log.info(f"[{hashtag}] 전체 수집: {len(items)}건")

    # Video 타입만 필터링 (릴스)
    reels = []
    for item in items:
        raw_type = item.get("type") or item.get("productType") or ""
        mapped = config.CONTENT_TYPE_MAP.get(raw_type, raw_type.lower())
        if mapped == "reel":
            item["hashtag_source"] = hashtag
            item["hashtag_category"] = category
            reels.append(item)

    log.info(f"[{hashtag}] 릴스 필터 후: {len(reels)}건")
    return reels


def main():
    parser = argparse.ArgumentParser(description="Step 1 (릴스 전용): 해시태그 릴스 수집")
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 더미 데이터")
    parser.add_argument("--limit", type=int, default=50, help="해시태그별 수집 수 (기본 50)")
    parser.add_argument("--debug", action="store_true", help="상세 로그 출력")
    args = parser.parse_args()

    log = setup_logging(args.debug)
    log.info("=" * 50)
    log.info("Step 1 (릴스 전용): 해시태그 릴스 수집")
    log.info("=" * 50)

    if args.dry_run:
        log.info("[DRY-RUN] 더미 릴스 데이터 사용")
        save_json(DUMMY_REELS, "01_reels_raw.json")
        log.info(f"저장 완료: data/01_reels_raw.json ({len(DUMMY_REELS)}건)")
        return

    if not config.APIFY_API_TOKEN:
        log.error("APIFY_API_TOKEN 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    from apify_client import ApifyClient
    client = ApifyClient(config.APIFY_API_TOKEN)

    all_reels = []
    for hashtag, cfg in config.HASHTAG_CONFIG.items():
        category = cfg["category"]
        try:
            reels = scrape_hashtag_reels(client, hashtag, category, args.limit, log)
            all_reels.extend(reels)
        except Exception as e:
            log.error(f"[{hashtag}] 수집 실패: {e}")

    log.info(f"전체 릴스 수집: {len(all_reels)}건")
    if all_reels == 0:
        log.warning("릴스 0건. Instagram Scraper가 해당 해시태그에서 Video 타입을 찾지 못했을 수 있습니다.")
        log.warning("Tip: Apify Console에서 직접 Actor를 테스트해보세요.")

    save_json(all_reels, "01_reels_raw.json")
    log.info("저장 완료: data/01_reels_raw.json")

    if args.debug and all_reels:
        log.debug(f"첫 번째 릴스 키: {list(all_reels[0].keys())}")


if __name__ == "__main__":
    main()
