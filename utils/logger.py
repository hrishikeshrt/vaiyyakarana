#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger Setup

@author: Hrishikesh Terdalkar

https://docs.python.org/3/howto/logging.html
https://stackoverflow.com/questions/17035077/logging-to-multiple-log-files-from-different-classes-in-python
"""

import logging


def setup_logger(logger_name, log_file=None, stream=None, level=logging.DEBUG,
                 append=False):
    '''
    Setup a Logger
    '''
    logmode = 'a' if append else 'w'

    logr = logging.getLogger(logger_name)
    logr.setLevel(level)
    logr.handlers = []

    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    if log_file:
        fileHandler = logging.FileHandler(log_file, mode=logmode)
        fileHandler.setFormatter(formatter)
        fileHandler.setLevel(level)
        logr.addHandler(fileHandler)

    if stream:
        streamHandler = logging.StreamHandler(stream)
        streamHandler.setFormatter(formatter)
        streamHandler.setLevel(level)
        logr.addHandler(streamHandler)
