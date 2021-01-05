# Vyakarana Telegram Bot

A telegram bot which offers various tools for a Sanskrit learner including stem finder, root finder,
 declension generator, conjugation generator, and sandhi/samasa splitter.


The bot is powered by,

* Telethon  https://docs.telethon.dev/en/latest/

* https://ashtadhyayi.com for conjugations (Dhaatu Paatha)

* Heritage Platform by Gérard Huet for declensions

* Sandhi and Compound Splitter by Oliver Hellwig

## Installation

Please refer to the INSTALL.md file for installation instructions.

## Usage

* `/start` 

    Initiate the bot.

*  `/help`

    Help manual. Displays commands available at glance

* `/setscheme`

    Displays available input translieration schemes (देवनागरी - default, Harvard-Kyoto, Velthuis, ITRANS) to select from.

* `/dhatu verb`

    Search for a root or a conjugated `verb` to find its root or to display its conjugation tables.

    Eg: `/dhatu अगच्छत्`

* `/shabda word`

    Search for a stem or an inflected `word` to find its stem or to display its inflection table.

    Eg: `/shabda रामस्य`

* `/vigraha compound_word_1 compound_word_2 ...`

    Split given word(s) into their constituent words whether they may be in sandhi or samāsa.

    Eg: `/vigraha महर्षिः`
