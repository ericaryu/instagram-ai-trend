"""
Step 1: Apify로 해시태그 Top Posts 수집
출력: data/01_top_posts_raw.json
"""
import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

import config
from utils import setup_logging, save_json

# --- Dry-run dummy data ---
DUMMY_POSTS = [
    {
        "shortCode": "ABC123",
        "url": "https://www.instagram.com/reel/ABC123/",
        "caption": "AI로 업무 자동화하는 방법 #AI #클로드 #자동화",
        "likesCount": 1200,
        "commentsCount": 45,
        "videoPlayCount": 25000,
        "ownerUsername": "ai_creator_kr",
        "type": "Reel",
        "timestamp": "2024-03-01T10:00:00Z",
        "musicInfo": {"artistName": "popular artist", "songName": "trending song"},
        "videoUrl": "https://example.com/video1.mp4",
        "transcript": "안녕하세요, 오늘은 AI로 업무 자동화하는 방법을 알려드릴게요.",
        "latestComments": [
            {"text": "너무 유용해요!", "username": "user1", "likesCount": 10},
            {"text": "저도 써봐야겠어요", "username": "user2", "likesCount": 5},
        ],
        "hashtag_source": "AI",
        "hashtag_category": "AI_일반",
    },
    {
        "shortCode": "DEF456",
        "url": "https://www.instagram.com/reel/DEF456/",
        "caption": "클로드 AI 사용법 완전정복 #클로드 #AI툴 #업무효율",
        "likesCount": 890,
        "commentsCount": 67,
        "videoPlayCount": 18000,
        "ownerUsername": "claude_expert",
        "type": "Reel",
        "timestamp": "2024-03-02T14:00:00Z",
        "musicInfo": None,
        "videoUrl": "https://example.com/video2.mp4",
        "transcript": "",
        "latestComments": [],
        "hashtag_source": "클로드",
        "hashtag_category": "AI_툴",
    },
    {
        "shortCode": "GHI789",
        "url": "https://www.instagram.com/reel/GHI789/",
        "caption": "AI 대학원 합격 후기 솔직하게 #AI대학원 #AI공부",
        "likesCount": 2100,
        "commentsCount": 132,
        "videoPlayCount": 52000,
        "ownerUsername": "ai_grad_story",
        "type": "GraphVideo",
        "timestamp": "2024-03-03T09:00:00Z",
        "musicInfo": {"artistName": "bgm", "songName": "study vibes"},
        "videoUrl": "https://example.com/video3.mp4",
        "transcript": "AI 대학원 지원부터 합격까지 제 경험을 솔직하게 공유할게요.",
        "latestComments": [
            {"text": "학비가 얼마예요?", "username": "user3", "likesCount": 22},
            {"text": "저도 준비 중인데 너무 도움돼요", "username": "user4", "likesCount": 18},
            {"text": "비개발자도 갈 수 있나요?", "username": "user5", "likesCount": 15},
        ],
        "hashtag_source": "AI대학원",
        "hashtag_category": "AI_교육",
    },
]


def scrape_with_analytics(client, hashtag: str, category: str, log) -> list:
    """apify/instagram-hashtag-analytics-scraper로 top posts 수집."""
    log.info(f"[{hashtag}] Analytics Scraper 실행 중...")
    run = client.actor(config.ACTOR_HASHTAG_ANALYTICS).call(
        run_input={"hashtags": [hashtag], "resultsType": "posts", "resultsLimit": 30}
    )
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

    posts = []
    for item in items:
        # top posts가 nested 구조인 경우 flatten
        if "topPosts" in item and isinstance(item["topPosts"], list):
            for post in item["topPosts"]:
                post["hashtag_source"] = hashtag
                post["hashtag_category"] = category
                posts.append(post)
        else:
            item["hashtag_source"] = hashtag
            item["hashtag_category"] = category
            posts.append(item)
    return posts


def scrape_with_fallback(client, hashtag: str, category: str, log) -> list:
    """apify/instagram-hashtag-scraper (fallback) 사용."""
    log.info(f"[{hashtag}] Fallback Scraper 실행 중...")
    run = client.actor(config.ACTOR_HASHTAG_SCRAPER).call(
        run_input={"hashtags": [hashtag], "resultsLimit": 30}
    )
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    for item in items:
        item["hashtag_source"] = hashtag
        item["hashtag_category"] = category
    return items


def main():
    parser = argparse.ArgumentParser(description="Step 1: 해시태그 Top Posts 수집")
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 더미 데이터 사용")
    parser.add_argument("--fallback", action="store_true", help="Hashtag Scraper(fallback) 사용")
    parser.add_argument("--debug", action="store_true", help="상세 로그 출력")
    args = parser.parse_args()

    log = setup_logging(args.debug)
    log.info("=" * 50)
    log.info("Step 1: 해시태그 Top Posts 수집")
    log.info("=" * 50)

    if args.dry_run:
        log.info("[DRY-RUN] 더미 데이터 사용")
        save_json(DUMMY_POSTS, "01_top_posts_raw.json")
        log.info(f"저장 완료: data/01_top_posts_raw.json ({len(DUMMY_POSTS)}건)")
        return

    if not config.APIFY_API_TOKEN:
        log.error("APIFY_API_TOKEN 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    from apify_client import ApifyClient
    client = ApifyClient(config.APIFY_API_TOKEN)

    all_posts = []
    for hashtag, cfg in config.HASHTAG_CONFIG.items():
        category = cfg["category"]
        try:
            if args.fallback:
                posts = scrape_with_fallback(client, hashtag, category, log)
            else:
                posts = scrape_with_analytics(client, hashtag, category, log)
            log.info(f"[{hashtag}] {len(posts)}건 수집")
            if args.debug and posts:
                log.debug(f"[{hashtag}] 첫 번째 항목 키: {list(posts[0].keys())}")
            all_posts.extend(posts)
        except Exception as e:
            log.error(f"[{hashtag}] 수집 실패: {e}")
            if not args.fallback:
                log.info(f"[{hashtag}] --fallback 옵션으로 재시도 추천")

    log.info(f"전체 수집: {len(all_posts)}건")
    save_json(all_posts, "01_top_posts_raw.json")
    log.info("저장 완료: data/01_top_posts_raw.json")


if __name__ == "__main__":
    main()
