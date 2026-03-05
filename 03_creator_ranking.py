"""
Step 3: 크리에이터별 집계 + 랭킹
입력: data/02_filtered_reels.json
출력: data/03_creator_ranking.json
"""
import argparse
from collections import defaultdict

from dotenv import load_dotenv

load_dotenv()

from utils import setup_logging, load_json, save_json


def main():
    parser = argparse.ArgumentParser(description="Step 3: 크리에이터 랭킹")
    parser.add_argument("--debug", action="store_true", help="상세 로그 출력")
    args = parser.parse_args()

    log = setup_logging(args.debug)
    log.info("=" * 50)
    log.info("Step 3: 크리에이터별 집계 + 랭킹")
    log.info("=" * 50)

    reels = load_json("02_filtered_reels.json")
    log.info(f"입력 릴스: {len(reels)}건")

    # 크리에이터별 집계
    creators: dict[str, dict] = defaultdict(lambda: {
        "username": "",
        "reels": [],
        "hashtags": set(),
        "categories": set(),
    })

    for reel in reels:
        username = reel.get("ownerUsername") or "unknown"
        entry = creators[username]
        entry["username"] = username
        entry["reels"].append(reel)
        hashtag = reel.get("hashtag_source")
        category = reel.get("hashtag_category")
        if hashtag:
            entry["hashtags"].add(hashtag)
        if category:
            entry["categories"].add(category)

    # 지표 계산 및 포맷팅
    ranking = []
    for username, entry in creators.items():
        reel_list = entry["reels"]
        views_list = [r.get("videoPlayCount") or 0 for r in reel_list]
        eng_list = [r.get("engagement_score") or 0 for r in reel_list]

        best_reel = max(reel_list, key=lambda r: r.get("engagement_score") or 0)
        caption_preview = (best_reel.get("caption") or "")[:100]

        ranking.append({
            "username": username,
            "appearance_count": len(reel_list),
            "avg_views": round(sum(views_list) / len(views_list)) if views_list else 0,
            "avg_engagement": round(sum(eng_list) / len(eng_list)) if eng_list else 0,
            "total_views": sum(views_list),
            "total_engagement": sum(eng_list),
            "hashtags": sorted(entry["hashtags"]),
            "categories": sorted(entry["categories"]),
            "multi_hashtag": len(entry["hashtags"]) > 1,
            "best_reel_url": best_reel.get("url") or "",
            "best_reel_views": best_reel.get("videoPlayCount") or 0,
            "best_reel_caption": caption_preview,
        })

    # 출현 횟수 → total_engagement 내림차순 정렬
    ranking.sort(key=lambda x: (-x["appearance_count"], -x["total_engagement"]))

    multi_count = sum(1 for c in ranking if c["multi_hashtag"])
    log.info(f"고유 크리에이터: {len(ranking)}명")
    log.info(f"복수 해시태그 등장 크리에이터: {multi_count}명")

    if args.debug:
        for i, c in enumerate(ranking[:5]):
            log.debug(
                f"Top {i+1}: @{c['username']} | "
                f"등장 {c['appearance_count']}회 | "
                f"평균 조회수 {c['avg_views']:,} | "
                f"해시태그: {c['hashtags']}"
            )

    save_json(ranking, "03_creator_ranking.json")
    log.info(f"저장 완료: data/03_creator_ranking.json ({len(ranking)}건)")


if __name__ == "__main__":
    main()
