"""Общие помощники для ботов: повторы при Flood control и хранение last_post_id."""
import os
import random
import time

import requests
from vk_api.exceptions import ApiError

# 6 = слишком много запросов в секунду, 9 = Flood control
RETRY_CODES = (6, 9)


def vk_call(method, label="VK", retries=5, base_delay=20, **params):
    """Вызывает метод vk_api (например, vk.wall.get) и повторяет его при Flood control.

    Паузы между попытками: 20, 40, 80, 160 с (плюс 0-10 с случайно).
    Если попытки кончились, исключение уходит наверх, как и раньше.
    """
    for attempt in range(1, retries + 1):
        try:
            return method(**params)
        except ApiError as e:
            if e.code not in RETRY_CODES or attempt == retries:
                raise
            delay = base_delay * 2 ** (attempt - 1) + random.randint(0, 10)
            print(f"[{label}] VK вернул ошибку {e.code}, попытка {attempt}/{retries}, жду {delay} c...", flush=True)
            time.sleep(delay)


# --- Хранение ID последнего поста -------------------------------------------
# На Render файловая система стирается при каждом деплое и рестарте, поэтому
# если заданы UPSTASH_REDIS_REST_URL и UPSTASH_REDIS_REST_TOKEN, ID хранится
# в Redis. Без них используется обычный файл (работает локально, но на Render
# после рестарта будет пустым, и бот просто запомнит текущий пост как стартовый).

def _redis():
    url = os.environ.get("UPSTASH_REDIS_REST_URL")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    if url and token:
        return url.rstrip("/"), {"Authorization": f"Bearer {token}"}
    return None


def load_last_id(key):
    """Возвращает сохранённый ID поста или 0, если ничего не сохранено."""
    redis = _redis()
    if redis:
        url, headers = redis
        try:
            r = requests.get(f"{url}/get/{key}", headers=headers, timeout=10)
            r.raise_for_status()
            value = r.json().get("result")
            return int(value) if value else 0
        except Exception as e:
            print(f"[state] Redis недоступен при чтении '{key}': {e}", flush=True)
    try:
        with open(f"{key}.txt", encoding="utf-8") as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return 0


def save_last_id(key, post_id):
    redis = _redis()
    if redis:
        url, headers = redis
        try:
            r = requests.get(f"{url}/set/{key}/{post_id}", headers=headers, timeout=10)
            r.raise_for_status()
        except Exception as e:
            print(f"[state] Redis недоступен при записи '{key}': {e}", flush=True)
    with open(f"{key}.txt", "w", encoding="utf-8") as f:
        f.write(str(post_id))
