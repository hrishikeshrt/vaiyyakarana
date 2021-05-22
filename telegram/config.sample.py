#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 16:06:13 2020

@author: Hrishikesh Terdalkar
"""

import os

###############################################################################

home_dir = os.path.expanduser('~')
data_dir = os.path.join(os.path.realpath(__file__), 'data')

dhatu_file = os.path.join(data_dir, 'dhatu.json')
shabda_file = os.path.join(data_dir, 'shabda.json')

hellwig_splitter_dir = ''
heritage_platform_dir = ''
suggestion_dir = 'suggestions'

###############################################################################


class TelegramConfig:
    api_id = ''
    api_hash = ''
    bot_user = ''
    bot_name = ''
    bot_token = ''

###############################################################################
