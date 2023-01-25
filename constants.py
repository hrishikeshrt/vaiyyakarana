#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 19:02:49 2023

@author: Hrishikesh Terdalkar
"""

###############################################################################

MESSAGE_INTRODUCTION = [
    "<h1>स्वागतम्।</h1>",
    "अहम् धातुपाठं शब्दपाठं पदविश्लेषणं च जानामि।",
]

MESSAGE_AVAILABLE_COMMANDS = "उपलब्ध-आदेशाः –"
MESSAGE_CHOOSE_SCHEME = "कृपया एकां लेखनविधिं वृणोतु –"
MESSAGE_THANK_YOU = "धन्यवादः।"
MESSAGE_SELECTED_SCHEME = "वृणीता लेखनविधिः –"
MESSAGE_ASK_QUERY = "कृपया पृच्छतु।"

MESSAGE_SHOW_FORMS = "रूपाणि दर्शयतु –"
MESSAGE_ALL_VERB_FORMS = "सर्वे लकाराः –"
MESSAGE_UNKNOWN_WORD = "तत् शब्दम् शब्दरूपम् वा न जानामि।"
MESSAGE_UNKNOWN_VERB = "तम् धातुम् धातुरूपम् वा न जानामि।"

MESSAGE_NO_SEGMENTER = "विश्लेषणयन्त्राभावात् दत्तपदानां विश्लेषणं कर्तुं न शक्यते।"
MESSAGE_CHOOSE_TYPE = "दत्तपदस्य प्रकारं वृणोतु –"
MESSAGE_SUGGESTION_REPLY = "समीचीना सूचना। धन्यवादः।"

###############################################################################

COMMAND_HELP = "help"
COMMAND_SCHEME = "scheme"
COMMAND_VERB = "dhatu"
COMMAND_WORD = "shabda"
COMMAND_CONJUGATION = "dhaturupa"
COMMAND_DECLENSION = "shabdarupa"
COMMAND_SEGMENTATION = "vishleshana"
COMMAND_SUGGESTION = "suggestion"

###############################################################################

KEYWORD_FULL = "full"

###############################################################################

COMMAND_DETAILS = {
    COMMAND_HELP: {
        "command": ["help"],
        "english": ["help"],
        "sanskrit": ["साहाय्य"],
        "help": True,
        "help.english": "Print this help",
        "help.sanskrit": "साहाय्यक-पटलं दर्शयतु",
        "arguments": 0,
    },
    COMMAND_SCHEME: {
        "command": ["setscheme"],
        "english": ["scheme"],
        "sanskrit": ["लेखनविधि"],
        "help": True,
        "help.english": "Choose input scheme, Default: Devanagari",
        "help.sanskrit": "लेखनविधानं वृणोतु, यदभावे देवनागरी",
        "arguments": 1,
        "argument_text": "[लेखनविधिः]",
    },
    COMMAND_VERB: {
        "command": ["dhatu"],
        "english": ["dhatu"],
        "sanskrit": ["धातु"],
        "help": True,
        "help.english": "Search a verb form",
        "help.sanskrit": "एकं धातुं अन्वेषयतु",
        "arguments": 1,
        "argument_text": "[धातुः धातुरूपम् वा]",
    },
    COMMAND_WORD: {
        "command": ["shabda"],
        "english": ["shabda"],
        "sanskrit": ["शब्द"],
        "help": True,
        "help.english": "Search a word form",
        "help.sanskrit": "एकं शब्दं अन्वेषयतु",
        "arguments": 1,
        "argument_text": "[शब्दः शब्दरूपम् वा]",
    },
    COMMAND_CONJUGATION: {
        "command": ["dhaturupa"],
        "english": ["dhaturupa"],
        "sanskrit": ["धातुरूप"],
        "help": False,
        "help.english": None,
        "help.sanskrit": None,
        "arguments": 1,
        "argument_text": f"[धातुक्रमाङ्क] ({KEYWORD_FULL})",
    },
    COMMAND_DECLENSION: {
        "command": ["shabdarupa"],
        "english": ["shabdarupa"],
        "sanskrit": ["शब्दरूप"],
        "help": False,
        "help.english": None,
        "help.sanskrit": None,
        "arguments": 2,
        "argument_text": "[प्रातिपदिकम्] [लिङ्गम्]",
    },
    COMMAND_SEGMENTATION: {
        "command": ["split", "vishleshana", "vigraha"],
        "english": ["split", "segment"],
        "sanskrit": ["विश्लेषण", "विग्रह"],
        "help": True,
        "help.english": "Split the sandhi and samaasa",
        "help.sanskrit": "पदं (पदानि) विगृह्णातु (सन्धिसमासौ)",
        "arguments": -1,
        "argument_text": "[सन्धिपदं समस्तपदम् वा]"
    },
    COMMAND_SUGGESTION: {
        "command": ["suggest", "feedback", "pratikriya", "suchana"],
        "english": ["suggest", "feedback"],
        "sanskrit": ["सूचना", "प्रतिक्रिया"],
        "help": True,
        "help.english": "Collect feedback",
        "help.sanskrit": "अभिप्रायसङ्कलनं करोतु",
        "arguments": -1,
    },
}

###############################################################################

CALLBACK_SEPARATOR = "___"
CALLBACK_PREFIX_SCHEME = "scheme"
CALLBACK_PREFIX_QUERY = "query"

###############################################################################

BUTTONS = {
    COMMAND_WORD: {
        "id": "sup",
        "text": "सुबन्तम् पदम्",
    },
    COMMAND_VERB: {
        "id": "tiG",
        "text": "तिङन्तम् पदम्",
    },
    COMMAND_SEGMENTATION: {
        "id": "vis",
        "text": "सन्धिपदम् समस्तपदम्",
    },
    COMMAND_HELP: {
        "id": "help",
        "text": "साहाय्यम्",
    }
}

###############################################################################

ERROR_MESSAGE_COMMON = "क्षम्यताम्।"
ERROR_MESSAGE_ARGUMENT_MISTMATCH = "एतेषां शब्दानां तत् कार्यं न शक्यम्।"

###############################################################################
