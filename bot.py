#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Vyakarana Bot
"""

import os
import logging
import datetime

from telethon import TelegramClient, events, sync, Button  # noqa
from indic_transliteration import sanscript

import tabulate

from heritage import HeritagePlatform, HERITAGE_LANG
import sanskrit_text as skt

# local
import config

from constants import (
    MESSAGE_INTRODUCTION,
    MESSAGE_AVAILABLE_COMMANDS,
    MESSAGE_NO_SEGMENTER,
    MESSAGE_CHOOSE_SCHEME,
    MESSAGE_THANK_YOU,
    MESSAGE_ASK_QUERY,
    MESSAGE_SELECTED_SCHEME,
    MESSAGE_SHOW_FORMS,
    MESSAGE_ALL_VERB_FORMS,
    MESSAGE_UNKNOWN_WORD,
    MESSAGE_UNKNOWN_VERB,
    MESSAGE_CHOOSE_TYPE,
    MESSAGE_SUGGESTION_REPLY,

    CALLBACK_SEPARATOR,
    CALLBACK_PREFIX_SCHEME,
    CALLBACK_PREFIX_QUERY,

    KEYWORD_FULL,

    ERROR_MESSAGE_COMMON,
    ERROR_MESSAGE_ARGUMENT_MISTMATCH,

    COMMAND_HELP,
    COMMAND_SCHEME,
    COMMAND_VERB,
    COMMAND_WORD,
    COMMAND_CONJUGATION,
    COMMAND_DECLENSION,
    COMMAND_SEGMENTATION,
    COMMAND_SUGGESTION,

    COMMAND_DETAILS,
    BUTTONS,
)
from utils.functions import fold
from utils.dhatupatha import DhatuPatha, DHATU_LANG, LAKARA_LANG, VALUES_LANG
from utils.shabdapatha import ShabdaPatha

###############################################################################

LOGGER = logging.getLogger()
if not LOGGER.hasHandlers():
    LOGGER.addHandler(logging.StreamHandler())

if config.VERBOSE:
    LOGGER.setLevel(logging.INFO)

if config.DEBUG:
    LOGGER.setLevel(logging.DEBUGG)
LOGGER.setLevel(logging.INFO)

###############################################################################
# Initialization

# --------------------------------------------------------------------------- #

DHATUPATHA = DhatuPatha(
    config.DHATU_FILE,
    display_keys=[
        'baseindex', 'dhatu', 'aupadeshik', 'gana', 'pada', 'artha', 'karma',
        'artha_english'
    ]
)

# --------------------------------------------------------------------------- #

SHABDAPATHA = ShabdaPatha(config.SHABDA_FILE)

# --------------------------------------------------------------------------- #

if not config.HELLWIG_SPLITTER_DIR:
    class NonSplitter:
        def split(self, sentence):
            return MESSAGE_NO_SEGMENTER
    VISHLESHANA = NonSplitter()
else:
    from utils.splitter import Splitter
    VISHLESHANA = Splitter(config.HELLWIG_SPLITTER_DIR)

# --------------------------------------------------------------------------- #

if config.HERITAGE_PLATFORM_DIR:
    Heritage = HeritagePlatform(config.HERITAGE_PLATFORM_DIR)
else:
    Heritage = HeritagePlatform('', method='web')

# --------------------------------------------------------------------------- #

if not os.path.isdir(config.SUGGESTION_DIR):
    os.makedirs(config.SUGGESTION_DIR)

###############################################################################
# Bot Client

bot = TelegramClient(
    config.TelegramConfig.bot_user,  # Session Identifier
    config.TelegramConfig.api_id,
    config.TelegramConfig.api_hash
)

###############################################################################
# Transliteration Configuration

TRANSLITERATION_SCHEMES = {
    sanscript.DEVANAGARI: 'देवनागरी',
    sanscript.HK: 'Harvard-Kyoto',
    sanscript.VELTHUIS: 'Velthuis',
    sanscript.ITRANS: 'ITRANS',
    sanscript.SLP1: 'SLP1',
    sanscript.WX: 'WX'
}
TRANSLITERATION_SCHEME_COMMAND = sanscript.HK
TRANSLITERATION_SCHEME_DEFAULT = sanscript.DEVANAGARI
TRANSLITERATION_SCHEME_INTERNAL = sanscript.DEVANAGARI

###############################################################################

transliteration_scheme = {}

###############################################################################

GENDER_MAP = {
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
        'input': TRANSLITERATION_SCHEME_DEFAULT
    })['input']


###############################################################################
# Output Formatters


def format_word_match(root, gender, cases):
    """ Print root, gender, list(vibhakti - vachan) """
    output = [
        f'<b>प्रातिपदिकम्</b> - {root}',
        f'<b>लिङ्गम्</b> - {gender}',
        '----------'
    ]

    for ele in cases:
        output.append(f"{ele['case']} {ele['number']}")
    output.append('----------')

    return output


def format_verb_match(dhaatu):
    output = []
    kramanka = ''
    for k, v in dhaatu['dhatu'].items():
        output_key = DHATU_LANG.get(k, k)
        output_val = v
        if output_key == 'क्रमाङ्कः':
            kramanka = output_val
            continue
        if k in VALUES_LANG:
            output_val = VALUES_LANG[k][v]
        output.append(f'**{output_key}** - {output_val}')

    if dhaatu['desc']:
        output.append("")
        output.append(f"**{dhaatu['desc']}**")

    max_len = max([len(output[i]) for i in range(len(output)-1) if i % 2 == 0])
    output2 = []
    i = 0
    while i < len(output):
        space_counter = max_len + 15 - len(output[i])
        output2.append((' '*space_counter).join(output[i:i+2]))
        i = i + 2

    output2.append('----------')

    return '\n'.join(output2), kramanka


def format_declensions(rupaani):
    formatted_table = tabulate.tabulate(
        [[', '.join(cell) for cell in row] for row in rupaani],
        headers="firstrow",
        tablefmt="rst",
        colalign=['left', 'right', 'right', 'right']
    )

    return f"```{formatted_table}```"


def format_conjugations(dhatu, rupaani, full_flag):
    output = [
        (f"{dhatu['dhatu']} ({dhatu['aupadeshik']}), "
         f"{dhatu['artha']}, {dhatu['artha_english']}"),
        (f"{VALUES_LANG['gana'][dhatu['gana']]}, "
         f"{VALUES_LANG['pada'][dhatu['pada']]}, "),
    ]

    show_lakara = [
        'plat', 'plang', 'plrut', 'plot',
        'alat', 'alang', 'alrut', 'alot'
    ]

    p_output = []
    a_output = []
    for lakara, forms in rupaani.items():
        if not full_flag and lakara not in show_lakara:
            continue
        if forms:
            if lakara.startswith('a'):
                _output = a_output
            if lakara.startswith('p'):
                _output = p_output

            _output.append('')
            _output.append(LAKARA_LANG[lakara])
            _output.append("```" + tabulate.tabulate(
                [[', '.join(cell) for cell in row] for row in forms],
                headers="firstrow",
                tablefmt="rst",
                colalign=['left', 'right', 'right']
            ) + "```")

    # output.append('+' + '-' * 60 + '+',)
    return ['\n'.join(_output)
            for _output in [output, p_output, a_output] if _output]

###############################################################################
# Basic Event Handlers


# Start
@bot.on(events.NewMessage(pattern='^/start'))
async def start(event):
    """Send a message when the command /start is issued."""

    await event.respond('\n'.join(MESSAGE_INTRODUCTION), parse_mode='html')

    # call help handler
    await help_handler(event)

    # call to scheme setting
    await set_scheme(event)

    raise events.StopPropagation


# Help
@bot.on(events.NewMessage(
    pattern=f'^/({"|".join(COMMAND_DETAILS[COMMAND_HELP]["command"])})'
))
async def help_handler(event):
    """Display Help Message"""

    help_message = [MESSAGE_AVAILABLE_COMMANDS]

    for _, _command in COMMAND_DETAILS.items():
        if _command["help"]:
            help_message.append(
                f"{_command['sanskrit'][0]} or /{_command['command'][0]} - "
                f"{_command['help.sanskrit']} ({_command['help.english']})"
            )
    await event.respond('\n'.join(help_message))


# Scheme
@bot.on(events.NewMessage(
    pattern=f'^/({"|".join(COMMAND_DETAILS[COMMAND_SCHEME]["command"])})'
))
async def set_scheme(event):
    '''Set transliteration scheme for user'''
    global transliteration_scheme

    keyboard = []
    current_row = []
    row_length = 2

    # Populating keyboard
    for scheme, scheme_name in TRANSLITERATION_SCHEMES.items():
        current_row.append(
            Button.inline(
                scheme_name,
                data=f'{CALLBACK_PREFIX_SCHEME}_{scheme}'
            )
        )
        if len(current_row) == row_length:
            keyboard.append(current_row)
            current_row = []

    response_message = [MESSAGE_CHOOSE_SCHEME]

    # Asking user to choose a keyboard scheme
    await event.respond(
        '\n'.join(response_message), buttons=keyboard, parse_mode='html'
    )

    # while event.data.decode('utf-8') == "":
    #     pass


###############################################################################
# Verb Event Handlers


@bot.on(events.NewMessage(
    pattern=f'^/({"|".join(COMMAND_DETAILS[COMMAND_VERB]["command"])}) '
))
async def verb_handler(event):
    _command = COMMAND_DETAILS[COMMAND_VERB]
    search_key = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id

    if search_key == "" or len(search_key.split()) > 1:
        await event.reply(
            f'USAGE: /{_command["command"][0]} {_command["argument_text"]}'
        )
    else:
        search_key = sanscript.transliterate(
            search_key,
            get_user_scheme(sender_id),
            TRANSLITERATION_SCHEME_INTERNAL
        )
        matches = [
            format_verb_match(match)
            for match in DHATUPATHA.search(search_key)
        ]
        # print(matches)
        if not matches:
            await event.respond(MESSAGE_UNKNOWN_VERB)
        else:
            display_message = []
            for match in matches:
                match_message = match[0].split("\n")
                kramanka = match[1].replace(".", "_")

                match_message.append(
                    f'{MESSAGE_SHOW_FORMS} '
                    f'/dr_{kramanka}'
                )
                display_message.append('\n'.join(match_message))

            max_char_len = 4096
            curr_msg = []
            curr_length = 0
            for msg in display_message:
                msg_len = len(msg)
                if curr_length + msg_len > max_char_len:
                    await event.respond('\n\n'.join(curr_msg))
                    curr_msg = []
                    curr_length = 0
                curr_msg.append(msg)
                curr_length = curr_length + msg_len
            await event.respond('\n\n'.join(curr_msg))


@bot.on(events.NewMessage(pattern='^/dr_'))
async def conjugation_handler_wrapper(event):
    _bot_command = COMMAND_DETAILS[COMMAND_CONJUGATION]["command"][0]
    words = event.text.split("_")
    kramanka = '.'.join(words[1:3])
    full_keyword = KEYWORD_FULL if KEYWORD_FULL in words else ''
    event.text = ' '.join([f'/{_bot_command}', kramanka, full_keyword])
    await conjugation_handler(event)
    raise events.StopPropagation


@bot.on(events.NewMessage(
    pattern=f'^/({"|".join(COMMAND_DETAILS[COMMAND_CONJUGATION]["command"])}) '
))
async def conjugation_handler(event):
    words = event.text.split()
    # print(words)
    search_key = words[1]
    full_flag = KEYWORD_FULL in words

    if search_key == "" or len(search_key.split()) > 1:
        pass
    else:
        dhaatu_idx = DHATUPATHA.validate_index(search_key)
        if dhaatu_idx:
            # print(f"VERBINDEX: {dhaatu_idx}")
            dhaatu = DHATUPATHA.get(dhaatu_idx)
            rupaani = DHATUPATHA.get_forms(dhaatu_idx)
            dhaturupa_output = format_conjugations(dhaatu, rupaani, full_flag)
            if not full_flag:
                # Provide option to check all lakArAH
                command_key = search_key.replace(".", "_")
                full_command = (
                    f'\n{MESSAGE_ALL_VERB_FORMS} '
                    f'/dr_{command_key}_full'
                )
                dhaturupa_output.append(full_command)
            for output in dhaturupa_output:
                await event.respond(output)
        else:
            # print(f"INVALID_VERBINDEX: {dhaatu_idx}")
            pass
    raise events.StopPropagation


###############################################################################
# Word Event Handlers


@bot.on(events.NewMessage(
    pattern=f'^/({"|".join(COMMAND_DETAILS[COMMAND_WORD]["command"])}) '
))
async def word_handler(event):
    _command = COMMAND_DETAILS[COMMAND_WORD]
    search_key = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id

    if search_key == "" or len(search_key.split()) > 1:
        await event.reply(
            f'USAGE: /{_command["command"][0]} {_command["argument_text"]}'
        )
    else:
        search_key = sanscript.transliterate(
            search_key,
            get_user_scheme(sender_id),
            TRANSLITERATION_SCHEME_INTERNAL
        )
        matches = []
        grouped_matches = {}

        analyses = Heritage.get_analysis(search_key)
        for _, solution in analyses.items():
            has_gender = False
            for word_analysis in solution['words'][0]:
                grouped = {}
                grouped['genders'] = {}
                for analysis in word_analysis['analyses']:
                    grouped['root'] = word_analysis['root']
                    _match = {}
                    _match['root'] = word_analysis['root']
                    for x in analysis:
                        for a_key, a_values in HERITAGE_LANG.items():
                            if x in a_values:
                                _match[a_key] = a_values[x]
                                if a_key == 'gender':
                                    has_gender = True

                    if has_gender:
                        if _match['gender'] not in grouped['genders']:
                            grouped['genders'][_match['gender']] = []

                        # Hack to circumvent the आकारान्त root issue
                        # present in Heritage Platform
                        if _match['gender'] == 'स्त्रीलिङ्गम्':
                            if _match['root'][-1] in skt.VYANJANA:
                                _fixed_root = _match['root'] + skt.MATRA[0]
                                _match['root'] = _fixed_root
                                grouped['root'] = _fixed_root

                        grouped['genders'][_match['gender']].append({
                            'case': _match['case'],
                            'number': _match['number']
                        })
                        matches.append(_match)

                if grouped['genders']:
                    if grouped['root'] not in grouped_matches:
                        grouped_matches[grouped['root']] = {}

                    for gender, gender_values in grouped['genders'].items():
                        if gender not in grouped_matches[grouped['root']]:
                            grouped_matches[grouped['root']][gender] = []
                        grouped_matches[grouped['root']][gender].extend(
                            gender_values
                        )

        if not matches:
            await event.reply(MESSAGE_UNKNOWN_WORD)
        else:
            # keyboard = []
            display_message = []
            for root, genders in grouped_matches.items():
                root_en = sanscript.transliterate(
                    root,
                    TRANSLITERATION_SCHEME_INTERNAL,
                    TRANSLITERATION_SCHEME_COMMAND
                )
                for gender in genders:
                    match_message = format_word_match(
                        root, gender, genders[gender]
                    )
                    gender_en = GENDER_MAP[gender]
                    match_message.append(
                        f'{MESSAGE_SHOW_FORMS} '
                        f'/sr_{root_en}_{gender_en}'
                    )

                    display_message.append('\n'.join(match_message))

            await event.respond(
                '\n\n'.join(display_message), parse_mode='html'
            )


@bot.on(events.NewMessage(
    pattern=f'^/({"|".join(COMMAND_DETAILS[COMMAND_DECLENSION]["command"])}) '
))
async def declension_handler(event):
    _command = COMMAND_DETAILS[COMMAND_DECLENSION]
    words = event.text.split()
    if len(words) == 3:
        root = words[1]
        gender = words[2]

        # print(f'WORDFORMS: {root} {gender}')
        shabdapatha_gender = GENDER_MAP[gender].replace('a', 'm')
        shabda_idx = SHABDAPATHA.get_word(root, shabdapatha_gender)
        if shabda_idx is not None:
            rupaani = SHABDAPATHA.get_forms(shabda_idx)
        else:
            rupaani = Heritage.get_declensions(root, gender)

        rupaani[0][0] = ""
        await event.respond('\n'.join([
            f"**प्रातिपदिकम्**: {root}, **लिङ्गम्**: {gender}",
            format_declensions(rupaani)
        ]))
    else:
        await event.reply(
            f'USAGE: /{_command["command"][0]} {_command["argument_text"]}'
        )
    raise events.StopPropagation


@bot.on(events.NewMessage(pattern='^/sr_'))
async def declension_handler_wrapper(event):
    _bot_command = COMMAND_DETAILS[COMMAND_DECLENSION]["command"][0]
    words = event.text.split("_")
    # Change back root from ITRANS to devanagari
    words[1] = sanscript.transliterate(
        words[1],
        TRANSLITERATION_SCHEME_COMMAND,
        TRANSLITERATION_SCHEME_INTERNAL
    )
    # Fetch gender
    words[2] = GENDER_MAP[words[2]]
    event.text = ' '.join([f'/{_bot_command}', words[1], words[2]])
    await declension_handler(event)
    raise events.StopPropagation


###############################################################################
# Segmentation Event Handler

@bot.on(events.NewMessage(
    pattern=f'^/({"|".join(COMMAND_DETAILS[COMMAND_SEGMENTATION]["command"])}) '
))
async def segmentation_handler(event):
    """Output the sandhi split of the input word."""
    _command = COMMAND_DETAILS[COMMAND_SEGMENTATION]
    input_line = ' '.join(event.text.split()[1:])
    sender_id = event.sender.id
    input_line = sanscript.transliterate(
        input_line,
        get_user_scheme(sender_id),
        TRANSLITERATION_SCHEME_INTERNAL
    )
    # Limit on IAST text is 128 characters
    # 115 is just a heuristic approximation for Devanagari text
    # so that resulting IAST is < 128 length

    if input_line == "":
        await event.reply(
            f'USAGE: /{_command["command"][0]} {_command["argument_text"]}'
        )
    else:
        fold_input_line = fold(input_line, width=115)
        split_output = VISHLESHANA.split(fold_input_line)
        # print(f"SPLIT: '{input_line}' --> '{split_line}'")
        await event.respond(split_output)

###############################################################################
# Suggestion Event Handler


@bot.on(events.NewMessage(
    pattern=f'^/({"|".join(COMMAND_DETAILS[COMMAND_SUGGESTION]["command"])}) '
))
async def suggestion_handler(event):
    """Give suggestions"""
    message = event.text
    sender = await event.get_sender()
    user_file = os.path.join(config.SUGGESTION_DIR, f"{sender.username}.txt")
    with open(user_file, 'a') as f:
        f.write("\n".join([f"--- {datetime.datetime.now()} ---", message, ""]))
    await event.reply(MESSAGE_SUGGESTION_REPLY)


###############################################################################
# Command Handler Map

COMMAND_HANDLERS = {
    COMMAND_HELP: help_handler,
    COMMAND_VERB: verb_handler,
    COMMAND_WORD: word_handler,
    COMMAND_CONJUGATION: conjugation_handler,
    COMMAND_DECLENSION: declension_handler,
    COMMAND_SEGMENTATION: segmentation_handler,
    COMMAND_SUGGESTION: suggestion_handler
}

###############################################################################
# Inline Button Callback Handlers


@bot.on(events.CallbackQuery(pattern=f'^{CALLBACK_PREFIX_SCHEME}_'))
async def scheme_handler(event):
    """ Invoked from set_scheme() """
    global transliteration_scheme
    sender_id = event.sender.id

    if sender_id not in transliteration_scheme:
        transliteration_scheme[sender_id] = {
            'input': TRANSLITERATION_SCHEME_DEFAULT,
            'output': TRANSLITERATION_SCHEME_DEFAULT
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
        MESSAGE_THANK_YOU,
        ' '.join([MESSAGE_SELECTED_SCHEME, TRANSLITERATION_SCHEMES[scheme]]),
        MESSAGE_ASK_QUERY
    ]

    await event.respond('\n'.join(response_message))
    raise events.StopPropagation


@bot.on(events.CallbackQuery(
    pattern=f'^{CALLBACK_PREFIX_QUERY}{CALLBACK_SEPARATOR}')
)
async def query_handler(event):
    """ Invoked from search() when single words given as input """
    # print("qh " + event.data.decode('utf-8'))
    if 'help' in event.data.decode('utf-8'):
        await help_handler(event)
    else:
        await query_redirect(event)


async def query_redirect(event):
    data = event.data.decode('utf-8')
    prefix, text, query_id = data.split(CALLBACK_SEPARATOR)

    for _command in [COMMAND_WORD, COMMAND_VERB, COMMAND_SEGMENTATION]:
        if query_id == BUTTONS[_command]["id"]:
            _bot_command = COMMAND_DETAILS[_command]["command"][0]
            event.text = f"/{_bot_command} {text}"
            await COMMAND_HANDLERS[_command](event)


###############################################################################
# Non-Commands


def make_buttons(event_text, _buttons, _prefix, _separator):
    """Generate Clickable Buttons"""
    text = f"{_prefix}{_separator}{event_text}{_separator}"
    buttons = []
    for _button_row in _buttons:
        _row = []
        for _button in _button_row:
            _row.append(
                Button.inline(_button["text"], data=f"{text}{_button['id']}")
            )
        if _row:
            buttons.append(_row)
    return buttons


@bot.on(events.NewMessage(pattern='^[^/]'))
async def process_non_command(event):
    """Handle messages that do not start with /"""
    event_text = event.text

    # print(f"Search: {event_text}")
    keys = event_text.split()

    command_found = False
    for _command_id, _handler in COMMAND_HANDLERS.items():
        _command = COMMAND_DETAILS[_command_id]
        LOGGER.info(_command_id)
        LOGGER.info(_command)
        _commands = [
            sanscript.transliterate(
                sanskrit_word,
                TRANSLITERATION_SCHEME_INTERNAL,
                output_scheme
            )
            for sanskrit_word in _command["sanskrit"]
            for output_scheme in TRANSLITERATION_SCHEMES
        ] + _command["english"]

        if keys[0] in _commands:
            if _command["arguments"] == -1:
                command_found = True
                await _handler(event)
            elif len(keys[1:]) == _command["arugments"]:
                command_found = True
                await _handler(event)
            else:
                await event.respond(ERROR_MESSAGE_ARGUMENT_MISTMATCH)
                await help_handler(event)

    if not command_found:
        _buttons = [
            [BUTTONS[COMMAND_WORD], BUTTONS[COMMAND_VERB]],
            [BUTTONS[COMMAND_SEGMENTATION]],
            [BUTTONS[COMMAND_HELP]]
        ]
        buttons = make_buttons(
            event_text,
            _buttons=_buttons,
            _prefix=CALLBACK_PREFIX_QUERY,
            _separator=CALLBACK_SEPARATOR
        )
        await event.reply(MESSAGE_CHOOSE_TYPE, buttons=buttons)


###############################################################################


def main():
    bot.start(bot_token=config.TelegramConfig.bot_token)
    bot.run_until_disconnected()


###############################################################################


if __name__ == '__main__':
    main()
