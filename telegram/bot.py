#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 27 19:04:19 2020

@author: Hrishikesh Terdalkar
"""

from telethon import TelegramClient, events, sync, Button
from indic_transliteration import sanscript

import dhatupatha
import shabdapatha
import heritage

import config

###############################################################################

Dhatu = dhatupatha.DhatuPatha(
    'dhatu.json',
    display_keys=[
        'baseindex', 'dhatu', 'swara', 'gana', 'pada', 'artha', 'karma',
        'artha_english'
    ]
)

Shabda = shabdapatha.ShabdaPatha('shabda.json')

if not config.hellwig_splitter_dir:
    class NonSplitter:
        def split(self, sentence):
            return "अहम् विग्रहः कर्तुम् न शक्नोमि।"
    Vigraha = NonSplitter()
else:
    import splitter
    Vigraha = splitter.Splitter(config.hellwig_splitter_dir)

if not config.heritage_platform_dir:
    Heritage = heritage.HeritagePlatform(config.heritage_platform_dir)
else:
    Heritage = heritage.HeritagePlatform('', method='web')

###############################################################################

bot = TelegramClient(
    'Bot Session',
    config.TelegramConfig.api_id,
    config.TelegramConfig.api_hash
)

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
        if output_key == 'क्रमाङ्कः':
            kramanka = output_val

    if shabda['desc']:
        output.append(shabda['desc'])
    return '\n'.join(output), kramanka


def format_verb_match(dhaatu):
    output = []
    kramanka = ''
    for k, v in dhaatu['dhatu'].items():
        output_key = dhatupatha.DHATU_LANG.get(k, k)
        output_val = v
        if k in dhatupatha.VALUES_LANG:
            output_val = dhatupatha.VALUES_LANG[k][v]
        output.append(f'**{output_key}**: {output_val}')
        if output_key == 'क्रमाङ्कः':
            kramanka = output_val
    if dhaatu['desc']:
        output.append(dhaatu['desc'])
    return '\n'.join(output), kramanka


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
        'The following commands are supported.',
        '/help - Print this help.',
        '/setinputscheme - Choose input scheme (Default - Devanagari).',
        '/setoutputscheme - Choose output scheme (Default - Devanagari).',
        '/dhatu - Describe a verb form (Tingantam).',
        '/dhaturupa - Display dhaturup (lakaar).',
        '/shabda - Describe a word form (Subantam).',
        '/shabdarupa - Display shabdarup.',
        '/split - Display the sandhi samaas split.'
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
        'कृपया एकां लेखनविधिं वृणोतु –'
    ]

    # Asking user to choose a keyboard scheme
    await event.respond(
        '\n'.join(response_message), buttons=keyboard, parse_mode='html'
    )
    print("Scheme asked")
    while event.data.decode('utf-8') == "":
        pass

###############################################################################


@bot.on(events.CallbackQuery(pattern='^scheme_'))
async def scheme_handler(event):
    global transliteration_scheme
    global transliteration_config
    sender_id = event.sender.id

    if sender_id not in transliteration_scheme:
        transliteration_scheme[sender_id] = {
            'input': transliteration_config['default'],
            'output': transliteration_config['default']
        }

    data = event.data.decode('utf-8')
    _, scheme = data.split('_')

    transliteration_scheme[sender_id]['input'] = scheme

    # Editing last message, removing keyboard
    last_message = await event.get_message()
    await event.edit(
        last_message.raw_text, buttons=Button.clear(), parse_mode='html'
    )

    response_message = [
        'धन्यवादः।',
        ' '.join(['वृणीता - ', transliteration_config['schemes'][scheme]]),
        'कृपया पृच्छतु।'
    ]

    await event.respond('\n'.join(response_message))


@bot.on(events.CallbackQuery(pattern='^query_'))
async def query_handler(event):
    await redirect(event)


@bot.on(events.CallbackQuery(pattern='^[wordsearch_]|[verbsearch_]'))
async def query__handler(event):
    await redirect2(event)


###############################################################################


@bot.on(events.NewMessage(pattern='^[^/]'))
async def search(event):
    event_text = event.text

    print(f"Search: {event_text}")
    keys = event_text.split()

    if len(keys) == 2:
        # Check if first word is dhaatu or shabda in Latin or Devanagari
        dhatu_command = [
            sanscript.transliterate(
                'धातु',
                transliteration_config['default'],
                output_scheme
            )
            for output_scheme in transliteration_config['schemes']
        ]
        dhatu_command = dhatu_command + ['dhatu']

        shabda_command = [
            sanscript.transliterate(
                'शब्द',
                transliteration_config['default'],
                output_scheme
            )
            for output_scheme in transliteration_config['schemes']
        ]
        shabda_command = shabda_command + ['shabd']

        dhaturup_command = [
            sanscript.transliterate(
                'धातुरूप',
                transliteration_config['default'],
                output_scheme
            )
            for output_scheme in transliteration_config['schemes']
        ]
        dhaturup_command = dhatu_command + ['dhaturup']

        shabdarup_command = [
            sanscript.transliterate(
                'शब्दरूप',
                transliteration_config['default'],
                output_scheme
            )
            for output_scheme in transliteration_config['schemes']
        ]
        shabdarup_command = shabdarup_command + ['shabdarup']

        if keys[0] in dhatu_command:
            await search_verb(event)
        elif keys[0] in shabda_command:
            await search_word(event)
        elif keys[0] in dhaturup_command:
            await show_verb_forms(event)
        elif keys[0] in shabdarup_command:
            await show_word_forms(event)
        else:
            event.respond("Sorry, I don't understand this.")
            await help(event)
    elif len(keys) == 1:
        text = f'query_{event_text}'
        keyboard = [
            [Button.inline("सुबन्तम्", data=text+' sup'),
             Button.inline("तिङन्तम्", data=text+' tiG')]
        ]
        await event.respond('दत्तपदस्य प्रकारं वृणोतु –', buttons=keyboard)
    elif len(keys) > 2:
        event.respond("Sorry, I don't understand this.")
        await help(event)


async def redirect2(event):
    print('Redirect2')
    data = event.data.decode('utf-8')
    form, text = data.split('_')
    if form == 'wordsearch':
        event.text = '/wordforms ' + text
        await show_word_forms(event)
    elif form == 'verbsearch':
        event.text = '/verbforms ' + text
        await show_verb_forms(event)


async def redirect(event):
    print("Redirect")
    data = event.data.decode('utf-8')
    text, form = data.split('_')[1].split()
    if form == 'sup':
        event.text = '/shabda ' + text
        await search_word(event)
    elif form == 'tiG':
        event.text = '/dhatu ' + text
        await search_verb(event)

###############################################################################


@bot.on(events.NewMessage(pattern='^/dhatu'))
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

    if search_key == "":
        await event.respond('USAGE: /dhatu धातुम्/ धातुरूपम्')
    else:
        matches = [
            format_verb_match(match)
            for match in Dhatu.search(search_key)
        ]
        if not matches:
            await event.respond('तम् धातुम् धातुरूपम् वा न जानामि।')
        else:
            for match in matches:
                keyboard = [[Button.inline('रूपं दर्शयतु',
                                           data=f'verbsearch_{match[1]}')]]
            await event.respond(match[0], buttons=keyboard)


@bot.on(events.NewMessage(pattern='^/dhaturupa'))
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


@bot.on(events.NewMessage(pattern='^/shabda_new'))
async def search_word_new(event):
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

    if search_key == "":
        await event.respond('USAGE: /shabda शब्दम्/ शब्दरूपम्')
    else:
        matches = []
        grouped_matches = []
        for solution in Heritage.get_analysis(search_key):
            has_gender = False
            grouped = {}
            grouped['genders'] = {}
            for analysis in solution['words'][0]['analyses']:
                grouped['root'] = solution['words'][0]['root']
                match = {}
                match['root'] = solution['words'][0]['root']
                for x in analysis:
                    for a_key, a_values in heritage.HERITAGE_LANG.items():
                        if x in a_values:
                            match[a_key] = a_values[x]
                            if a_key == 'gender':
                                has_gender = True

                if has_gender:
                    if match['gender'] not in grouped['genders']:
                        grouped['genders'][match['gender']] = []

                    grouped['genders'][match['gender']].append({
                        'case': match['case'],
                        'number': match['number']
                    })
                    matches.append(match)

            if grouped['genders']:
                grouped_matches.append(grouped)

        if not matches:
            await event.reply("तत् शब्दम् शब्दरूपम् वा न जानामि।")
        else:
            for match in matches: # grouped_matches maybe
                keyboard = [[
                    Button.inline(
                        'रूपं दर्शयतु', data=f'wordsearch_#root_#linga'
                    )
                ]]
                await event.respond(match[0], buttons=keyboard)


@bot.on(events.NewMessage(pattern='^/shabda'))
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

    if search_key == "":
        await event.respond('USAGE: /shabda शब्दम्/ शब्दरूपम्')
    else:
        print(Shabda.search(search_key))
        matches = [
            format_word_match(match)
            for match in Shabda.search(search_key)
        ]
        if not matches:
            await event.reply("तत् शब्दम् शब्दरूपम् वा न जानामि।")
        else:
            for match in matches:
                keyboard = [[
                    Button.inline(
                        'रूपं दर्शयतु', data=f'wordsearch_{match[1]}'
                    )
                ]]
                await event.respond(match[0], buttons=keyboard)


@bot.on(events.NewMessage(pattern='^/shabdarupa'))
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


@bot.on(events.NewMessage(pattern='^/shabdarupa_new'))
async def show_word_forms_new(event):
    words = event.text.split()
    if len(words) == 3:
        root = words[1]
        gender = words[2]
        rupaani = Heritage.get_declensions(root, gender)
        await event.reply(format_word_forms(root, rupaani))
    else:
        await event.reply("USAGE: /shabdarupa root gender")


@bot.on(events.NewMessage(pattern='^/split'))
async def sandhi_samaasa_split(event):
    """Output the sandhi split of the input word."""
    global transliteration_scheme
    input_line = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id
    input_line = sanscript.transliterate(
        input_line,
        transliteration_scheme[sender_id]['input'],
        transliteration_config['internal']
    )
    split_line = Vigraha.split(input_line)
    print(f"SPLIT: '{input_line}' --> '{split_line}'")
    if input_line == "":
        await event.respond('USAGE: /split पद')
    else:
        await event.reply(split_line)

###############################################################################


def main():
    bot.start(bot_token=config.TelegramConfig.bot_token)
    bot.run_until_disconnected()


###############################################################################


if __name__ == '__main__':
    main()
