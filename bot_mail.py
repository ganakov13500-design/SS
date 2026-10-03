import imaplib
import email
from email.header import decode_header
import email.utils
import time
import requests
import asyncio
import os

EMAIL_LOGIN = 'sharoy-roo@mail.ru'
EMAIL_PASSWORD = 'musalovamb99'
IMAP_SERVER = 'imap.mail.ru'
ID_INSTANCE = '7107631855'
API_TOKEN = '6b85d9d9086b4c18919ab1d919c3795d896e40cfb1244c42a8'
WHATSAPP_CHAT_ID = '120363423933263919@g.us'
CHECK_INTERVAL = 60  

def decode_mime_words(s):
    if not s: return "(Без заголовка)"
    decoded_words = []
    for word, encoding in decode_header(s):
        if isinstance(word, bytes):
            charset = encoding if encoding else 'utf-8'
            try: decoded_words.append(word.decode(charset))
            except: decoded_words.append(word.decode('windows-1251', errors='ignore'))
        else:
            decoded_words.append(word)
    return u''.join(decoded_words)

# --- НОВАЯ ФУНКЦИЯ ДЛЯ ПРАВИЛЬНЫХ ИМЕН ФАЙЛОВ ---
def decode_filename(filename):
    if not filename:
        return "document.file"
    
    # Исправляем сложные кодировки RFC2231
    filename = email.utils.collapse_rfc2231_value(filename)
    
    decoded_parts = decode_header(filename)
    result = []
    for word, encoding in decoded_parts:
        if isinstance(word, bytes):
            charset = encoding if encoding else 'utf-8'
            try:
                result.append(word.decode(charset))
            except:
                try: result.append(word.decode('windows-1251'))
                except: result.append(word.decode('utf-8', errors='ignore'))
        else:
            # Исправляем "кракозябры", если Python ошибся с кодировкой (fallback to latin-1)
            if isinstance(word, str):
                try:
                    raw_bytes = word.encode('latin-1')
                    try: word = raw_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        try: word = raw_bytes.decode('windows-1251')
                        except: pass
                except UnicodeEncodeError:
                    pass
            result.append(word)
            
    clean_name = ''.join(result)
    
    # Очищаем имя от запрещенных системных символов (защита от ошибок сохранения)
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\r']:
        clean_name = clean_name.replace(char, '_')
        
    return clean_name
# ------------------------------------------------

def send_whatsapp_message(text):
    url = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
    try: requests.post(url, json={"chatId": WHATSAPP_CHAT_ID, "message": text})
    except Exception as e: print(f"[Бот Mail] Ошибка WhatsApp (Текст): {e}")

def send_whatsapp_file(filepath, filename):
    url = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendFileByUpload/{API_TOKEN}"
    payload = {'chatId': WHATSAPP_CHAT_ID}
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f)}
            response = requests.post(url, data=payload, files=files)
            if response.status_code == 200:
                print(f"[Бот Mail] Вложение '{filename}' успешно отправлено.")
            else:
                print(f"[Бот Mail] Ошибка отправки файла '{filename}': {response.text}")
    except Exception as e: 
        print(f"[Бот Mail] Ошибка WhatsApp (Файл): {e}")

async def check_mail_loop():
    print("Запуск бота Mail.ru (с умной дешифровкой файлов)...")
    while True:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL_LOGIN, EMAIL_PASSWORD)
            mail.select("INBOX")
            status, messages = mail.search(None, "UNSEEN")
            
            if status == "OK" and messages[0]:
                email_ids = messages[0].split()
                for e_id in email_ids:
                    res, msg_data = mail.fetch(e_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = decode_mime_words(msg.get("Subject"))
                            sender = decode_mime_words(msg.get("From"))
                            
                            body = ""
                            attachments = [] 
                            
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain" and part.get_filename() is None:
                                        try: 
                                            if not body:
                                                body = part.get_payload(decode=True).decode(errors='ignore')
                                        except: pass
                                    
                                    # --- ПРИМЕНЯЕМ НОВУЮ ФУНКЦИЮ ЗДЕСЬ ---
                                    raw_filename = part.get_filename()
                                    if raw_filename:
                                        filename = decode_filename(raw_filename)
                                        filepath = os.path.join(os.getcwd(), filename)
                                        try:
                                            file_data = part.get_payload(decode=True)
                                            if file_data:
                                                with open(filepath, 'wb') as f:
                                                    f.write(file_data)
                                                attachments.append({'path': filepath, 'name': filename})
                                        except Exception as e:
                                            print(f"[Бот Mail] Ошибка сохранения '{filename}': {e}")
                            else:
                                try: body = msg.get_payload(decode=True).decode(errors='ignore')
                                except: pass
                            
                            if len(body) > 500: body = body[:500] + "\n[...]"
                            text = f"📧 *НОВОЕ ПИСЬМО (Mail.ru)*\n👤 *От:* {sender}\n📌 *Тема:* {subject}\n📝 *Текст:*\n{body.strip()}"
                            
                            if attachments:
                                text += f"\n\n📎 *Вложений в письме:* {len(attachments)} (файлы отправляются...)"
                            
                            send_whatsapp_message(text)
                            await asyncio.sleep(2) 
                            
                            for att in attachments:
                                send_whatsapp_file(att['path'], att['name'])
                                await asyncio.sleep(2)
                                try: os.remove(att['path'])
                                except: pass
                                
            mail.logout()
        except Exception as e: 
            print(f"[Бот Mail] Ошибка: {e}")
        
        await asyncio.sleep(CHECK_INTERVAL)

def run_bot_mail():
    asyncio.run(check_mail_loop())
