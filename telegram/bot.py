#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 27 19:04:19 2020

@author: Hrishikesh Terdalkar
"""

from telethon import TelegramClient, events, sync, Button
from indic_transliteration import sanscript

import tabulate

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
            return "दत्तपदस्य विग्रहं कर्तुं न शक्यते"
    Vigraha = NonSplitter()
else:
    import splitter
    Vigraha = splitter.Splitter(config.hellwig_splitter_dir)

if config.heritage_platform_dir:
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
        sanscript.DEVANAGARI: 'देवनागरी',
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

gender_map = {
    'm': 'पुंलिङ्गम्',
    'f': 'स्त्रीलिङ्गम्',
    'n': 'नपुंसकलिङ्गम्',
    'a': 'त्रिलिङ्गम्',
    'पुंलिङ्गम्': 'm',
    'स्त्रीलिङ्गम्': 'f',
    'नपुंसकलिङ्गम्': 'n',
    'त्रिलिङ्गम्': 'a'
}

###############################################################################


def get_user_scheme(sender_id):
    global transliteration_scheme
    return transliteration_scheme.get(sender_id, {
        'input': transliteration_config['default']
    })['input']

###############################################################################
# Output formats for dhatu dhaturupa shabda and shabdarupa


def format_word_match(root, gender, cases):
    """ Print root, gender, list(vibhakti - vachan) """
    output = [
        f'<b>प्रातिपदिकम्</b> - {root}',
        f'<b>लिङ्गम्</b> - {gender}',
        '----------'
        # f'<b>vachana - vibhakti </b>'
    ]

    for ele in cases:
        output.append(f"{ele['case']} {ele['number']}")
    output.append('----------')

    return output


def format_verb_match(dhaatu):

    output = []
    kramanka = ''
    for k, v in dhaatu['dhatu'].items():
        output_key = dhatupatha.DHATU_LANG.get(k, k)
        output_val = v
        if output_key == 'क्रमाङ्कः':
            kramanka = output_val
            continue
        if k in dhatupatha.VALUES_LANG:
            output_val = dhatupatha.VALUES_LANG[k][v]
        output.append(f'**{output_key}** - {output_val}')

    if dhaatu['desc']:
        output.append(dhaatu['desc'])

    max_len = max([len(output[i]) for i in range(len(output)-1) if i%2==0])
    output2 = []
    i = 0
    while i < len(output):
        space_counter = max_len + 15 - len(output[i])
        output2.append((' '*space_counter).join(output[i:i+2]))
        i = i + 2

    output2.append('----------')

    return '\n'.join(output2), kramanka


def format_word_forms(shabda, rupaani):
    output = [
        (f"**{shabda['word']}** ({shabda['end']}) "
         f"({shabdapatha.VALUES_LANG['linga'][shabda['linga']]})"),
        '+' + '-' * 60 + '+',
    ]
    for idx, forms in enumerate(rupaani):
        output.append(f"**{shabdapatha.VIBHAKTI[idx]}**: {forms}")
    return '\n'.join(output)


def format_word_forms_new(rupaani):
    formatted_table = tabulate.tabulate(
        [[', '.join(cell) for cell in row] for row in rupaani],
        headers="firstrow", tablefmt="rst", colalign=['left', 'right', 'right', 'right']
    )

    return f"```{formatted_table}```"


def format_verb_forms(dhatu, rupaani, full_flag):
    output = [
        (f"{dhatu['dhatu']} ({dhatu['swara']}), "
         f"{dhatu['artha']}, {dhatu['artha_english']}"),
        (f"{dhatupatha.VALUES_LANG['gana'][dhatu['gana']]}, "
         f"{dhatupatha.VALUES_LANG['pada'][dhatu['pada']]}, "),
        '+' + '-' * 60 + '+',
            ]

    lakaars = ['plat', 'plang', 'plrut', 'plot', 'alat', 'alang', 'alrut', 'alot']

    for lakara, forms in rupaani.items():
        if not full_flag and lakara not in lakaars:    
            continue
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
        'अहम् धातुपाठं शब्दपाठं पदविग्रहं च जानामि।',
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
        'उपलब्ध-आदेशाः –',
        '/help - साहाय्यक-पटलं दर्शयतु',
        # '/setinputscheme - Choose input scheme (Default - Devanagari).',
        # '/setoutputscheme - Choose output scheme (Default - Devanagari).',
        '/setscheme - लेखनविधानं वृणोतु (यदभावे देवनागरी).',
        '/dhatu - एकं धातुं अन्वेषयतु',
        # '/dhaturupa - Display dhaturup (lakaar).',
        '/shabda - एकं शब्दं अन्वेषयतु',
        # '/shabdarupa - Display shabdarup.',
        '/vigraha - पदं (पदानि) विगृह्णातु (सन्धिसमासौ)'
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

# Inline button handlers

@bot.on(events.CallbackQuery(pattern='^scheme_'))
async def scheme_handler(event):
    """ Invoked from set_scheme() """
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
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern='^query_'))
async def query_handler(event):
    """ Invoked from search() when single words given as input """
    print("qh " + event.data.decode('utf-8'))
    if 'help' in event.data.decode('utf-8'):
        await help(event)
    else:
        await redirect(event)


@bot.on(events.CallbackQuery(pattern='^[wordsearch_]|[verbsearch_]'))
async def query_handler2(event):
    """ Invoked from search_word_new() """
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
                transliteration_config['internal'],
                output_scheme
            )
            for output_scheme in transliteration_config['schemes']
        ]
        dhatu_command = dhatu_command + ['dhatu']

        shabda_command = [
            sanscript.transliterate(
                'शब्द',
                transliteration_config['internal'],
                output_scheme
            )
            for output_scheme in transliteration_config['schemes']
        ]
        shabda_command = shabda_command + ['shabd']

        dhaturupa_command = [
            sanscript.transliterate(
                'धातुरूप',
                transliteration_config['internal'],
                output_scheme
            )
            for output_scheme in transliteration_config['schemes']
        ]
        dhaturupa_command = dhaturupa_command + ['dhaturup']

        shabdarupa_command = [
            sanscript.transliterate(
                'शब्दरूप',
                transliteration_config['internal'],
                output_scheme
            )
            for output_scheme in transliteration_config['schemes']
        ]
        shabdarupa_command = shabdarupa_command + ['shabdarup']

        vigraha_command = [
            sanscript.transliterate(
                'विग्रह',
                transliteration_config['internal'],
                output_scheme
            )
            for output_scheme in transliteration_config['schemes']
        ]

        if keys[0] in dhatu_command:
            await search_verb(event)
        elif keys[0] in shabda_command:
            await search_word_new(event)
        elif keys[0] in dhaturupa_command:
            await show_verb_forms(event)
        elif keys[0] in shabdarupa_command:
            await show_word_forms_new(event)
        elif keys[0] in vigraha_command:
            await sandhi_samaasa_split(event)
        else:
            await event.respond("क्षम्यताम्।")
            await help(event)
    elif len(keys) == 1:
        text = f'query_{event_text}'
        keyboard = [
            [   Button.inline("सुबन्तः", data=f'{text} sup'),
                Button.inline("तिङन्तः", data=f'{text} tiG')    ],
            [   Button.inline("साहाय्यम्", data=f'{text} help')     ]
        ]
        print(keyboard)
        await event.reply('दत्तपदस्य प्रकारं वृणोतु –', buttons=keyboard)
    elif len(keys) > 2:
        vigraha_command = [
            sanscript.transliterate(
                'विग्रह',
                transliteration_config['internal'],
                output_scheme
            )
            for output_scheme in transliteration_config['schemes']
        ]

        if keys[0] in vigraha_command:
            await sandhi_samaasa_split(event)
        else:
            await event.respond("क्षम्यताम्।")
            await help(event)


async def redirect2(event):
    print('Redirect2')
    data = event.data.decode('utf-8')
    words = data.split('_')
    command = words[0]
    if command == 'wordsearch':
        event.text = '/shabdarupa ' + ' '.join(words[1:])
        await show_word_forms_new(event)
    elif command == 'verbsearch':
        event.text = '/dhaturupa ' + ' '.join(words[1:])
        await show_verb_forms(event)


async def redirect(event):
    print("Redirect")
    data = event.data.decode('utf-8')
    text, form = data.split('_')[1].split()
    if form == 'sup':
        event.text = '/shabda ' + text
        await search_word_new(event)
    elif form == 'tiG':
        event.text = '/dhatu ' + text
        await search_verb(event)

###############################################################################


@bot.on(events.NewMessage(pattern='^/dr_'))
async def show_verb_forms_new_wrapper(event):
    words = event.text.split("_")
    full_keyword = 'full' if 'full' in words else ''
    kramanka = '.'.join(words[1:3])
    # # Change back dhaatu and gaNa from ITRANS to devanagari
    # words[1] = sanscript.transliterate(words[1], sanscript.HK, transliteration_config['default'])
    # words[2] = sanscript.transliterate(words[2], sanscript.HK, transliteration_config['default'])
    event.text = ' '.join(['/dhaturupa', kramanka, full_keyword])
    print(f'dr {event.text}')
    await show_verb_forms(event)
    raise events.StopPropagation


@bot.on(events.NewMessage(pattern='^/dhaturupa'))
async def show_verb_forms(event):
    search_key = ' '.join(event.text.split()[1:])
    full_flag = False
    if 'full' in search_key.split():
        full_flag = True
        search_key = ' '.join(search_key.split()[:-1])
    print(f'svf {full_flag}')
    if search_key == "" or len(search_key.split()) > 1:
        #await event.reply('USAGE: /dhaturupa धातुम्/ धातुरूपम्')
        pass
    else:
        dhaatu_idx = Dhatu.validate_index(search_key)
        if dhaatu_idx:
            print(f"VERBINDEX: {dhaatu_idx}")
            dhaatu = Dhatu.get(dhaatu_idx)
            rupaani = Dhatu.get_forms(dhaatu_idx)
            dhaturupa_output = format_verb_forms(dhaatu, rupaani, full_flag)
            if not full_flag:
                """ Provide option to check all lakaras """
                full_dr_command = f'\nFor dhaturupa in all lakaras - /dr_{search_key.replace(".","_")}_full'
                dhaturupa_output = '\n'.join([dhaturupa_output, full_dr_command])
            await event.respond(dhaturupa_output)
        else:
            print(f"INVALID_VERBINDEX: {dhaatu_idx}")
    raise events.StopPropagation


@bot.on(events.NewMessage(pattern='^/dhatu'))
async def search_verb(event):
    global transliteration_scheme
    global transliteration_config
    search_key = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id
    print(f"VERBSEARCH: {search_key}")

    if search_key == "" or len(search_key.split()) > 1:
        await event.reply('USAGE: /dhatu धातुम्/ धातुरूपम्')
    else:
        search_key = sanscript.transliterate(
            search_key,
            get_user_scheme(sender_id),
            transliteration_config['internal']
        )
        matches = [
            format_verb_match(match)
            for match in Dhatu.search(search_key)
        ]
        print(matches)
        if not matches:
            await event.respond('तम् धातुम् धातुरूपम् वा न जानामि।')
        else:
            display_message = []
            for match in matches:
                # keyboard = [[Button.inline('रूपं दर्शयतु',
                #                            data=f'verbsearch_{match[1]}')]]
                # await event.respond(match[0])   #, buttons=keyboard)
                match_message = match[0].split("\n")
                kramanka = match[1].replace(".", "_")

                # # extract dhatu and gaNa
                # dhatu = match_message[0].split()[2].split()[-1]
                # gana = match_message[1].split()[2].split()[-1]

                # # convert to ITRANS
                # dhatu = sanscript.transliterate(dhatu, transliteration_config['default'], sanscript.HK)
                # gana = sanscript.transliterate(gana, transliteration_config['default'], sanscript.HK)
                
                match_message.append(f'रूपं दर्शयतु- /dr_{kramanka}')

                display_message.append('\n'.join(match_message))

            max_char_len = 4096
            curr_msg = []
            curr_length = 0
            for msg in display_message:
                msg_len = len(msg)
                if curr_length + msg_len > max_char_len:
                    print("here3")
                    await event.respond('\n\n'.join(curr_msg))
                    curr_msg = []
                    curr_length = 0
                curr_msg.append(msg)
                curr_length = curr_length + msg_len
            await event.respond('\n\n'.join(curr_msg))


@bot.on(events.NewMessage(pattern='^/sr_'))
async def show_word_forms_new_wrapper(event):
    words = event.text.split("_")
    # Change back root from ITRANS to devanagari
    words[1] = sanscript.transliterate(
        words[1],
        sanscript.HK,
        transliteration_config['internal']
    )
    # Fetch gender
    words[2] = gender_map[words[2]]
    event.text = ' '.join(['/shabdarupa', words[1], words[2]])
    await show_word_forms_new(event)
    raise events.StopPropagation


@bot.on(events.NewMessage(pattern='^/shabdarupa'))
async def show_word_forms_new(event):
    words = event.text.split()
    if len(words) == 3:
        root = words[1]
        gender = words[2]

        print(f'WORDFORMS: {root} {gender}')

        rupaani = Heritage.get_declensions(root, gender)
        await event.respond(format_word_forms_new(rupaani))
    else:
        await event.reply("USAGE: /shabdarupa root gender")
    raise events.StopPropagation


@bot.on(events.NewMessage(pattern='^/shabda'))
async def search_word_new(event):
    global transliteration_scheme
    global transliteration_config

    search_key = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id

    print(f"WORDSEARCH: {search_key}")

    if search_key == "" or len(search_key.split()) > 1:
        await event.reply('USAGE: /shabda शब्दः/ शब्दरूपम्')
    else:
        # wait_message = [
        #     'Please wait.'
        # ]
        # await event.reply('\n'.join(wait_message))

        search_key = sanscript.transliterate(
            search_key,
            get_user_scheme(sender_id),
            transliteration_config['internal']
        )
        matches = []
        grouped_matches = {}
        """ Format of grouped_matches
            {
                'root': {
                    linga_1: [{
                        case: vibhakti_1,
                        number: vachan_1
                    }, ...],
                    linga_2: [...]
                    },
                    ...
                ]
            }
        """
        for solution in Heritage.get_analysis(search_key):
            has_gender = False
            for word_analysis in solution['words'][0]:
                grouped = {}
                grouped['genders'] = {}
                for analysis in word_analysis['analyses']:
                    grouped['root'] = word_analysis['root']
                    match = {}
                    match['root'] = word_analysis['root']
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
                    if grouped['root'] not in grouped_matches:
                        grouped_matches[grouped['root']] = {}

                    for gender, gender_values in grouped['genders'].items():
                        if gender not in grouped_matches[grouped['root']]:
                            grouped_matches[grouped['root']][gender] = []
                        grouped_matches[grouped['root']][gender].extend(
                            gender_values
                        )

        if not matches:  # TODO: verify if this is the condition we need
            await event.reply("तत् शब्दम् शब्दरूपम् वा न जानामि।")
        else:
            print(grouped_matches)
            # keyboard = []
            display_message = []
            for root, genders in grouped_matches.items():
                root_en = sanscript.transliterate(
                    root,
                    transliteration_config['internal'],
                    sanscript.HK
                )
                for gender in genders:
                    # keyboard = [[Button.inline(
                    #     'रूपं दर्शयतु', data=f'wordsearch_{root}_{gender}'
                    # )]]

                    match_message = format_word_match(root, gender, genders[gender])
                    gender_en = gender_map[gender]
                    print(root_en, gender_en)
                    match_message.append(f'रूपं दर्शयतु - /sr_{root_en}_{gender_en}')

                    display_message.append('\n'.join(match_message))
                    print('\n\n'.join(display_message))

                    # await event.respond('\n'.join(display_message), buttons=keyboard, parse_mode='html')
            await event.respond('\n\n'.join(display_message), parse_mode='html')


@bot.on(events.NewMessage(pattern='^/old_shabda'))
async def search_word(event):
    global transliteration_scheme
    global transliteration_config

    search_key = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id

    print(f"WORDSEARCH: {search_key}")

    if search_key == "" or len(search_key.split()) > 1:
        await event.reply('USAGE: /shabda शब्दः/ शब्दरूपम्')
    else:
        search_key = sanscript.transliterate(
            search_key,
            get_user_scheme(sender_id),
            transliteration_config['internal']
        )
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


@bot.on(events.NewMessage(pattern='^/old_shabdarupa'))
async def show_word_forms(event):
    shabda_idx = Shabda.validate_index(' '.join(event.text.split()[1:]))
    if shabda_idx:
        print(f"WORDINDEX: {shabda_idx}")
        shabda = Shabda.get(shabda_idx)
        rupaani = Shabda.get_forms(shabda_idx)
        await event.respond(format_word_forms(shabda, rupaani))
    else:
        print(f"INVALID_WORDINDEX: {shabda_idx}")
        await event.reply("कृपया शब्दक्रमाङ्कं लिखतु।")


@bot.on(events.NewMessage(pattern='^/vigraha'))
async def sandhi_samaasa_split(event):
    """Output the sandhi split of the input word."""
    global transliteration_scheme
    input_line = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id
    input_line = sanscript.transliterate(
        input_line,
        get_user_scheme(sender_id),
        transliteration_config['internal']
    )
    split_line = Vigraha.split(input_line)
    print(f"SPLIT: '{input_line}' --> '{split_line}'")
    if input_line == "":
        await event.reply('USAGE: /split पदः')
    else:
        await event.reply(split_line)

###############################################################################


def main():
    bot.start(bot_token=config.TelegramConfig.bot_token)
    bot.run_until_disconnected()


###############################################################################


if __name__ == '__main__':
    main()
