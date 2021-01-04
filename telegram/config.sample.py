#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 16:06:13 2020

@author: Hrishikesh Terdalkar
"""

import os

###############################################################################

home_dir = os.path.expanduser('~')
hellwig_splitter_dir = os.path.join(
    home_dir, 'git', 'oliverhellwig', 'papers', '2018emnlp', 'code'
)
heritage_platform_dir = os.path.join(
    home_dir, 'git', 'heritage', 'Heritage_Platform'
)

###############################################################################


class TelegramConfig:
    api_id = ''
    api_hash = ''
    bot_user = ''
    bot_name = ''
    bot_token = ''

###############################################################################
