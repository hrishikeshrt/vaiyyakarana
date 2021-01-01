#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 27 19:04:19 2020

@author: Hrishikesh Terdalkar
"""

from telethon import TelegramClient, events, sync

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

lekhavidhiH = {}

def nAgariprati_parivartati(vAkyam,pUrvavidhiH):
    if pUrvavidhiH == 'HK':
        return sanscript.transliterate(vAkyam,sanscript.HK,sanscript.DEVANAGARI)
    elif pUrvavidhiH == 'VELTHUIS':
        return sanscript.transliterate(vAkyam,sanscript.VELTHUIS,sanscript.DEVANAGARI)
    elif pUrvavidhiH == 'ITRANS':
        return sanscript.transliterate(vAkyam,sanscript.ITRANS,sanscript.DEVANAGARI)
    else:
        return vAkyam
    

def nAgaritaH_parivartati(vAkyam,pazcAdvidhiH):
    if pazcAdvidhiH == 'HK':
        return sanscript.transliterate(vAkyam,sanscript.DEVANAGARI,sanscript.HK)
    elif pazcAdvidhiH == 'VELTHUIS':
        return sanscript.transliterate(vAkyam,sanscript.DEVANAGARI,sanscript.VELTHUIS)
    elif pazcAdvidhiH == 'ITRANS':
        return sanscript.transliterate(vAkyam,sanscript.DEVANAGARI,sanscript.ITRANS)
    else:
        return vAkyam

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
    args = event.text.split()
    global lekhavidhiH
    sender_id = event.sender.id
    if sender_id not in lekhavidhiH:
        lekhavidhiH[sender_id] = {'pUrva':'DEVANAGARI','para':'DEVANAGARI'}
    if len(args) > 1:
        lekhavidhiH[sender_id]['pUrva'] = args[1]
    if len(args) > 2:
        lekhavidhiH[sender_id]['para'] = args[2]

    await event.respond(config.start_message, parse_mode='html')
    raise events.StopPropagation


@bot.on(events.NewMessage(pattern='^/verbsearch'))
async def search_verb(event):
    global lekhavidhiH
    search_key = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id
    search_key = nAgariprati_parivartati(search_key,lekhavidhiH[sender_id]['pUrva'])
    print(f"VERBSEARCH: {search_key}")
    matches = [
        format_verb_match(match)
        for match in Dhatu.search(search_key)
    ]
    if not matches:
        await event.reply('तम् धातुम् धातुरूपम् वा न जानामि।')
    else:
        await event.reply('\n---\n'.join(matches))


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
    global pUrvalekhavidhiH
    search_key = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id
    search_key = nAgariprati_parivartati(search_key,lekhavidhiH[sender_id]['pUrva'])
    print(f"WORDSEARCH: {search_key}")
    matches = [
        format_word_match(match)
        for match in Shabda.search(search_key)
    ]
    if not matches:
        await event.reply('तत् शब्दम् शब्दरूपम् वा न जानामि।')
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

###############################################################################


def main():
    bot.start(bot_token=config.bot_token)
    bot.run_until_disconnected()

###############################################################################


if __name__ == '__main__':
    main()
    pass
