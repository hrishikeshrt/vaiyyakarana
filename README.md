# Vaiyyākaraṇa -- Vyakarana Bot for Telegram

Vaiyyākaraṇa is a telegram bot that offers various tools
for a Sanskrit learner including stem (प्रातिपदिकम्) finder, root (धातुः) finder, declension (सुबन्ताः) generator, conjugation (तिङन्ताः) generator, and compound word (सन्धिसमासौ) splitter.


The bot is powered by,

* Telethon  https://docs.telethon.dev/en/latest/

* https://ashtadhyayi.com for conjugations (धातुपाठः)

* The Heritage Platform by Gérard Huet for declensions

* Sanskrit Sandhi and Compound Splitter by Oliver Hellwig

## Installation

Please refer to the [INSTALL.md](INSTALL.md) file for installation instructions.

## Usage

*  `/help` or `साहाय्य`

    Help manual. Displays commands available at glance

* `/setscheme` or `लेखनविधि`

    Displays available input translieration schemes (देवनागरी - default, Harvard-Kyoto, Velthuis, ITRANS) to select from.

* `/dhatu verb` or `धातु <धातुः धातुरूपम् वा>`

    Search for a root or a conjugated `verb` to find its root or to display its conjugation tables.

    Eg: `/dhatu अगच्छत्`

* `/shabda word` or `शब्द <शब्दः शब्दरूपम् वा>`

    Search for a stem or an inflected `word` to find its stem or to display its inflection table.

    Eg: `/shabda रामस्य`

* `/vigraha sentence or words` or `विग्रह <वाक्यम् शब्दाः वा>`

    Split given word(s) into their constituent words whether they may be in sandhi or samāsa.

    Eg: `/vigraha महर्षिः`


## Contributors

* Hrishikesh Terdalkar
* Mahesh A V S D S
* Shubhangi Agarwal
* Arnab Bhattacharya
