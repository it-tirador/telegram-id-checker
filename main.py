import requests
import json
import os
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv(override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")


def extract_all_chats_and_topics(updates: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Recursively extracts all groups (chats) and topics from Telegram updates.

    Args:
        updates (List[Dict[str, Any]]): List of updates received from Telegram API (getUpdates).

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary where the key is chat_id (str),
            the value is a dict with the group name (chat_title) and a dictionary of topics,
            where the key is topic_id (str), and the value is the topic name (str).
    """
    chats: Dict[str, Dict[str, Any]] = {}
    def recursive_search(msg: Dict[str, Any], parent_chat_id: Any = None, parent_chat_title: Any = None) -> None:
        if not isinstance(msg, dict):
            return
        chat = msg.get('chat', {})
        chat_id = chat.get('id', parent_chat_id)
        chat_title = chat.get('title', chat.get('username', 'No name')) if chat else parent_chat_title
        if chat_id is not None:
            if str(chat_id) not in chats:
                chats[str(chat_id)] = {"chat_title": chat_title, "topics": {}}
        # Topics
        if 'message_thread_id' in msg:
            topic_id = msg['message_thread_id']
            topic_name = msg.get('forum_topic_created', {}).get('name')
            if str(chat_id) in chats:
                if str(topic_id) not in chats[str(chat_id)]["topics"]:
                    chats[str(chat_id)]["topics"][str(topic_id)] = topic_name or "No name (or not found)"
                elif topic_name and chats[str(chat_id)]["topics"][str(topic_id)] == "No name (or not found)":
                    chats[str(chat_id)]["topics"][str(topic_id)] = topic_name
        # Recursively search all nested dicts/lists
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
    Gets the current bot's username via Telegram API getMe.

    Args:
        token (str): Telegram bot token.
    Returns:
        str: Bot username (without @)
    """
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url)
    result = response.json()
    if result.get("ok") and "result" in result and "username" in result["result"]:
        return result["result"]["username"]
    else:
        raise Exception(f"Failed to get bot username: {result}")


def main() -> None:
    """
    Main function: gets updates from Telegram, extracts all groups and topics,
    saves them to topics.json (by bot username), and prints the result to the console.
    """
    bot_username = get_bot_username(BOT_TOKEN)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url)
    result = response.json()
    if not result.get("ok"):
        print(f"[❌] Telegram API error: {result}")
        return
    updates = result.get("result", [])
    print(f'[DEBUG] All messages with message_thread_id and chat_id for @{bot_username}:')
    for update in updates:
        message = update.get("message") or update.get("channel_post")
        if message and "message_thread_id" in message:
            print(f"chat_id: {message.get('chat', {}).get('id')}, thread_id: {message['message_thread_id']}, text: {message.get('text')}, topic_name: {message.get('forum_topic_created', {}).get('name')}")
    all_chats = extract_all_chats_and_topics(updates)
    # Load existing topics.json (if any)
    try:
        with open("topics.json", "r", encoding="utf-8") as f:
            all_bots_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_bots_data = {}
    # Update only for the current username
    all_bots_data[bot_username] = all_chats
    with open("topics.json", "w", encoding="utf-8") as f:
        json.dump(all_bots_data, f, ensure_ascii=False, indent=2)
    print(f"[✅] All groups and topics saved for @{bot_username}:")
    for chat_id, chat_info in all_chats.items():
        print(f"Group: {chat_id} | {chat_info['chat_title']}")
        for tid, tname in chat_info["topics"].items():
            print(f"    topic_id: {tid} | topic_name: {tname}")

if __name__ == "__main__":
    main()
