#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 17:35:57 2020

@author: Hrishikesh Terdalkar
"""

import re
import json

import samskrit_text as skt

###############################################################################

VERSION = '2020.11.03.1637'

###############################################################################

SHABDA_LANG = {
    "baseindex": "क्रमाङ्कः",
    "word": "शब्दः",
    "end": "अन्त्यः",
    "forms": "रूपाणि",
    "linga": "लिङ्गम्"
}

###############################################################################

VALUES_LANG = {
    "linga": {
        "P": "पुंलिङ्गम्",
        "S": "स्त्रीलिङ्गम्",
        "N": "नपुंसकलिङ्गम्"
    }
}

###############################################################################

VIBHAKTI = [
    'प्रथमा', 'द्वितीया', 'तृतीया', 'चतुर्थी',
    'पञ्चमी', 'षष्ठी', 'सप्तमी', 'सम्बोधनम्'
]
VACHANA = ['एकवचनम्', 'द्विवचनम्', 'बहुवचनम्']
PURUSHA = ['प्रथमपुरुषः', 'मध्यमपुरुषः', 'उत्तमपुरुषः']

###############################################################################


class ShabdaPatha:
    SEARCH_KEYS = ['word']
    DISPLAY_KEYS = ['baseindex', 'word', 'end', 'linga']

    def __init__(self, shabda_file, search_keys=None, display_keys=None):
        self.search_keys = search_keys or self.SEARCH_KEYS
        self.display_keys = display_keys or self.DISPLAY_KEYS

        with open(shabda_file, encoding='utf-8') as f:
            self.index = json.load(f)

        self.antya_index = {}
        for idx, word in self.index.items():
            word['forms'] = word['forms'].split(';')
            last_varna = word['end'][0]
            if last_varna not in self.antya_index:
                self.antya_index[last_varna] = {
                    v: [] for v in VALUES_LANG['linga']
                }
            self.antya_index[last_varna][word['linga']].append(
                word['baseindex']
            )

    def search(self, search_str, **kwargs):
        """
        Search for a Shabda

        Parameters
        ----------
        search_str : str
            Search string
            Can be the index number, word root, linga, ending or
            any valid form of that shabda

        Returns
        -------
        search_matches : list(dict)
            List of dictionaries (search-result objects) which contain the
            dictionary of dhatu, type of the match and an optional description

        """
        search_matches = []
        index = self.validate_index(search_str)
        if index:
            search_matches.append({
                'shabda': {
                     k: v for k, v in self.index[index].items()
                     if k in self.display_keys
                 },
                'type': 'baseindex',
                'desc': ''
            })

        for shabda_idx, shabda in self.index.items():
            display_shabda = {
                k: v for k, v in shabda.items()
                if k in self.display_keys
            }
            for key in self.search_keys:
                if search_str in shabda[key]:
                    search_matches.append({
                        'shabda': display_shabda,
                        'type': key,
                        'desc': ''
                    })

            if search_str in shabda['forms']:
                indices = [
                    idx for idx, shabda_form in enumerate(shabda['forms'])
                    if shabda_form == search_str
                ]
                for idx in indices:
                    description = '{} {}'.format(
                        VIBHAKTI[idx // 3],
                        VACHANA[idx % 3]
                    )
                    search_matches.append({
                        'shabda': display_shabda,
                        'type': 'rupaani',
                        'desc': description
                        })
        return search_matches

    def get_similar(self, word, linga=None):
        last_varna = skt.split_varna_word(word, False)[-1]
        last_varna = last_varna.replace(skt.HALANTA, '')
        print(last_varna)
        similar = []
        if last_varna in self.antya_index:
            all_linga = list(VALUES_LANG['linga'])
            linga_options = all_linga if linga not in all_linga else [linga]

            for linga in linga_options:
                for word_idx in self.antya_index[last_varna][linga]:
                    word = self.get(word_idx)
                    similar.append((word['word'], word['baseindex'], linga))
        return similar

    def get(self, shabda_idx):
        shabda_idx = self.validate_index(shabda_idx)
        return self.index.get(shabda_idx, None)

    def get_forms(self, shabda_idx):
        shabda_idx = self.validate_index(shabda_idx)
        shabda_forms = self.index.get(shabda_idx, None)
        if shabda_forms is None:
            return None

        shabda_forms = self.get(shabda_idx)['forms']
        shabda_forms = [shabda_forms[3 * i: 3 * i + 3] for i in range(8)]

        return shabda_forms

    @staticmethod
    def validate_index(shabda_idx):
        shabda_idx = shabda_idx.translate(
            str.maketrans('०१२३४५६७८९।॥', '0123456789..')
        )
        match = re.match(r'([0-9]+)\.([0-9]+)', shabda_idx)
        if match:
            group_idx = match.group(1)
            inner_idx = match.group(2)
            if 0 < int(group_idx) < 80:
                return f'{group_idx.zfill(2)}.{inner_idx.zfill(3)}'
        return False
