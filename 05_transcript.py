"""
Step 5: 대본(transcript) + 댓글 정리 + 콘텐츠 요약 생성
입력: data/02_filtered_reels.json
출력: data/05_with_transcript.json
"""
import argparse
import re
from collections import Counter

from dotenv import load_dotenv

load_dotenv()

from utils import setup_logging, load_json, save_json

STOPWORDS = {
    "이", "가", "은", "는", "을", "를", "의", "에", "와", "과",
    "도", "로", "으로", "에서", "이다", "있다", "하다", "이고",
    "the", "and", "for", "that", "this", "with", "are", "was",
}


def extract_hashtags(caption: str) -> list[str]:
    return re.findall(r"#(\w+)", caption or "")


def clean_caption(caption: str) -> str:
    text = re.sub(r"#\w+", "", caption or "")
    text = re.sub(r"@\w+", "", text)
    return text.strip()


def extract_comment_themes(comments: list[dict], top_n: int = 10) -> list[dict]:
    """댓글 텍스트에서 핵심 키워드 추출 (한글 2자+, 영문 3자+, 2회 이상)."""
    all_words: list[str] = []
    for c in comments:
        text = c.get("text") or ""
        # 한글 단어
        all_words.extend(re.findall(r"[가-힣]{2,}", text))
        # 영문 단어
        all_words.extend(re.findall(r"[a-zA-Z]{3,}", text.lower()))

    filtered = [w for w in all_words if w not in STOPWORDS]
    counter = Counter(filtered)
    return [{"word": word, "count": cnt} for word, cnt in counter.most_common(top_n) if cnt >= 2]


def build_content_summary(reel: dict) -> str:
    """캡션 + 나레이션 + 댓글을 LLM에 넘길 통합 요약 텍스트로 조합."""
    parts = []

    clean = reel.get("clean_caption", "").strip()
    if clean:
        parts.append(f"[캡션] {clean}")

    transcript = reel.get("transcript", "")
    if transcript and isinstance(transcript, str) and transcript.strip():
        parts.append(f"[나레이션] {transcript.strip()}")

    comments = reel.get("comments_cleaned", [])
    if comments:
        lines = [f"@{c.get('username', '?')}: {c.get('text', '')}" for c in comments]
        parts.append("[댓글 반응]\n" + "\n".join(lines))

    return "\n\n".join(parts) if parts else "(내용 없음)"


def process_reel(reel: dict) -> dict:
    """릴스 하나에 transcript/댓글/캡션 관련 필드를 추가."""
    # Transcript
    transcript_raw = reel.get("transcript")
    has_transcript = bool(transcript_raw and isinstance(transcript_raw, str) and transcript_raw.strip())
    reel["has_transcript"] = has_transcript

    # 댓글 추출
    raw_comments = reel.get("latestComments") or []
    if not isinstance(raw_comments, list):
        raw_comments = []

    comments_cleaned = []
    for c in raw_comments[:10]:
        if isinstance(c, dict):
            comments_cleaned.append({
                "text": c.get("text") or c.get("comment") or "",
                "username": c.get("username") or c.get("ownerUsername") or "",
                "likes": c.get("likesCount") or c.get("likes") or 0,
            })

    reel["comments_cleaned"] = comments_cleaned
    reel["comments_count_actual"] = len(comments_cleaned)
    reel["comment_summary"] = " | ".join(c["text"] for c in comments_cleaned if c["text"])
    reel["comment_themes"] = extract_comment_themes(comments_cleaned)

    # 캡션 처리
    caption = reel.get("caption") or ""
    reel["extracted_hashtags"] = extract_hashtags(caption)
    reel["clean_caption"] = clean_caption(caption)

    # 통합 요약
    reel["content_summary"] = build_content_summary(reel)

    return reel


def main():
    parser = argparse.ArgumentParser(description="Step 5: 대본 + 댓글 정리")
    parser.add_argument("--debug", action="store_true", help="상세 로그 출력")
    args = parser.parse_args()

    log = setup_logging(args.debug)
    log.info("=" * 50)
    log.info("Step 5: 대본 + 댓글 정리 + 콘텐츠 요약")
    log.info("=" * 50)

    reels = load_json("02_filtered_reels.json")
    log.info(f"입력 릴스: {len(reels)}건")

    processed = [process_reel(reel) for reel in reels]

    has_trans = sum(1 for r in processed if r["has_transcript"])
    has_comments = sum(1 for r in processed if r["comments_count_actual"] > 0)
    log.info(f"transcript 보유: {has_trans}/{len(processed)}건")
    log.info(f"댓글 보유: {has_comments}/{len(processed)}건")

    if has_comments == 0:
        log.warning("댓글 데이터 없음. Apify 키워드 모드 또는 Reel Scraper 사용을 검토하세요.")

    if args.debug and processed:
        log.debug(f"content_summary 샘플:\n{processed[0].get('content_summary')}")

    save_json(processed, "05_with_transcript.json")
    log.info(f"저장 완료: data/05_with_transcript.json ({len(processed)}건)")


if __name__ == "__main__":
    main()
