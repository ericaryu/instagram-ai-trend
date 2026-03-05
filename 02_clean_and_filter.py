"""
Step 2: 데이터 정제 + 필터링 + 지표 계산
입력: data/01_top_posts_raw.json
출력: data/02_filtered_reels.json
"""
import argparse

from dotenv import load_dotenv

load_dotenv()

import config
from utils import setup_logging, load_json, save_json, get_field


def normalize_fields(item: dict) -> dict:
    """FIELD_ALIASES를 사용해 Apify 출력 필드명을 통일."""
    normalized = {}
    for canonical, _ in config.FIELD_ALIASES.items():
        value = get_field(item, canonical, config.FIELD_ALIASES)
        normalized[canonical] = value
    # 원본 태그 유지
    normalized["hashtag_source"] = item.get("hashtag_source", "")
    normalized["hashtag_category"] = item.get("hashtag_category", "")
    return normalized


def resolve_content_type(item: dict) -> str:
    """Instagram type 값을 reel/image/carousel 중 하나로 변환."""
    raw_type = item.get("type") or ""
    return config.CONTENT_TYPE_MAP.get(raw_type, raw_type.lower() if raw_type else "unknown")


def calculate_engagement(item: dict) -> dict:
    """인게이지먼트 지표 계산 후 추가."""
    likes = item.get("likesCount") or 0
    comments = item.get("commentsCount") or 0
    views = item.get("videoPlayCount") or 0

    item["engagement_score"] = likes + comments
    item["engagement_to_views"] = round((likes + comments) / views * 100, 2) if views > 0 else 0.0
    return item


def main():
    parser = argparse.ArgumentParser(description="Step 2: 데이터 정제 + 필터링")
    parser.add_argument("--min-views", type=int, default=config.MIN_VIEWS, help="최소 조회수 기준")
    parser.add_argument("--debug", action="store_true", help="상세 로그 출력")
    args = parser.parse_args()

    log = setup_logging(args.debug)
    log.info("=" * 50)
    log.info("Step 2: 데이터 정제 + 필터링 + 지표 계산")
    log.info("=" * 50)

    raw = load_json("01_top_posts_raw.json")
    log.info(f"원본 데이터: {len(raw)}건")

    # 1. 필드 정규화
    normalized = [normalize_fields(item) for item in raw]
    if args.debug:
        log.debug(f"정규화 후 키: {list(normalized[0].keys()) if normalized else []}")

    # 2. 콘텐츠 유형 분류 및 릴스 필터링
    type_counts: dict[str, int] = {}
    typed = []
    for item in normalized:
        ctype = resolve_content_type(item)
        item["content_type"] = ctype
        type_counts[ctype] = type_counts.get(ctype, 0) + 1
        typed.append(item)

    log.info(f"콘텐츠 유형 분포: {type_counts}")
    reels_only = [i for i in typed if i["content_type"] in config.TARGET_CONTENT_TYPES]
    log.info(f"릴스 필터 후: {len(reels_only)}건")

    # 3. 조회수 컷오프
    before_cut = len(reels_only)
    reels_only = [i for i in reels_only if (i.get("videoPlayCount") or 0) >= args.min_views]
    log.info(f"조회수 {args.min_views:,} 컷 후: {len(reels_only)}건 (제거: {before_cut - len(reels_only)}건)")

    if not reels_only:
        log.warning("필터 후 0건. --min-views를 낮추거나 Step 1 데이터를 확인하세요.")

    # 4. 중복 제거 (shortCode 기준)
    seen: set[str] = set()
    deduped = []
    for item in reels_only:
        code = item.get("shortCode") or item.get("url", "")
        if code and code not in seen:
            seen.add(code)
            deduped.append(item)
    log.info(f"중복 제거 후: {len(deduped)}건 (제거: {len(reels_only) - len(deduped)}건)")

    # 5. 인게이지먼트 계산
    deduped = [calculate_engagement(item) for item in deduped]

    # 6. engagement_score 내림차순 정렬
    deduped.sort(key=lambda x: x["engagement_score"], reverse=True)

    if args.debug:
        for i, item in enumerate(deduped[:3]):
            log.debug(
                f"Top {i+1}: @{item.get('ownerUsername')} | "
                f"views={item.get('videoPlayCount'):,} | "
                f"eng={item['engagement_score']:,} | "
                f"eng_rate={item['engagement_to_views']}%"
            )

    save_json(deduped, "02_filtered_reels.json")
    log.info(f"저장 완료: data/02_filtered_reels.json ({len(deduped)}건)")


if __name__ == "__main__":
    main()
