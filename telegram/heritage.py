#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  1 11:18:04 2021

@author: Hrishikesh Terdalkar


Python Wrapper for Inria Heritage Platform

Can query through web mirror and unix shell

UNIX Shell
- Heritage_Platform/ML/ contains the scripts
- export QUERY_STRING as shell variable
  (referred to as OPTION_STRING in this code alongwith the '&text=TEXT' part)
- execute various scripts, such as ./reader
- still produces HTML output that needs to be parsed


# Default input needs to be in the devanagari format
# Heritage.dn2vh() function will convert this to VH
"""

import os
import time
import random
import signal
import logging
import requests
import subprocess
import urllib.parse

from bs4 import BeautifulSoup

from logger import setup_logger

scriptname, _ = os.path.splitext(os.path.basename(__file__))
setup_logger('heritage', f'{scriptname}.log')
log = logging.getLogger('heritage')

###############################################################################


def timeout_handler(signum, frame):
    raise TimeoutError("Time limit exceeded.")


signal.signal(signal.SIGALRM, timeout_handler)


###############################################################################


class Heritage:
    """
    Heritage Platform

    Python wrapper for using various utilities from INRIA Heritage Platform
    """

    INRIA_URL = 'https://sanskrit.inria.fr/cgi-bin/SKT/'
    ACTIONS = {
        'reader': {
            'shell': 'reader',
            'web': 'sktreader.cgi'
        },
        'search': {
            'shell': 'indexer',
            'web': 'sktindex.cgi'
        },
        'generator': {
            'shell': 'declension',
            'web': 'sktdeclin.cgi'
        },
        'lemma': {
            'shell': 'lemmatizer',
            'web': 'sktlemmatizer.cgi'
        }
    }

    def __init__(self, repository_dir, base_url=None, method='shell'):
        """
        Initialize Heritage Class

        Parameters
        ----------
        repository_dir : str
            Path to the Heritage_Platform repository.
        base_url : str, optional
            URL for the Heritage Platform Mirror.
            If None, the official INRIA website will be used.
            The default is None.
        method : str, optional
            Method used to obtain results. Results can be obtained either using
            the web installation or using UNIX shell.

            Possible values are, 'shell' and 'web'
            The default is 'shell'.
        """
        self.base_url = self.INRIA_URL if base_url is None else base_url
        self.heritage_dir = repository_dir
        self.scripts_dir = os.path.join(self.heritage_dir, 'ML')
        self.method = method.lower()

    ###########################################################################
    # Utilities (Actions)

    def get_analysis(self):
        """
        Under Construction.
        Utility to obtain morphological analysis using Reader Companion
        TODO: Port get_analysis.py and parse_analysis.py

        Returns
        -------
        result : dict
            Result
        """
        options = {
            'lex': 'SH',  # Lexicon (MW) Monier-Williams (SH) Heritage
            'cache': 't',  # Use Cache (t)rue, (f)alse
            'st': 't',  # Sentence (t)rue, Word (f)alse
            'us': 't',  # Unsandhied (t)rue, (f)alse
                        # if 'us' is 'f', "ca eva" is parsed as "ca_eva",
                        # "tathā eva" as "tathā_eva" etc.
            'cp': 't',  # Full Parser Strength (t)rue, (f)alse
            't': 'VH',  # Transliteration Scheme (Must be VH)
            'mode': 'p',  # Parse Mode (p)arse, (g)raph, (s)ummary
            'topic': '',
            'corpmode': '',
            'corpdir': '',
            'sentno': ''
        }
        return options

    # ----------------------------------------------------------------------- #

    def search_lexicon(self, word, lexicon='MW'):
        """
        Search a word in the dictionary

        Parameters
        ----------
        word : str
            Sanskrit Word to search (in Devanagari)
        lexicon : str, optional
            Lexicon to search the word in.
            Possible values are,
                * MW: Monier-Williams Dictionary
                * SH: Heritage Dictionary
            The default is 'MW'.

        Returns
        -------
        matches : list
            List of matches.
        """
        options = {
            'lex': lexicon,
            't': 'VH',
            'q': self.prepare_input(word)
        }
        result = self.get_result('search', options)
        soup = BeautifulSoup(result, 'html.parser')
        matches = soup.find('table', class_='yellow_cent')

        return matches

    # ----------------------------------------------------------------------- #

    def search_inflected_form(self, word, category):
        """
        Search an inflected form

        Parameters
        ----------
        word : str
            Sanskrit Word to search (in Devanagari)
        category : str
            Type of the word
                * Noun: Noun
                * Pron: Pronoun
                * Part: Participle
                * Inde: Indeclinible
                * Absya, Abstvaa, Voca, Iic, Ifc, Iiv, Piic etc.
        Returns
        -------
        matches : list
            List of matches.
        """
        options = {
            't': 'VH',
            'q': self.prepare_input(word),
            'c': category
        }
        result = self.get_result('lemma', options)
        soup = BeautifulSoup(result, 'html.parser')
        matches = soup.find('table', class_='yellow_cent')
        return matches

    ###########################################################################
    # Fetch Result through Web or Shell

    def get_result_from_web(self, url, options, attempts=3):
        """
        Get results from the Heritage Platform web mirror
        Exponential backoff is used in case there are network errors

        Parameters
        ----------
        url : str
            URL of the CGI script to call
            Heritage.get_url() can be used to generate the supported URLs
        options : dict
            Dictionary containing valid options for the script
        attempts : int, optional
            Number of attempts for the exponential backoff
            The default is 3.

        Returns
        -------
        str
            Result (HTML) obtained
        """

        query_string = '&'.join([f'{k}={v}' for k, v in options.items()])
        query_url = f'{url}?{query_string}'

        # query with exponential-backoff
        r = requests.get(query_url)

        if r.status_code != 200:
            for n in range(attempts):
                if n == 0:
                    print(f"QUERY_URL: {query_url}")
                    log.warning(f"URL: {query_url}")

                log.warning(f"Status Code: {r.status_code} (n = {n})")
                print(f"Status Code: {r.status_code}. (n = {n})")

                fn = n
                backoff = (2 ** fn) + random.random()
                time.sleep(backoff)
                r = requests.get(query_url)

                if r.status_code == 200:
                    log.info(f"Resolved! (n = {n})")
                    print(f"Resolved! (n = {n})")
                    break
            else:
                log.warning(f"Failed on '{query_url}' after {n} attempts.")
                print(f"Failed on '{query_url}' after {n} attempts.")

        return r.text

    # ----------------------------------------------------------------------- #

    def get_result_from_shell(self, path, options, timeout=15):
        """
        Get results from the Heritage Platform's local installation via shell

        Parameters
        ----------
        path : str
            Path to the executable script
            Heritage.get_path() can be used to generate the supported paths
        options : dict
            Valid options for the script
        timeout : int, optional
            Timeout in seconds, after which the function will abort.
            The default is 15.

        Returns
        -------
        result : str
            Result (HTML) obtained
        """
        query_string = '&'.join([f'{k}={v}' for k, v in options.items()])
        environment = {'QUERY_STRING': query_string}
        signal.alarm(timeout)
        try:
            result = str(subprocess.check_output(path, env=environment))
        except TimeoutError:
            log.error("TimeoutError")
            return None
        signal.alarm(0)
        return result

    # ----------------------------------------------------------------------- #

    def get_result(self, action, options, *args, **kwargs):
        """
        High-level function to obtain result for various actions

        Avoids the hassle of generating the URL or PATH.
        Utilizes the Heritage.method attribute to determine
        whether to fetch through shell or web.

        Parameters
        ----------
        action : str
            Action value corresponding to the utility to be used.
            Refer to Heritage.ACTIONS
        options : dict
            Valid options for the specified action

        Returns
        -------
        str
            Result (HTML) obtained
        """
        if self.method == 'shell':
            path = self.get_path(action)
            return self.get_result_from_shell(path, options, *args, **kwargs)
        if self.method == 'web':
            url = self.get_url(action)
            return self.get_result_from_web(url, options, *args, **kwargs)
        log.error("Method must be 'shell' or 'web'.")

    ###########################################################################
    # URL or Path Builders

    def get_url(self, action):
        """URL Builder"""
        return urllib.parse.urljoin(self.base_url, self.ACTIONS[action]['cgi'])

    def get_path(self, action):
        """Path Builder"""
        return os.path.join(self.scripts_dir, self.ACTIONS[action]['shell'])

    ###########################################################################

    def prepare_input(self, input_text):
        """
        Prepare Input
            * Convert Devanagari to Velthuis
            * Join words by '+' instead of by whitespaces
        """
        return '+'.join(self.dn2vh(' '.join(input_text.split())))

    @staticmethod
    def dn2vh(text):
        """
        Convert Devanagari to Velthuis

        Heritage Platform uses its own DN to VH conversion
        This deviates from the standard one (from Wiki or other sources)
        Following is a translation of the JS function convert() from the
        Heritage Platform
        Source URL: http://hrishirt.cse.iitk.ac.in/heritage/DICO/utf82VH.js
        """

        inHex = ["05", "06", "07", "08", "09", "0a", "0b", "60", "0c", "0f",
                 "10", "13", "14", "02", "01", "03", "3d", "4d"]
        outVH = ["a", "aa", "i", "ii", "u", "uu", ".r", ".rr", ".l", "e", "ai",
                 "o", "au", ".m", "~l", ".h", "'", ""]
        matIn = ["3e", "3f", "40", "41", "42", "43", "44", "62", "47", "48",
                 "4b", "4c"]
        consIn = ["15", "16", "17", "18", "19", "1a", "1b", "1c", "1d", "1e",
                  "1f", "20", "21", "22", "23", "24", "25", "26", "27", "28",
                  "2a", "2b", "2c", "2d", "2e", "2f", "30", "32", "35", "36",
                  "37", "38", "39", "00"]

        orig = text
        output = ''
        wasCons = False

        for i in range(len(orig)):
            origC = orig[i]
            hexcode = hex(ord(origC)).lstrip('0x')
            lenL = len(hexcode)
            hexcode = '0' * (4 - lenL) + hexcode

            check = hexcode[2:]
            init = hexcode[:2]

            if init != '09':
                check = '00'
            consOut = ["k", "kh", "g", "gh", "f", "c", "ch", "j", "jh", "~n",
                       ".t", ".th", ".d", ".dh", ".n", "t", "th", "d", "dh",
                       "n", "p", "ph", "b", "bh", "m", "y", "r", "l", "v", "z",
                       ".s", "s", "h", origC + ""]

            for j in range(len(inHex)):
                if check == inHex[j]:
                    if check in ["01", "02", "03", "3d"]:
                        if wasCons:
                            output += "a" + outVH[j]
                        else:
                            output += outVH[j]
                    else:
                        output += outVH[j]
                    wasCons = False

            for j in range(len(consIn)):
                if check == consIn[j]:
                    if wasCons:
                        output += "a" + consOut[j]
                    else:
                        output += consOut[j]
                    wasCons = (check != '00')
                    if i == len(orig) - 1:
                        output += "a"
            for j in range(len(matIn)):
                if check == matIn[j]:
                    output += outVH[j+1]
                    wasCons = False

        return output

###############################################################################


if __name__ == '__main__':
    HOME_DIR = os.path.expanduser('~')
    HERITAGE_DIR = os.path.join(
        HOME_DIR, 'git', 'heritage', 'Heritage_Platform'
    )

    H = Heritage(HERITAGE_DIR)

###############################################################################
