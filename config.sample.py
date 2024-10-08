#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 16:06:13 2020

@author: Hrishikesh Terdalkar
"""

import os

###############################################################################

HOME_DIR = os.path.expanduser('~')
DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')

DHATU_FILE = os.path.join(DATA_DIR, 'dhatu.json')
SHABDA_FILE = os.path.join(DATA_DIR, 'shabda.json')

HELLWIG_SPLITTER_DIR = ''
HERITAGE_PLATFORM_DIR = ''
SUGGESTION_DIR = 'suggestions'

VERBOSE = True
DEBUG = False

###############################################################################


class TelegramConfig:
    api_id = ''
    api_hash = ''
    bot_user = ''
    bot_name = ''
    bot_token = ''

    use_custom_datacenter = True
    dc_id = 5
    dc_server_address = '91.108.56.158'
    dc_port = 443

###############################################################################
