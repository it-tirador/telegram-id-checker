# Telegram Group & Topic ID Checker

_Read this in [English](README.md) | [Русский](README.ru.md)_

This project is designed to automatically collect the IDs and names of all groups (chats) and all topics in those groups where the bot is a member and there are messages in the topics.

## Features
- Detects `chat_id` and the name of each group/chat where the bot is present.
- For each group, detects all known topics: their `topic_id` and name (if available).
- All information is automatically saved to the `topics.json` file:

```json
{
  "my_bot": {
    "-1001111111111": {
      "chat_title": "Example Group",
      "topics": {
        "101": "General Discussion",
        "102": "Support"
      }
    }
  },
  "another_bot": {
    "-1002222222222": {
      "chat_title": "Project Team",
      "topics": {
        "201": "Development",
        "202": "Announcements"
      }
    }
  }
}
```

- For each bot username (`my_bot`, `another_bot`, etc.), a separate section with groups and topics is created.
- Data for different bots is not overwritten and is preserved between runs.

## How it works
1. The script queries the Telegram API and receives all updates related to the bot.
2. Finds all unique groups/chats where the bot is present.
3. For each group, collects all known topics in which there were messages from the bot or users.
4. Saves all information to `topics.json` under the section corresponding to the current bot's username.

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file and specify:
   ```env
   BOT_TOKEN=your_bot_token
   ```
3. Run the script:
   ```bash
   python main.py
   ```
4. After execution, `topics.json` will contain up-to-date information about all groups and topics for all your bots.

## Important
- The bot must be added to the group and have admin rights.
- Topics will only appear if there were messages from users in them (the bot does not always see its own messages).
- The topic name is saved only if the bot saw the topic creation event.
- Data for different bots is not overwritten — a separate section is created for each bot username.

---

**The project works on Windows, all commands can be run in PowerShell.** 