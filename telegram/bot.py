#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 27 19:04:19 2020

@author: Hrishikesh Terdalkar
"""

from telethon import TelegramClient, events, sync, Button

import dhatupatha
import shabdapatha
from config import TelegramConfig as config
from indic_transliteration import sanscript

###############################################################################

Dhatu = dhatupatha.DhatuPatha('dhatu.json')
Shabda = shabdapatha.ShabdaPatha('shabda.json')

###############################################################################

bot = TelegramClient('Bot Session', config.api_id, config.api_hash)

###############################################################################

transliteration_config = {
    'schemes': {
        sanscript.DEVANAGARI: 'Devanagari',
        sanscript.HK: 'Harvard-Kyoto',
        sanscript.VELTHUIS: 'Velthuis',
        sanscript.ITRANS: 'ITRANS'
    },
    'default': sanscript.DEVANAGARI,
    'internal': sanscript.DEVANAGARI
}

###############################################################################

transliteration_scheme = {}

###############################################################################


def format_word_match(shabda):
    output = []
    for k, v in shabda['shabda'].items():
        output_key = shabdapatha.SHABDA_LANG.get(k, k)
        output_val = v
        if k in shabdapatha.VALUES_LANG:
            output_val = shabdapatha.VALUES_LANG[k][v]
        output.append(f'**{output_key}**: {output_val}')
    if shabda['desc']:
        output.append(shabda['desc'])
    return '\n'.join(output)


def format_verb_match(dhaatu):
    output = []
    for k, v in dhaatu['dhatu'].items():
        output_key = dhatupatha.DHATU_LANG.get(k, k)
        output_val = v
        if k in dhatupatha.VALUES_LANG:
            output_val = dhatupatha.VALUES_LANG[k][v]
        output.append(f'**{output_key}**: {output_val}')
    if dhaatu['desc']:
        output.append(dhaatu['desc'])
    return '\n'.join(output)


def format_word_forms(shabda, rupaani):
    output = [
        (f"**{shabda['word']}** ({shabda['end']}) "
         f"({shabdapatha.VALUES_LANG['linga'][shabda['linga']]})"),
        '+' + '-' * 60 + '+',
    ]
    for idx, forms in enumerate(rupaani):
        output.append(f"**{shabdapatha.VIBHAKTI[idx]}**: {forms}")
    return '\n'.join(output)


def format_verb_forms(dhatu, rupaani):
    output = [
        (f"{dhatu['dhatu']} ({dhatu['swara']}), "
         f"{dhatu['artha']}, {dhatu['artha_english']}"),
        '+' + '-' * 60 + '+',
        (f"{dhatupatha.VALUES_LANG['gana'][dhatu['gana']]}, "
         f"{dhatupatha.VALUES_LANG['pada'][dhatu['pada']]}, "
         '+' + '-' * 60 + '+'
         f"{dhatu['tags']}"),
    ]
    for lakara, forms in rupaani.items():
        if forms:
            output.append('')
            output.append(dhatupatha.LAKARA_LANG[lakara])
            output.append('+' + '-' * 30 + '+')
            output.extend([str(row) for row in forms])
    # output.append('+' + '-' * 60 + '+',)
    return '\n'.join(output)

###############################################################################


@bot.on(events.NewMessage(pattern='^/start'))
async def start(event):
    """Send a message when the command /start is issued."""
    
    start_message = [
        '<h1>स्वागतम्।</h1>',
       'अहम् धातुपाठः शब्दपाठः च जानामि।', 
    ]

    await event.respond('\n'.join(start_message), parse_mode='html')

    # call help handler
    await help(event)

    # call to scheme setting
    await set_scheme(event)

    raise events.StopPropagation


@bot.on(events.NewMessage(pattern='^/help'))
async def help(event):
    """Send a message when the command /help is issued."""

    help_message = [
        '/help - ',
        '/setscheme - '
        '/dhatu - ',
        '/verb - ',
        '/shabd - ',
        '/word - ',
        '/sandhi_samaas - ',
        '/split - '
    ]

    await event.respond('\n'.join(help_message))


@bot.on(events.NewMessage(pattern='^/setscheme'))
async def set_scheme(event):
    '''Set transliteration scheme for user'''
    global transliteration_config
    global transliteration_scheme

    keyboard = []
    current_row = []
    row_length = 2

    # Populating keyboard
    for scheme, scheme_name in transliteration_config['schemes'].items():
        current_row.append(
            Button.inline(scheme_name, data=f'scheme_{scheme}')
        )
        if len(current_row) == row_length:
            keyboard.append(current_row)
            current_row = []

    response_message = [
        'कृपया  एकां लेखनविधिं वृणोतु –'
    ]
    
    # Asking user to choose a keyboard scheme
    await event.respond('\n'.join(response_message), buttons=keyboard, parse_mode='html')
    print("Scheme asked")


###############################################################################


@bot.on(events.CallbackQuery(pattern='^scheme_'))
async def scheme_handler(event):
    print("Scheme selected")
    global transliteration_scheme
    global transliteration_config
    sender_id = event.sender.id

    if sender_id not in transliteration_scheme:
        transliteration_scheme[sender_id] = {
            'input': transliteration_config['default'],
            'output': transliteration_config['default']
        }

    data = event.data.decode('utf-8')
    indx, scheme = data.split('_')
        
    transliteration_scheme[sender_id][indx] = scheme

    response_message = [
        'कृपया  एकां लेखनविधिं वृणोतु –'
    ]
    
    # Editing last message, removing keyboard
    await event.edit('\n'.join(response_message), buttons=Button.clear(), parse_mode='html')
    

    response_message = [
        'धन्यवादः।',
        ' '.join(['वृणीता - ', transliteration_config['schemes'][scheme]]),
        'कृपया पृच्छतु।'
    ]

    await event.respond('\n'.join(response_message))


@bot.on(events.CallbackQuery(pattern='^query_'))
async def query_handler(event):
    await redirect(event)

###############################################################################


@bot.on(events.NewMessage(pattern='^[^/]'))
async def search(event):
    text = f'query_{event.text}'
    keyboard = [
        [Button.inline("सुबन्तम्", data=text+' sup'),
         Button.inline("तिङन्तम्", data=text+' tiG')]
    ]
    await event.respond('दत्तपदस्य प्रकारं वृणोतु –', buttons=keyboard)


async def redirect(event):
    print("Redirect")
    data = event.data.decode('utf-8')
    text, form = data.split('_')[1].split()
    if form == 'sup':
        event.text = '/wordsearch ' + text
        await search_word(event)
    elif form == 'tiG': 
        event.text = '/verbsearch ' + text
        await search_verb(event)

###############################################################################


@bot.on(events.NewMessage(pattern='^/verbsearch'))
async def search_verb(event):
    global transliteration_scheme
    global transliteration_config
    search_key = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id
    search_key = sanscript.transliterate(
        search_key,
        transliteration_scheme[sender_id]['input'],
        transliteration_config['default']
    )
    print(f"VERBSEARCH: {search_key}")

    if search_key=="":
        await event.respond('USAGE: /verbsearch धातुम्/ धातुरूपम्')
    else:
        matches = [
            format_verb_match(match)
            for match in Dhatu.search(search_key)
        ]
        if not matches:
            await event.respond('तम् धातुम् धातुरूपम् वा न जानामि।')
        else:
            await event.respond('\n---\n'.join(matches))


@bot.on(events.NewMessage(pattern='^/verbforms'))
async def show_verb_forms(event):
    dhaatu_idx = Dhatu.validate_index(' '.join(event.text.split()[1:]))
    if dhaatu_idx:
        print(f"VERBINDEX: {dhaatu_idx}")
        dhaatu = Dhatu.get(dhaatu_idx)
        rupaani = Dhatu.get_forms(dhaatu_idx)
        await event.reply(format_verb_forms(dhaatu, rupaani))
    else:
        print(f"INVALID_VERBINDEX: {dhaatu_idx}")
        await event.reply("कृपया धातुक्रमाङ्कः लिखतु।")


@bot.on(events.NewMessage(pattern='^/wordsearch'))
async def search_word(event):
    global transliteration_scheme
    global transliteration_config

    search_key = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id
    search_key = sanscript.transliterate(
        search_key,
        transliteration_scheme[sender_id]['input'],
        transliteration_config['default']
    )
    print(f"WORDSEARCH: {search_key}")

    if search_key=="":
        await event.respond('USAGE: /wordsearch शब्दम्/ शब्दरूपम्')
    else:
        matches = [
            format_word_match(match)
            for match in Shabda.search(search_key)
        ]
        if not matches:
            await event.reply("तत् शब्दम् शब्दरूपम् वा न जानामि।")
        else:
            await event.reply('\n---\n'.join(matches))


@bot.on(events.NewMessage(pattern='^/wordforms'))
async def show_word_forms(event):
    shabda_idx = Shabda.validate_index(' '.join(event.text.split()[1:]))
    if shabda_idx:
        print(f"WORDINDEX: {shabda_idx}")
        shabda = Shabda.get(shabda_idx)
        rupaani = Shabda.get_forms(shabda_idx)
        await event.reply(format_word_forms(shabda, rupaani))
    else:
        print(f"INVALID_WORDINDEX: {shabda_idx}")
        await event.reply("कृपया शब्दक्रमाङ्कः लिखतु।")

@bot.on(events.NewMessage(pattern='^/split'))
async def sandhi_samaasa_split(event):
    """Output the sandhi split of the input word."""
    global transliteration_scheme
    search_key = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id
    search_key = sanscript.transliterate(search_key,transliteration_scheme[sender_id]['input'],transliteration_config['internal'])
    print(f"SPLIT: {search_key}")
    if search_key=="":
        await event.respond('USAGE: /split शब्द')
    else:
        pass


###############################################################################


def main():
    bot.start(bot_token=config.bot_token)
    bot.run_until_disconnected()

###############################################################################


if __name__ == '__main__':
    main()
