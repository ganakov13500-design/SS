import vk_api
import time
import os
import builtins
import random

from vk_utils import vk_call, load_last_id, save_last_id

# --- ХАК ДЛЯ ПРИНУДИТЕЛЬНОГО ВЫВОДА ЛОГОВ В RENDER ---
def print(*args, **kwargs):
    kwargs['flush'] = True
    builtins.print(*args, **kwargs)
# -----------------------------------------------------

# 1. ТОКЕН ДЛЯ ЧТЕНИЯ (фейковый/дополнительный аккаунт)
READ_TOKEN = 'vk1.a.UQQypBdwlUwwk6O3z7iJAXc8Tnzx6VcB3seRHXgioyrLDLW-xYTXy7SCqONeAc7FOuadlIg1u52uEVFGrKvjCZmV-wq70J2TG_MqZKtn7aXkudTIrURT-OG2bzB1neTWwkHAM-buqJIWLYT8ioGLy6EiL84LamSMjstFgw1ynkXR_sCGZsspN2zbF5P9chaLu98ONjvbDVGk67_j1-CURw'

# 2. ТОКЕН ДЛЯ ПУБЛИКАЦИИ (Новый токен вашей группы)
WRITE_TOKEN = 'vk1.a.toKd8FuijClshyBhhwOz5WT5StVS5wYcLQsqYzkcdVWDpBlRp3IE_bVAB2VMf4tjXbLaHKzkXIiqz49d9fLsu0lPeRmqYMBZ04aQQ-uorhHqEwra5XnaECvHFFteN5dUvbbpQh6iz0kl-fb4a8-xLhgK0TTna73UXqT51w_iBmciiqNBTiYl012SceQMdZqHK339pfLPyEg7qpi0-ElR6Q'

SOURCE_GROUP_ID = -218341918  
TARGET_GROUP_IDS = [-225274463]  
CHECK_INTERVAL = 300  
STATE_KEY = 'vk_bot_1'

def get_saved_last_post_id():
    return load_last_id(STATE_KEY)

def save_last_post_id(post_id):
    save_last_id(STATE_KEY, post_id)

def run_bot_vk_1():
    print("Авторизация ВКонтакте (Бот 1)...")
    
    # Инициализация сессии для ЧТЕНИЯ (донора)
    try:
        vk_read_session = vk_api.VkApi(token=READ_TOKEN)
        vk_reader = vk_read_session.get_api()
        print("[Успех] Бот 1: Сессия для чтения создана.")
    except Exception as e:
        print(f"[Фатальная Ошибка] Бот 1: Ошибка читающего аккаунта. Детали: {e}")
        return

    # Инициализация сессии для ПУБЛИКАЦИИ (группа)
    try:
        vk_write_session = vk_api.VkApi(token=WRITE_TOKEN)
        vk_writer = vk_write_session.get_api()
        print(f"[Успех] Бот 1: Сессия публикации для группы {TARGET_GROUP_IDS[0]} успешно авторизована.")
    except Exception as e:
        print(f"[Фатальная Ошибка] Бот 1: Ошибка сессии публикации. Детали: {e}")
        return

    last_post_id = get_saved_last_post_id()
    print(f"Бот ВК 1 запущен. Последний сохраненный пост: {last_post_id}")

    while True:
        try:
            # Читаем через vk_reader (токен чтения)
            response = vk_call(vk_reader.wall.get, label="Бот 1", owner_id=SOURCE_GROUP_ID, count=2)
            posts = response['items']
            if not posts:
                print(f"[Бот 1] Стена пуста. Ожидание...")
                time.sleep(CHECK_INTERVAL)
                continue

            current_post = next((p for p in posts if not p.get('is_pinned')), posts[0])
            current_post_id = current_post['id']

            if last_post_id == 0:
                last_post_id = current_post_id
                save_last_post_id(last_post_id)
                print(f"[Бот 1] Первый запуск. Запомнили пост: {last_post_id}. Ждем новые.")
            
            elif current_post_id <= last_post_id:
                # Тихо ждем, если новых постов нет
                pass
                
            elif current_post_id > last_post_id:
                print(f"\n[Бот 1] НАЙДЕН НОВЫЙ ПОСТ: {current_post_id}! Подготовка к копированию...")
                post_text = current_post.get('text', '')
                attachments_list = []
                
                # --- УЛУЧШЕННАЯ ФУНКЦИЯ ИЗВЛЕЧЕНИЯ МЕДИА ---
                def extract_attachments(attachments_data):
                    extracted = []
                    for att in attachments_data:
                        att_type = att.get('type')
                        if att_type in ['photo', 'video', 'doc', 'audio']:
                            item = att.get(att_type, {})
                            owner_id = item.get('owner_id')
                            media_id = item.get('id')
                            
                            # Безопасная проверка на None
                            if owner_id is not None and media_id is not None:
                                att_str = f"{att_type}{owner_id}_{media_id}"
                                if item.get('access_key'): 
                                    att_str += f"_{item.get('access_key')}"
                                extracted.append(att_str)
                    return extracted

                # 1. Извлекаем медиа из обычного поста
                if 'attachments' in current_post:
                    attachments_list.extend(extract_attachments(current_post['attachments']))
                
                # 2. Обработка репоста (copy_history)
                if 'copy_history' in current_post and len(current_post['copy_history']) > 0:
                    repost = current_post['copy_history'][0]
                    if not post_text and repost.get('text'):
                        post_text = repost['text']
                    if 'attachments' in repost:
                        attachments_list.extend(extract_attachments(repost['attachments']))

                attachments_str = ','.join(attachments_list)
                
                # Публикация по целевым группам
                for target_id in TARGET_GROUP_IDS:
                    try:
                        # Пишем через vk_writer (токен с правами публикации)
                        vk_call(vk_writer.wall.post, label="Бот 1", 
                            owner_id=target_id, 
                            from_group=1, 
                            message=post_text, 
                            attachments=attachments_str
                        )
                        print(f"  -> [Бот 1] Пост успешно опубликован в {target_id}.")
                        
                        # Антиспам пауза
                        sleep_time = random.randint(30, 60)
                        print(f"  -> [Бот 1] Антиспам: пауза {sleep_time} сек...")
                        time.sleep(sleep_time)
                        
                    except Exception as e:
                        print(f"  -> [Бот 1] Ошибка публикации в {target_id}: {e}")

                last_post_id = current_post_id
                save_last_post_id(last_post_id)
                print("[Бот 1] Обработка поста завершена.")

        except Exception as e:
            print(f"[Бот 1] Ошибка получения постов: {e}")
        
        # Динамическая задержка проверки для имитации человека
        final_wait = CHECK_INTERVAL + random.randint(10, 60)
        time.sleep(final_wait)

if __name__ == '__main__':
    run_bot_vk_1()
