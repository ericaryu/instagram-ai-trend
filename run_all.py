"""
전체 파이프라인 실행
Usage:
  python run_all.py                        # 1~7 전체 실행
  python run_all.py --start 3 --end 6      # Step 3~6만 실행
  python run_all.py --dry-run              # 모든 단계 dry-run
  python run_all.py --skip-sheets          # Step 4 스킵
  python run_all.py --limit 5              # Step 6 분석 릴스 수 제한
"""
import argparse
import subprocess
import sys
import time


STEPS = [
    (1, "01_scrape_top_posts.py", "해시태그 Top Posts 수집"),
    (2, "02_clean_and_filter.py", "데이터 정제 + 필터링"),
    (3, "03_creator_ranking.py", "크리에이터 랭킹"),
    (4, "04_to_sheets.py", "Google Sheets 업로드"),
    (5, "05_transcript.py", "대본 + 댓글 정리"),
    (6, "06_viral_analysis.py", "바이럴 분석 (GPT-4o)"),
    (7, "07_content_suggest.py", "핵심 포인트 제안 (GPT-4o)"),
]


def run_step(script: str, description: str, extra_args: list[str]) -> bool:
    cmd = [sys.executable, script] + extra_args
    print(f"\n{'='*60}")
    print(f"실행: {' '.join(cmd)}")
    print(f"{'='*60}")

    start = time.time()
    result = subprocess.run(cmd)
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n[실패] {description} — 종료 코드 {result.returncode}")
        return False

    print(f"\n[완료] {description} ({elapsed:.1f}초)")
    return True


def main():
    parser = argparse.ArgumentParser(description="전체 파이프라인 실행")
    parser.add_argument("--start", type=int, default=1, help="시작 스텝 번호 (기본: 1)")
    parser.add_argument("--end", type=int, default=7, help="종료 스텝 번호 (기본: 7)")
    parser.add_argument("--dry-run", action="store_true", help="모든 단계 dry-run")
    parser.add_argument("--skip-sheets", action="store_true", help="Step 4 스킵")
    parser.add_argument("--limit", type=int, default=None, help="Step 6 릴스 분석 수 제한")
    parser.add_argument("--fallback", action="store_true", help="Step 1에서 fallback scraper 사용")
    parser.add_argument("--debug", action="store_true", help="모든 단계 debug 로그")
    args = parser.parse_args()

    total_start = time.time()
    failed_steps = []
    skipped_steps = []

    for step_num, script, description in STEPS:
        if step_num < args.start or step_num > args.end:
            continue

        if args.skip_sheets and step_num == 4:
            print(f"\n[SKIP] Step 4: {description} (--skip-sheets)")
            skipped_steps.append(step_num)
            continue

        extra: list[str] = []
        if args.dry_run:
            extra.append("--dry-run")
        if args.debug:
            extra.append("--debug")
        if step_num == 1 and args.fallback:
            extra.append("--fallback")
        if step_num == 6 and args.limit:
            extra.extend(["--limit", str(args.limit)])

        success = run_step(script, description, extra)
        if not success:
            failed_steps.append(step_num)
            print(f"\n파이프라인 중단: Step {step_num} 실패")
            break

    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"파이프라인 완료 (총 {total_elapsed:.1f}초)")
    if skipped_steps:
        print(f"  스킵된 단계: {skipped_steps}")
    if failed_steps:
        print(f"  실패한 단계: {failed_steps}")
        sys.exit(1)
    else:
        print("  모든 단계 성공!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
