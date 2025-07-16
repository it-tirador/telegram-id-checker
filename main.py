import requests
import json
import os
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv(override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")


def extract_all_chats_and_topics(updates: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Рекурсивно извлекает все группы (чаты) и темы (topics) из апдейтов Telegram.

    Args:
        updates (List[Dict[str, Any]]): Список апдейтов, полученных от Telegram API (getUpdates).

    Returns:
        Dict[str, Dict[str, Any]]: Словарь, где ключ — chat_id (str),
            значение — dict с названием группы (chat_title) и словарём тем (topics),
            где ключ — topic_id (str), значение — название темы (str).
    """
    chats: Dict[str, Dict[str, Any]] = {}
    def recursive_search(msg: Dict[str, Any], parent_chat_id: Any = None, parent_chat_title: Any = None) -> None:
        if not isinstance(msg, dict):
            return
        chat = msg.get('chat', {})
        chat_id = chat.get('id', parent_chat_id)
        chat_title = chat.get('title', chat.get('username', 'Без названия')) if chat else parent_chat_title
        if chat_id is not None:
            if str(chat_id) not in chats:
                chats[str(chat_id)] = {"chat_title": chat_title, "topics": {}}
        # Темы
        if 'message_thread_id' in msg:
            topic_id = msg['message_thread_id']
            topic_name = msg.get('forum_topic_created', {}).get('name')
            if str(chat_id) in chats:
                if str(topic_id) not in chats[str(chat_id)]["topics"]:
                    chats[str(chat_id)]["topics"][str(topic_id)] = topic_name or "Без названия (или не найдено)"
                elif topic_name and chats[str(chat_id)]["topics"][str(topic_id)] == "Без названия (или не найдено)":
                    chats[str(chat_id)]["topics"][str(topic_id)] = topic_name
        # Рекурсивно ищем во всех вложенных dict/list
        for value in msg.values():
            if isinstance(value, dict):
                recursive_search(value, chat_id, chat_title)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        recursive_search(item, chat_id, chat_title)
    for update in updates:
        message = update.get("message") or update.get("channel_post")
        if message:
            recursive_search(message)
    return chats


def get_bot_username(token: str) -> str:
    """
    Получает username текущего бота через Telegram API getMe.

    Args:
        token (str): Токен Telegram-бота.
    Returns:
        str: username бота (без @)
    """
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url)
    result = response.json()
    if result.get("ok") and "result" in result and "username" in result["result"]:
        return result["result"]["username"]
    else:
        raise Exception(f"Не удалось получить username бота: {result}")


def main() -> None:
    """
    Основная функция: получает апдейты от Telegram, извлекает все группы и темы,
    сохраняет их в topics.json (по username бота) и выводит результат в консоль.
    """
    bot_username = get_bot_username(BOT_TOKEN)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url)
    result = response.json()
    if not result.get("ok"):
        print(f"[❌] Ошибка Telegram API: {result}")
        return
    updates = result.get("result", [])
    print(f'[DEBUG] Все сообщения с message_thread_id и chat_id для @{bot_username}:')
    for update in updates:
        message = update.get("message") or update.get("channel_post")
        if message and "message_thread_id" in message:
            print(f"chat_id: {message.get('chat', {}).get('id')}, thread_id: {message['message_thread_id']}, text: {message.get('text')}, topic_name: {message.get('forum_topic_created', {}).get('name')}")
    all_chats = extract_all_chats_and_topics(updates)
    # Загружаем существующий topics.json (если есть)
    try:
        with open("topics.json", "r", encoding="utf-8") as f:
            all_bots_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_bots_data = {}
    # Обновляем только для текущего username
    all_bots_data[bot_username] = all_chats
    with open("topics.json", "w", encoding="utf-8") as f:
        json.dump(all_bots_data, f, ensure_ascii=False, indent=2)
    print(f"[✅] Сохранены все группы и темы для @{bot_username}:")
    for chat_id, chat_info in all_chats.items():
        print(f"Группа: {chat_id} | {chat_info['chat_title']}")
        for tid, tname in chat_info["topics"].items():
            print(f"    topic_id: {tid} | topic_name: {tname}")

if __name__ == "__main__":
    main()
