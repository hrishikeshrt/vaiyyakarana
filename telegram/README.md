# Telegram Bot

Uses https://docs.telethon.dev/en/latest/


## Dependencies:
* python 3.8
* indic_transliteration-2.1.0
* telethon-1.18.2
* config-0.5.0

## Instructions:
1. Acquire API details from https://core.telegram.org/api/obtaining_api_id and fill them in config.sample.py.
2. A bot needs to be created with BotFather: https://t.me/botfather and fill in `bot_token` of config.sample.py.
3. After filling in the details rename config.sample.py to config.py
4. Run python bot.py
5. Type '/start [input transliteration scheme] [output transliteration scheme]' in the bot created to start.
    Supported transliteration schemes are DEVANAGARI, HK, VELTHUIS and ITRANS

## Supported Operations
1. /verbsearch \<verb form\>

    Eg: /verbsearch भवति 
2. /verbform \<धातुक्रमाङ्कः\>

    Eg: /verbform 08.001
3. /wordsearch \<word form\>

    Eg: /wordsearch दुहः

4. /wordform \<शब्दक्रमाङ्कः\>

    Eg: /wordform 01.003
