import multiprocessing
import os
import sys
import time

from aiohttp import web

# Импортируем функции запуска из файлов ботов
from bot_vk_1 import run_bot_vk_1
from bot_vk_2 import run_bot_vk_2
from bot_mail import run_bot_mail
from bot_max import run_bot_max

# Логи сразу попадают в Render, а не копятся в буфере процесса
sys.stdout.reconfigure(line_buffering=True)

BOTS = [run_bot_vk_1, run_bot_vk_2, run_bot_mail, run_bot_max]
START_DELAY = 20      # пауза между запусками ботов, сек (против Flood control)
RESTART_DELAY = 300   # через сколько секунд после падения перезапускать бота


# ==========================================
#     ВЕБ-СЕРВЕР (порт для Render + пинг)
# ==========================================
async def handle_ping(request):
    return web.Response(text="Супер-Бот (4 в 1) работает стабильно!")


def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    port = int(os.environ.get("PORT", 10000))
    print(f"[SERVER] Веб-сервер запущен на порту {port}")
    web.run_app(app, host='0.0.0.0', port=port, access_log=None)


def start_process(func):
    process = multiprocessing.Process(target=func, name=func.__name__, daemon=True)
    process.start()
    print(f"[SYSTEM] Процесс запущен: {func.__name__}")
    return process


# ==========================================
#               ГЛАВНЫЙ ЗАПУСК
# ==========================================
if __name__ == '__main__':
    print("[SYSTEM] Инициализация всех модулей...")

    # 1. Сначала веб-сервер: Render сразу видит открытый порт
    server = start_process(run_web_server)

    # 2. Потом боты, по одному, с паузой
    processes = {}
    for func in BOTS:
        processes[func] = start_process(func)
        time.sleep(START_DELAY)

    # 3. Присматриваем: упавшего бота перезапускаем, упавший веб-сервер = перезапуск сервиса
    died_at = {}
    try:
        while True:
            time.sleep(30)
            if not server.is_alive():
                print("[SYSTEM] Веб-сервер остановился, выходим (Render перезапустит сервис)")
                sys.exit(1)
            now = time.time()
            for func, process in processes.items():
                if process.is_alive():
                    died_at.pop(func, None)
                    continue
                died_at.setdefault(func, now)
                if now - died_at[func] >= RESTART_DELAY:
                    print(f"[SYSTEM] {func.__name__} остановился (код {process.exitcode}), перезапускаю")
                    processes[func] = start_process(func)
                    died_at.pop(func)
    except KeyboardInterrupt:
        print("[SYSTEM] Остановка. Завершение работы процессов...")
        for process in [server, *processes.values()]:
            process.terminate()
            process.join()
        print("[SYSTEM] Работа завершена.")
