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

# Настройки источника и интервала
SOURCE_GROUP_ID = -204081884  
CHECK_INTERVAL = 300  
STATE_KEY = 'vk_bot_2'

# 1. ТОКЕН ДЛЯ ЧТЕНИЯ (Оставляем для парсинга стены-донора)
READ_TOKEN = 'vk1.a.UQQypBdwlUwwk6O3z7iJAXc8Tnzx6VcB3seRHXgioyrLDLW-xYTXy7SCqONeAc7FOuadlIg1u52uEVFGrKvjCZmV-wq70J2TG_MqZKtn7aXkudTIrURT-OG2bzB1neTWwkHAM-buqJIWLYT8ioGLy6EiL84LamSMjstFgw1ynkXR_sCGZsspN2zbF5P9chaLu98ONjvbDVGk67_j1-CURw'

# 2. ИНДИВИДУАЛЬНЫЕ ТОКЕНЫ ЦЕЛЕВЫХ ГРУПП
# Если бот опубликует пост К1 в группу К2, просто поменяйте местами токены в этом списке.
TARGET_GROUPS = {
    -215578086: 'vk1.a.7xAW5jS-qXvnUq4u5gDU1zrOe-b0wLGTl1giQVIYrvoNZoXohR68-LxCPopBqGGrwWj43_NeL93SVRFcKk-Bqj4jOe9PgH70RcTjI3qnsSDDSmIA-iGHfF4n9gg3WjEnQC_KP5WpNkzNIEqcBEWaoeNgxSHlafVFkW5qn5RLawP2FIe-OjfJ9OdYTQRJNoNI21PY28wepzQBIdL6rK44kg', # К2
    -221202163: 'vk1.a.4cHbV3lJL2vc0-puNsdgjIVgYbYjd6pvNC4CIdFZZ04PswKN_BX3tkYKFcdqWdB4q5dHEXr5E6JSg0DF0ATpInCeCBxBEb51dMv18_MntKu1-ta6DX9l8h_GuT0C_0d4nnH-lt4KUuzlepGgdR4_izM4Tt6rb52hBBqOLVa2aDNWjfcybKkVsoD5kytzG0jiTtOjv1N9uGgyB6ksKO_zvQ', # К3
    -219647526: 'vk1.a.GSp81p6NjbYmiJb5v9bMsmi1E7jh6VKEUhZSNBIqUqAsAuU1Uo78FAH1s9twKaHfrRjMXT1653jcuBa5CFkH_kpFPzoXoy0HrsCnjejelaX_4jvN2lMPGUUAMcV8MXJt9OA0kugbB3_aXTJcsVpkTNzrjm-vhQiG32eHsDnsvPgIwPm5x8M5gP1hG2zCtLh_jsZHbOdVt-6SHsRZ4yTs2Q', # К1
    -219649455: 'vk1.a.-ffRiemlhl6GrjFiwXqglyWFA1pUUXyzIsOh-lRwm8qgSqItJCAARYnY1w9Uia7dlRPA2wX2XRZVjhJcb5gYD-CEQQqpMUmqrcWFSY8vy8v2IbObnFLFYm7DzCaovEOkzNR5IB1mtjyaMVkegmZBOXcNcFuemBZuq4eflzwVnd76VTuY16dzeRynmdgVjJ1LrJLAMEwDc6M8AE8eny4oOQ', # Ш
    -215622579: 'vk1.a.lZHgD2apAbqlrr9nV1HYgTWoInkIsCEHle6d_OXDLoGUTAmsGm0j9SpLecjLKd50sU1z0TJf5Ofi5VjAIliV3U24IVtGNe0GTMcjk7bgWXP5EzvKoYqudjDzyhAJZUHjdoPkWIIUqB8f0gWD2XNa7LFYyKnSpIQZoVay3b0g8_auuMLl0cDlJHl1cU3FS7CdipMqzn3OaZ3OSKwdV2rQvQ'  # РОО
}

# Если сохранённого ID нет (0), бот при старте запомнит текущий пост донора и ничего не опубликует.
def get_saved_last_post_id():
    return load_last_id(STATE_KEY)

def save_last_post_id(post_id):
    save_last_id(STATE_KEY, post_id)

