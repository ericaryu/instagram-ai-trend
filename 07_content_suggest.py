"""
Step 7: 핵심 포인트 하나 제안 (GPT-4o)
입력: data/06_viral_analysis.json
출력: data/07_content_suggestion.json
"""
import argparse
import json
import sys

from dotenv import load_dotenv

load_dotenv()

import config
from utils import setup_logging, load_json, save_json

DUMMY_SUGGESTION = {
    "one_liner": (
        "'AI 대학원 3천만원 쓴 사람이 다시 돌아가면 절대 안 할 행동' 이 훅으로 시작해서 "
        "비개발자가 자동화 파이프라인 만든 실화로 마무리하면 팔로우 유도까지 자연스럽게 된다."
    ),
    "why": (
        "수집된 릴스에서 '숫자+개인 경험' 조합이 가장 높은 조회수를 기록함. "
        "댓글에서 '비개발자도 가능한지' 질문이 반복 등장 → 이 불안을 직접 건드리는 것이 핵심."
    ),
    "hook_example": [
        "AI 대학원 3천만원 태우고 나서야 알게 된 것 (feat. 비개발자 생존기)",
        "최연소 팀장이 업무 자동화에 쓴 AI 툴 TOP 3 — 개발 1도 모르는데 가능한 이유",
    ],
    "comment_insight": (
        "댓글에서 '학비', '비개발자', '자동화' 키워드 반복 등장. "
        "사람들은 진입 장벽을 궁금해함 → '나도 할 수 있어?' 확신을 주는 콘텐츠가 팔림."
    ),
    "killer_keyword": (
        "'비개발자'를 훅에 반드시 포함. '극도의 효율'은 영상 중반 자동화 결과 보여줄 때 사용. "
        "'AI 대학원 3천만원'은 신뢰도 + FOMO 동시 자극."
    ),
}


def build_suggestion_prompt(reels: list) -> str:
    """Step 6 전체 분석 + 에리카 프로필로 핵심 포인트 1개 도출하는 프롬프트."""
    profile = config.ERICA_PROFILE

    # 릴스 트렌드 요약 (상위 10개만)
    trend_lines = []
    for i, r in enumerate(reels[:10]):
        analysis = r.get("viral_analysis") or {}
        comments_info = ""
        if r.get("comments_count_actual", 0) > 0:
            themes = r.get("comment_themes") or []
            keywords = ", ".join(t["word"] for t in themes[:5])
            comments_info = f"\n    댓글 키워드: {keywords}"
            sample_comments = [c["text"] for c in (r.get("comments_cleaned") or [])[:3]]
            if sample_comments:
                comments_info += f"\n    댓글 원문: {' | '.join(sample_comments)}"

        trend_lines.append(
            f"{i+1}. @{r.get('ownerUsername')} "
            f"(조회수 {r.get('videoPlayCount', 0):,}, 인게이지먼트 {r.get('engagement_score', 0):,})\n"
            f"    훅: {analysis.get('hook', 'N/A')}\n"
            f"    포맷: {analysis.get('format', 'N/A')}\n"
            f"    톤: {analysis.get('tone', 'N/A')}\n"
            f"    바이럴 요인: {analysis.get('viral_factor', 'N/A')}"
            f"{comments_info}"
        )

    trend_summary = "\n\n".join(trend_lines)

    return f"""당신은 한국 SNS 크리에이터 전략 전문가입니다.

[에리카 프로필]
- 포지셔닝: {profile['positioning']}
- 직무: {profile['role']}
- 강점: {profile['strengths']}
- 킬러 키워드: {', '.join(profile['killer_keywords'])}
- 톤: {profile['tone']}
- 타겟: {profile['target']}

[인스타그램 AI 릴스 트렌드 데이터]
총 {len(reels)}개 릴스 분석 결과입니다.

{trend_summary}

---

5개 아이디어 같은 거 필요 없어요. 딱 하나, 핵심 포인트만 찾아주세요.

이런 느낌이에요:
- "어떤 시점에 'AI 공부에 3천만원 쓴 사람이 다시 돌아가면 절대 안 할 행동' 이런 식으로 말하면 조회수 늘릴 거다"
- "'최연소 팀장' 같은 키워드가 시청 지속하게 할 거다"
- "~~하면 팔로우 유도할 수 있을 거야"

댓글 데이터가 있다면 반드시 활용하세요:
- 댓글에서 사람들이 뭘 궁금해하는지, 뭘 공감하는지 분석
- "이 포인트를 건드리면 댓글에서 나온 관심사를 자극할 수 있다"

다음 JSON 형식으로만 답변하세요 (한국어로):
{{
  "one_liner": "핵심 한 줄 전략 (2-3문장)",
  "why": "왜 이게 먹히는지 근거 (트렌드 데이터 + 댓글 반응 기반)",
  "hook_example": ["실제로 쓸 수 있는 훅 대사 예시 1", "예시 2"],
  "comment_insight": "댓글에서 발견한 인사이트. 없으면 '댓글 데이터 부족'",
  "killer_keyword": "에리카의 킬러 키워드 중 어떤 걸 어떻게 쓸지"
}}"""


def main():
    parser = argparse.ArgumentParser(description="Step 7: 핵심 포인트 1개 제안")
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 더미 결과")
    parser.add_argument("--debug", action="store_true", help="상세 로그 출력")
    args = parser.parse_args()

    log = setup_logging(args.debug)
    log.info("=" * 50)
    log.info("Step 7: 핵심 포인트 1개 제안 (GPT-4o)")
    log.info("=" * 50)

    reels = load_json("06_viral_analysis.json")
    log.info(f"분석 대상 릴스: {len(reels)}건")

    if args.dry_run:
        log.info("[DRY-RUN] 더미 제안 사용")
        save_json(DUMMY_SUGGESTION, "07_content_suggestion.json")
        log.info("저장 완료: data/07_content_suggestion.json")
        log.info("\n=== 핵심 포인트 ===")
        log.info(DUMMY_SUGGESTION["one_liner"])
        return

    if not config.OPENAI_API_KEY:
        log.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    prompt = build_suggestion_prompt(reels)
    if args.debug:
        log.debug(f"프롬프트 길이: {len(prompt)}자")

    log.info("GPT-4o 호출 중...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 한국 SNS 크리에이터 전략 전문가입니다."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        suggestion = json.loads(response.choices[0].message.content)
    except Exception as e:
        log.error(f"GPT 호출 실패: {e}")
        sys.exit(1)

    save_json(suggestion, "07_content_suggestion.json")
    log.info("저장 완료: data/07_content_suggestion.json")
    log.info("\n=== 핵심 포인트 ===")
    log.info(suggestion.get("one_liner", ""))
    if args.debug:
        log.debug(f"\n전체 결과:\n{json.dumps(suggestion, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    main()
