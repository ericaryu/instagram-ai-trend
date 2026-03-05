"""
Step 6: "왜 떴는지" 바이럴 분석 (GPT-4o)
입력: data/05_with_transcript.json
출력: data/06_viral_analysis.json
"""
import argparse
import json
import re
import sys
import time

from dotenv import load_dotenv

load_dotenv()

import config
from utils import setup_logging, load_json, save_json

DUMMY_ANALYSIS = {
    "hook": "AI로 업무 시간을 절반으로 줄였다는 충격적인 숫자 제시",
    "topic": "AI 자동화 실무 적용, 타겟: 직장인/마케터",
    "format": "비포/애프터 - 전후 비교 포맷",
    "tone": "실용 + FOMO (나만 모르는 거 아닌가 불안감)",
    "viral_factor": "구체적 수치 + 비개발자도 할 수 있다는 공감 포인트",
}


def build_analysis_prompt(reel: dict) -> str:
    return f"""당신은 한국 AI 콘텐츠 시장을 잘 아는 인스타 릴스 바이럴 분석가입니다.

아래 인스타그램 릴스 데이터를 보고, 이 영상이 왜 높은 반응을 얻었는지
자유롭게 분석해주세요.

## 릴스 데이터
- 해시태그: {reel.get('hashtag_source', '')} (카테고리: {reel.get('hashtag_category', '')})
- 조회수: {reel.get('videoPlayCount', 0):,} / 좋아요: {reel.get('likesCount', 0):,} / 댓글: {reel.get('commentsCount', 0):,}
- 조회 대비 인게이지먼트: {reel.get('engagement_to_views', 0)}%

## 콘텐츠 내용
{reel.get('content_summary', '(내용 없음)')}

## 분석 요청
이 영상이 왜 떴는지 자유롭게 분석하되,
반드시 아래 5가지 관점은 포함해주세요:

1. hook — 첫 1-3초의 시선 집중 장치를 "시선집중 → 호기심증폭 → 가치약속"
   프레임으로 분해해줘. 세 단계 중 어디가 강했고, 어디가 빠졌는지도.
2. topic — 어떤 AI 세부 주제를 다루는지, 타겟 시청자는 누구인지.
3. format — 튜토리얼 / 비포애프터 / 리스트형 / 스토리텔링 / 비교 / 밈 중
   어디에 해당하는지, 그 포맷이 이 주제에 왜 잘 맞았는지.
4. tone — 감정 톤(놀라움/실용/유머/공감/FOMO 등)과
   그 톤이 타겟 시청자의 어떤 심리를 건드렸는지.
5. viral_factor — 위 4가지를 종합해서,
   이 영상이 특히 잘 된 핵심 이유 1가지.
   그리고 "시청자가 왜 끝까지 봤을지" 이유도 한 줄로 추정해줘.

각 항목 1-2문장으로 간결하게. 한국어로 답변.
JSON 형식으로:
{{"hook": "...", "topic": "...", "format": "...", "tone": "...", "viral_factor": "..."}}"""


def parse_analysis_response(content: str) -> dict:
    """GPT 응답에서 JSON 파싱. 실패 시 원문 텍스트 그대로 저장."""
    content = content.strip()
    # 마크다운 코드 블록 제거
    if content.startswith("```"):
        content = re.sub(r"^```[a-z]*\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_response": content, "parse_error": True}


def analyze_reel(client, reel: dict, log) -> dict:
    """릴스 1개 GPT-4o 바이럴 분석."""
    prompt = build_analysis_prompt(reel)

    if prompt is None:
        log.warning(f"  [{reel.get('shortCode')}] build_analysis_prompt가 None 반환 — TODO(human) 미구현")
        return {**reel, "viral_analysis": {"error": "prompt not implemented"}}

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 한국 SNS 트렌드 전문 분석가입니다."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        analysis = json.loads(response.choices[0].message.content)
    except Exception as e:
        log.error(f"  [{reel.get('shortCode')}] 분석 실패: {e}")
        analysis = {"error": str(e)}

    return {**reel, "viral_analysis": analysis}


def main():
    parser = argparse.ArgumentParser(description="Step 6: 바이럴 분석 (GPT-4o)")
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 더미 분석")
    parser.add_argument("--limit", type=int, default=None, help="분석할 릴스 수 제한 (비용 절약)")
    parser.add_argument("--debug", action="store_true", help="상세 로그 출력")
    args = parser.parse_args()

    log = setup_logging(args.debug)
    log.info("=" * 50)
    log.info("Step 6: 바이럴 분석 (GPT-4o)")
    log.info("=" * 50)

    reels = load_json("05_with_transcript.json")
    if args.limit:
        reels = reels[: args.limit]
        log.info(f"분석 대상: {len(reels)}건 (--limit {args.limit})")
    else:
        log.info(f"분석 대상: {len(reels)}건")

    if args.dry_run:
        log.info("[DRY-RUN] 더미 분석 사용")
        result = [{**r, "viral_analysis": DUMMY_ANALYSIS} for r in reels]
        save_json(result, "06_viral_analysis.json")
        log.info(f"저장 완료: data/06_viral_analysis.json ({len(result)}건)")
        return

    if not config.OPENAI_API_KEY:
        log.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    import re
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    analyzed = []
    for i, reel in enumerate(reels):
        log.info(f"분석 중 ({i+1}/{len(reels)}): @{reel.get('ownerUsername')} [{reel.get('shortCode')}]")
        result = analyze_reel(client, reel, log)
        analyzed.append(result)
        if args.debug:
            log.debug(f"  결과: {result.get('viral_analysis')}")
        if i < len(reels) - 1:
            time.sleep(0.5)  # rate limit 방지

    save_json(analyzed, "06_viral_analysis.json")
    log.info(f"저장 완료: data/06_viral_analysis.json ({len(analyzed)}건)")


if __name__ == "__main__":
    main()
