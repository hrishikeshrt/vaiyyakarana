# Telegram Bot

Uses https://docs.telethon.dev/en/latest/


## Dependencies:
* python-3.8
* indic_transliteration-2.1.0
* telethon-1.18.2
* requests-2.25.1
* beautifulsoup4-4.9.3

## Instructions:

1. Acquire API details from https://core.telegram.org/api/obtaining_api_id and fill them in config.sample.py.
2. A bot needs to be created with BotFather: https://t.me/botfather and fill in `bot_token` of config.sample.py.
3. After filling in the details rename config.sample.py to config.py
4. Run python bot.py

Bot is now online and can be messaged directly.

## Supported Operations 
1. /verbsearch \<verb form\>

    Eg: /verbsearch भवति 
2. /verbforms \<धातुक्रमाङ्कः\>

    Eg: /verbform 08.001
3. /wordsearch \<word form\>

    Eg: /wordsearch दुहः

4. /wordforms \<शब्दक्रमाङ्कः\>

    Eg: /wordform 01.003
