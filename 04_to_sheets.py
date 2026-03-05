"""
Step 4: Google Sheets 업로드 (시트 4개)
입력: data/02_filtered_reels.json, data/03_creator_ranking.json, data/07_content_suggestion.json(선택)
출력: Google Sheets
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import config
from utils import setup_logging, load_json


def build_reels_rows(reels: list) -> tuple[list, list]:
    """포스트_Top 시트 헤더 + 데이터 행 생성 (이미지/캐러셀/릴스 혼합)."""
    headers = [
        "해시태그", "카테고리", "유형", "크리에이터", "캡션(200자)",
        "조회수", "좋아요", "댓글", "인게이지먼트", "조회대비(%)",
        "음원_아티스트", "음원_제목", "영상URL", "포스트URL", "날짜",
    ]
    rows = []
    for r in reels:
        music = r.get("musicInfo") or {}
        if isinstance(music, str):
            music = {}
        rows.append([
            r.get("hashtag_source", ""),
            r.get("hashtag_category", ""),
            r.get("content_type") or r.get("type") or "",
            r.get("ownerUsername", ""),
            (r.get("caption") or "")[:200],
            r.get("videoPlayCount") or 0,
            r.get("likesCount") or 0,
            r.get("commentsCount") or 0,
            r.get("engagement_score") or 0,
            r.get("engagement_to_views") or 0,
            music.get("artistName", ""),
            music.get("songName", ""),
            r.get("videoUrl") or "",
            r.get("url") or "",
            r.get("timestamp") or "",
        ])
    return headers, rows


def build_creator_rows(creators: list) -> tuple[list, list]:
    """크리에이터_랭킹 시트 헤더 + 데이터 행 생성."""
    headers = [
        "크리에이터", "출현횟수", "평균조회수", "평균인게이지먼트",
        "총조회수", "총인게이지먼트", "해시태그들", "카테고리들",
        "복수해시태그", "대표릴스URL", "대표릴스조회수", "대표릴스캡션",
    ]
    rows = []
    for c in creators:
        rows.append([
            c.get("username", ""),
            c.get("appearance_count", 0),
            c.get("avg_views", 0),
            c.get("avg_engagement", 0),
            c.get("total_views", 0),
            c.get("total_engagement", 0),
            ", ".join(c.get("hashtags") or []),
            ", ".join(c.get("categories") or []),
            "Y" if c.get("multi_hashtag") else "N",
            c.get("best_reel_url", ""),
            c.get("best_reel_views", 0),
            c.get("best_reel_caption", ""),
        ])
    return headers, rows


def build_trend_rows(reels: list) -> tuple[list, list]:
    """트렌드_요약 시트 헤더 + 데이터 행 생성."""
    headers = [
        "해시태그", "카테고리", "릴스수", "평균조회수",
        "평균인게이지먼트", "최고조회수", "주요크리에이터",
    ]

    by_hashtag: dict[str, list] = defaultdict(list)
    for r in reels:
        by_hashtag[r.get("hashtag_source", "기타")].append(r)

    rows = []
    for hashtag, items in by_hashtag.items():
        views = [i.get("videoPlayCount") or 0 for i in items]
        engs = [i.get("engagement_score") or 0 for i in items]
        creators = list({i.get("ownerUsername", "") for i in items})[:3]
        rows.append([
            hashtag,
            config.HASHTAG_CONFIG.get(hashtag, {}).get("category", ""),
            len(items),
            round(sum(views) / len(views)) if views else 0,
            round(sum(engs) / len(engs)) if engs else 0,
            max(views) if views else 0,
            ", ".join(creators),
        ])
    return headers, rows


def build_suggest_rows(suggestion: dict) -> tuple[list, list]:
    """AI_제안 시트 헤더 + 데이터 행 생성 (Step 7 결과)."""
    headers = ["항목", "내용"]
    hook_examples = suggestion.get("hook_example") or []
    if isinstance(hook_examples, list):
        hook_str = "\n".join(f"• {h}" for h in hook_examples)
    else:
        hook_str = str(hook_examples)

    rows = [
        ["핵심 한 줄 전략", suggestion.get("one_liner", "")],
        ["왜 먹히는가", suggestion.get("why", "")],
        ["훅 예시", hook_str],
        ["댓글 인사이트", suggestion.get("comment_insight", "")],
        ["킬러 키워드 활용법", suggestion.get("killer_keyword", "")],
    ]
    return headers, rows


def rename_sheet_if_exists(spreadsheet, old_title: str, new_title: str, log) -> None:
    """기존 시트 이름이 old_title이면 new_title로 변경."""
    for ws in spreadsheet.worksheets():
        if ws.title == old_title:
            ws.update_title(new_title)
            log.info(f"  시트 이름 변경: '{old_title}' → '{new_title}'")
            return


def upload_sheet(ws, headers: list, rows: list, log) -> None:
    """워크시트를 클리어하고 헤더 + 데이터 업로드."""
    ws.clear()
    all_rows = [headers] + rows
    ws.update(all_rows, value_input_option="USER_ENTERED")
    log.info(f"  '{ws.title}' 업로드 완료 ({len(rows)}행)")


def main():
    parser = argparse.ArgumentParser(description="Step 4: Google Sheets 업로드")
    parser.add_argument("--dry-run", action="store_true", help="업로드 없이 데이터 확인")
    parser.add_argument("--sheet-id", default=None, help="스프레드시트 ID 직접 지정")
    parser.add_argument("--debug", action="store_true", help="상세 로그 출력")
    args = parser.parse_args()

    log = setup_logging(args.debug)
    log.info("=" * 50)
    log.info("Step 4: Google Sheets 업로드")
    log.info("=" * 50)

    reels = load_json("02_filtered_reels.json")
    creators = load_json("03_creator_ranking.json")
    log.info(f"포스트 {len(reels)}건 / 크리에이터 {len(creators)}명 로드")

    # Step 7 결과 로드 (없으면 스킵)
    suggest_path = config.DATA_DIR / "07_content_suggestion.json"
    suggestion = None
    if suggest_path.exists():
        with open(suggest_path, encoding="utf-8") as f:
            suggestion = json.load(f)
        log.info("Step 7 제안 데이터 로드 완료")
    else:
        log.info("Step 7 데이터 없음 — AI_제안 시트 스킵 (07_content_suggest.py 실행 후 재업로드)")

    reels_headers, reels_rows = build_reels_rows(reels)
    creator_headers, creator_rows = build_creator_rows(creators)
    trend_headers, trend_rows = build_trend_rows(reels)

    if args.dry_run:
        log.info("[DRY-RUN] 업로드 스킵 — 데이터 미리보기:")
        log.info(f"  포스트_Top: {len(reels_rows)}행, 헤더={reels_headers}")
        log.info(f"  크리에이터_랭킹: {len(creator_rows)}행")
        log.info(f"  트렌드_요약: {len(trend_rows)}행")
        if suggestion:
            log.info(f"  AI_제안: {suggestion.get('one_liner','')[:60]}...")
        return

    cred_path = config.GOOGLE_SHEETS_CRED_PATH
    sheet_id = args.sheet_id or config.GOOGLE_SPREADSHEET_ID

    if not sheet_id:
        log.error("GOOGLE_SPREADSHEET_ID 환경변수 또는 --sheet-id 인자가 필요합니다.")
        sys.exit(1)

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        log.error("pip install gspread google-auth 를 먼저 실행하세요.")
        sys.exit(1)

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(cred_path, scopes=scopes)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(sheet_id)

    # 기존 "릴스_Top" → "포스트_Top" 이름 변경
    rename_sheet_if_exists(spreadsheet, "릴스_Top", "포스트_Top", log)

    sheet_map = {
        "포스트_Top": (reels_headers, reels_rows),
        "크리에이터_랭킹": (creator_headers, creator_rows),
        "트렌드_요약": (trend_headers, trend_rows),
    }
    if suggestion:
        sug_headers, sug_rows = build_suggest_rows(suggestion)
        sheet_map["AI_제안"] = (sug_headers, sug_rows)

    existing = {ws.title: ws for ws in spreadsheet.worksheets()}
    for title, (headers, rows) in sheet_map.items():
        ws = existing.get(title) or spreadsheet.add_worksheet(title=title, rows=100, cols=10)
        upload_sheet(ws, headers, rows, log)

    log.info(f"모든 시트 업로드 완료: {list(sheet_map.keys())}")


if __name__ == "__main__":
    main()