def run_bot_vk_2():
    print("Авторизация ВКонтакте (Бот 2)...")
    
    # 1. Создаем сессию для чтения
    try:
        vk_read_session = vk_api.VkApi(token=READ_TOKEN)
        vk_reader = vk_read_session.get_api()
        print("[Успех] Сессия для чтения исходной группы создана.")
    except Exception as e:
        print(f"[Фатальная Ошибка] Не удалось создать сессию чтения. Детали: {e}")
        return

    # 2. Создаем сессии для публикации (отдельно для каждой группы)
    vk_writers = {}
    for group_id, token in TARGET_GROUPS.items():
        try:
            session = vk_api.VkApi(token=token)
            vk_writers[group_id] = session.get_api()
            print(f"[Успех] Сессия публикации для группы {group_id} авторизована.")
        except Exception as e:
            print(f"[Ошибка] Ошибка авторизации для группы {group_id}: {e}")

    if not vk_writers:
        print("[Фатальная Ошибка] Ни одна целевая группа не авторизована. Остановка.")
        return

    last_post_id = get_saved_last_post_id()
    print(f"Бот ВК 2 запущен. В памяти ID прошлого поста: {last_post_id}")
    print(f"Готов к публикации в {len(vk_writers)} групп(ы).")

    while True:
        try:
            response = vk_call(vk_reader.wall.get, label="Бот 2", owner_id=SOURCE_GROUP_ID, count=2)
            posts = response['items']
            if not posts:
                print(f"[Бот 2] Стена донора пуста. Ждем {CHECK_INTERVAL} сек.")
                time.sleep(CHECK_INTERVAL)
                continue

            current_post = next((p for p in posts if not p.get('is_pinned')), posts[0])
            current_post_id = current_post['id']

            print(f"[Бот 2 ПРОВЕРКА] ID на стене: {current_post_id} | ID в памяти: {last_post_id}")

            if last_post_id == 0:
                last_post_id = current_post_id
                save_last_post_id(last_post_id)
                print(f"[Бот 2] Это ПЕРВЫЙ запуск. Запомнили пост {last_post_id}. Публиковать НЕ БУДЕМ. Ждем новый пост.")
            
            elif current_post_id <= last_post_id:
                print(f"[Бот 2] Новых постов нет (на стене {current_post_id} <= {last_post_id}). Ухожу в сон.")
                
            elif current_post_id > last_post_id:
                print(f"\n[Бот 2] НАЙДЕН НОВЫЙ ПОСТ: {current_post_id}! Начинаю обработку медиа...")
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
                            
                            if owner_id is not None and media_id is not None:
                                att_str = f"{att_type}{owner_id}_{media_id}"
                                if item.get('access_key'): 
                                    att_str += f"_{item.get('access_key')}"
                                extracted.append(att_str)
                    return extracted

                if 'attachments' in current_post:
                    attachments_list.extend(extract_attachments(current_post['attachments']))
                
                if 'copy_history' in current_post and len(current_post['copy_history']) > 0:
                    repost = current_post['copy_history'][0]
                    if not post_text and repost.get('text'):
                        post_text = repost['text']
                    if 'attachments' in repost:
                        attachments_list.extend(extract_attachments(repost['attachments']))

                attachments_str = ','.join(attachments_list)
                print(f"[Бот 2] Собрано вложений: {len(attachments_list)}")
                # ---------------------------------------------
                
                # Отправляем пост в каждую группу, используя её личный токен
                for target_id, vk_writer in vk_writers.items():
                    try:
                        vk_call(vk_writer.wall.post, label="Бот 2", 
                            owner_id=target_id, 
                            from_group=1, 
                            message=post_text, 
                            attachments=attachments_str
                        )
                        print(f"  -> Успешно отправлено в {target_id}")
                        
                        # Антиспам можно сделать меньше (10-20 сек), так как токены разные, 
                        # но оставим небольшую паузу для защиты общего IP-адреса сервера.
                        sleep_time = random.randint(10, 20)
                        print(f"  -> Антиспам: ждем {sleep_time} сек...")
                        time.sleep(sleep_time)
                        
                    except Exception as e:
                        print(f"  -> Ошибка отправки в {target_id}: {e}")

                last_post_id = current_post_id
                save_last_post_id(last_post_id)
                print("[Бот 2] Рассылка завершена. Возвращаюсь в режим ожидания.")

        except Exception as e:
            print(f"[Бот 2] Общая ошибка проверки постов: {e}")
        
        final_wait = CHECK_INTERVAL + random.randint(10, 90)
        time.sleep(final_wait)

if __name__ == '__main__':
    run_bot_vk_2()
