# Installation Instructions

The bot is written in the [Python](https://www.python.org/) programming language using [Telethon](https://pypi.org/project/Telethon/). The bot also makes use of [other Sanskrit tools](#sanskrit-tools) to offer specific functionalities.

## Requirements

### Python Packages

These packages are available on The Python Package Index (PyPI),
and can be installed using `pip install`

* python>=3.8
* telethon>=1.18.2
* indic_transliteration>=2.1.0
* requests>=2.25.1
* beautifulsoup4>=4.9.3
* tabulate>=0.8.7

### Sanskrit Tools

The bot depends on following platforms for different functionality, and these need to be installed from the respective repositories. The detailed installation instructions
can be found on the respective repositories.

* The Heritage Platform

https://gitlab.inria.fr/huet/Heritage_Platform

* Sanskrit Sandhi and Compound Splitter

https://github.com/OliverHellwig/sanskrit/tree/master/papers/2018emnlp

The bot can still be started without having these installations, in which case,
Sanskrit Sandhi and Compound splitting utility will be disabled, and Declensions will be
fetched via HTTP from https://sanskrit.inria.fr/DICO/reader.en.html which will add a delay of 5-10 seconds.

If the bot is to be used without these installations, parameters referring to the installation directories should be left empty in `config.py`

## Setup Instructions

1. Acquire API details from https://core.telegram.org/api/obtaining_api_id and fill them in `config.sample.py`.
2. A bot needs to be created with BotFather: https://t.me/botfather and fill in `bot_token` of `config.sample.py`.
3. After filling in the details rename config.sample.py to config.py
4. Run `python bot.py`

Bot is now online and can be messaged directly.
