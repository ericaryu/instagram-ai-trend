import json
import logging
import sys
import time
from functools import wraps
from pathlib import Path

from config import DATA_DIR


def setup_logging(debug: bool = False) -> logging.Logger:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("pipeline")


def load_json(filename: str) -> list | dict:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"입력 파일 없음: {path}\n이전 단계를 먼저 실행하세요.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data: list | dict, filename: str) -> Path:
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def step_runner(step_num: int, input_file: str | None, output_file: str):
    """
    Decorator for pipeline step functions.

    Usage:
        @step_runner(step_num=2, input_file="01_top_posts_raw.json", output_file="02_filtered_reels.json")
        def run(data, args, log):
            ...
            return result
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(args):
            log = setup_logging(getattr(args, "debug", False))
            log.info(f"{'='*50}")
            log.info(f"Step {step_num} 시작")
            log.info(f"{'='*50}")

            input_data = None
            if input_file:
                try:
                    input_data = load_json(input_file)
                    log.info(f"입력 로드: {input_file} ({len(input_data) if isinstance(input_data, list) else 1}건)")
                except FileNotFoundError as e:
                    log.error(str(e))
                    sys.exit(1)

            start = time.time()
            result = fn(input_data, args, log)
            elapsed = time.time() - start

            if result is not None:
                path = save_json(result, output_file)
                count = len(result) if isinstance(result, list) else 1
                log.info(f"저장 완료: {path} ({count}건, {elapsed:.1f}초)")
            else:
                log.warning("결과 없음 — 저장 스킵")

            return result
        return wrapper
    return decorator


def get_field(item: dict, canonical_key: str, aliases: dict) -> any:
    """FIELD_ALIASES를 사용해 여러 키 이름에서 값을 찾아 반환."""
    for key in aliases.get(canonical_key, [canonical_key]):
        if key in item:
            return item[key]
    return None
