#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 15:09:14 2020

@author: Hrishikesh Terdalkar
"""

import os
import re
import cmd
import json
from collections import defaultdict

from indic_transliteration.sanscript import transliterate

###############################################################################

VERSION = '2020.11.03.1637'

###############################################################################

DHATU_LANG = {
    "baseindex": "क्रमाङ्कः",
    "dhatu": "धातुः",
    "aupadeshik": "औपदेशिक",
    "swara": "स्वरः",
    "gana": "गणः",
    "pada": "पदम्",
    "settva": "इडागमः",
    "karma": "कर्म",
    "artha": "अर्थः",
    "artha_english": "Meaning",
    "split_artha": "अर्थविच्छेदः",
    "split": "विच्छेदः",
    "english": "English",
    "tags": "Tags",
    "madhaveeya": "माधवीयः",
    "ksheeratarangini": "क्षीरतरङ्गिणी",
    "dhatupradeep": "धातुप्रदीपः",
    "nich": "णिच्",
    "san": "सन्",
    "yak": "यक्",
    "rupaani": "रूपाणि",
    "examples": "उदाहरणानि",
}

LAKARA_LANG = {
    "plat": "लट्लकारः (परस्मैपदम्)",
    "alat": "लट्लकारः (आत्मनेपदम्)",
    "plit": "लिट्लकारः (परस्मैपदम्)",
    "alit": "लिट्लकारः (आत्मनेपदम्)",
    "plut": "लुट्लकारः (परस्मैपदम्)",
    "alut": "लुट्लकारः (आत्मनेपदम्)",
    "plrut": "लृट्लकारः (परस्मैपदम्)",
    "alrut": "लृट्लकारः (आत्मनेपदम्)",
    "plot": "लोट्लकारः (परस्मैपदम्)",
    "alot": "लोट्लकारः (आत्मनेपदम्)",
    "plang": "लङ्लकारः (परस्मैपदम्)",
    "alang": "लङ्लकारः (आत्मनेपदम्)",
    "pvidhiling": "विधिलिङ्लकारः (परस्मैपदम्)",
    "avidhiling": "विधिलिङ्लकारः (आत्मनेपदम्)",
    "pashirling": "आशीर्लिङ्लकारः (परस्मैपदम्)",
    "aashirling": "आशीर्लिङ्लकारः (आत्मनेपदम्)",
    "plung": "लुङ्लकारः (परस्मैपदम्)",
    "alung": "लुङ्लकारः (आत्मनेपदम्)",
    "plrung": "लृङ्लकारः (परस्मैपदम्)",
    "alrung": "लृङ्लकारः (आत्मनेपदम्)",
}

###############################################################################

VALUES_LANG = {
    "gana": {
        "1": "भ्वादिः",
        "2": "अदादिः",
        "3": "जुहोत्यादिः",
        "4": "दिवादिः",
        "5": "स्वादिः",
        "6": "तुदादिः",
        "7": "रुधादिः",
        "8": "तनादिः",
        "9": "क्र्यादिः",
        "10": "चुरादिः"
    },
    "pada": {
        "P": "परस्मैपदम्",
        "A": "आत्मनेपदम्",
        "U": "उभयपदम्"
    },
    "settva": {
        "S": "सेट्",
        "A": "अनिट्",
        "V": "वेट्"
    },
    "karma": {
        "S": "सकर्मकः",
        "A": "अकर्मकः"
    }
}

###############################################################################

VACHANA = ['एकवचनम्', 'द्विवचनम्', 'बहुवचनम्']
PURUSHA = ['प्रथमपुरुषः', 'मध्यमपुरुषः', 'उत्तमपुरुषः']


###############################################################################


class DhatuPatha:
    SEARCH_KEYS = ['dhatu', 'aupadeshik', 'artha_english', 'english', 'artha']
    DISPLAY_KEYS = ['baseindex', 'dhatu', 'aupadeshik', 'english',
                    'gana', 'pada', 'artha', 'tags',
                    'karma', 'settva', 'artha_english']

    def __init__(self, dhatu_file, search_keys=None, display_keys=None):
        self.search_keys = search_keys or self.SEARCH_KEYS
        self.display_keys = display_keys or self.DISPLAY_KEYS

        with open(dhatu_file, encoding='utf-8') as f:
            self.index = json.load(f)

        self.forms = {}
        for dhatu_idx, dhatu in self.index.items():
            self.forms[dhatu_idx] = {}
            for lakara, lakara_forms in dhatu['rupaani'].items():
                if lakara_forms.strip():
                    _forms = defaultdict(list)
                    for pv_idx, pv_forms in enumerate(lakara_forms.split(';')):
                        for pv_form in pv_forms.split(','):
                            _forms[pv_form].append(pv_idx)
                    self.forms[dhatu_idx][lakara] = _forms
                else:
                    self.forms[dhatu_idx][lakara] = {}

    def search(self, search_str, **kwargs):
        """
        Search for a Dhatu by Base-Index, Dhatu, Meaning or Forms

        Parameters
        ----------
        search_str : str
            Search string
            Can be the index number, dhatu text (with or without swara),
            meaning (Sanskrit or English) or any valid form of that dhatu

        fuzzy_match : bool, (optional)
            If true, search within keys instead of searching for exact keys

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
                'dhatu': {
                     k: v for k, v in self.index[index].items()
                     if k in self.display_keys
                 },
                'type': 'baseindex',
                'desc': ''
            })
        for dhatu_idx, dhatu in self.index.items():
            display_dhatu = {
                k: v for k, v in dhatu.items()
                if k in self.display_keys
            }
            for key in self.search_keys:
                if kwargs.get('fuzzy_match') is True:
                    condition = search_str in dhatu[key]
                else:
                    condition = search_str == dhatu[key]
                if condition:
                    search_matches.append({
                        'dhatu': display_dhatu,
                        'type': key,
                        'desc': ''
                    })
            for lakara_key, lakara_name in LAKARA_LANG.items():
                if search_str in self.forms[dhatu_idx][lakara_key]:
                    indices = self.forms[dhatu_idx][lakara_key][search_str]
                    for idx in indices:
                        description = '{} {} {}'.format(
                            lakara_name,
                            PURUSHA[idx // 3],
                            VACHANA[idx % 3]
                        )
                        search_matches.append({
                            'dhatu': display_dhatu,
                            'type': 'rupaani',
                            'desc': description
                        })
        return search_matches

    def get(self, dhatu_idx):
        dhatu_idx = self.validate_index(dhatu_idx)
        return self.index.get(dhatu_idx, None)

    def get_forms(self, dhatu_idx):
        dhatu_idx = self.validate_index(dhatu_idx)
        dhatu_forms = self.index.get(dhatu_idx, None)
        if dhatu_forms is None:
            return None
        output = {}
        for lakara, forms in dhatu_forms['rupaani'].items():
            output[lakara] = [
                [[""], ["एक."], ["द्वि."], ["बहु."]],
                [["प्र."], [], [], []],
                [["म."], [], [], []],
                [["उ."], [], [], []]
            ] if forms.strip() else []
            if not forms.strip():
                continue
            for pv_idx, pv_forms in enumerate(forms.split(';')):
                purusha_idx = pv_idx // 3
                vachana_idx = pv_idx % 3
                output[lakara][purusha_idx + 1][vachana_idx + 1] = pv_forms.split(',')
        return output

    @staticmethod
    def validate_index(dhatu_idx):
        dhatu_idx = dhatu_idx.translate(
            str.maketrans('०१२३४५६७८९।॥', '0123456789..')
        )
        match = re.match(r'([0-9]+)\.([0-9]+)', dhatu_idx)
        if match:
            gana_idx = match.group(1)
            inner_idx = match.group(2)
            if 0 < int(gana_idx) < 11:
                return f'{gana_idx.zfill(2)}.{inner_idx.zfill(4)}'
        return False

###############################################################################


class BasicShell(cmd.Cmd):
    def emptyline(self):
        pass

    def do_shell(self, commad):
        """Execute shell commands"""
        os.system(commad)

    def do_exit(self, arg):
        """Exit the shell"""
        print("Bye")
        return True

    # do_EOF corresponds to Ctrl + D
    do_EOF = do_exit


###############################################################################

class DhatuPathaShell(BasicShell):
    intro = "DhaatuPaatha Search"
    desc = "Type any search string in the proprer input scheme. " \
           " (help or ? for list of options)"
    prompt = "(dhatu) "

    def __init__(self, dhatu_file):
        super(self.__class__, self).__init__()
        self.schemes = ['hk', 'velthuis', 'itrans', 'iast', 'slp1',
                        'wx', 'devanagari']
        self.input_scheme = 'devanagari'
        self.dhatupatha = DhatuPatha(dhatu_file)

    # ----------------------------------------------------------------------- #
    # Input Transliteration Scheme

    def complete_scheme(self, text, line, begidx, endidx):
        return [sch for sch in self.schemes if sch.startswith(text)]

    def do_scheme(self, scheme):
        """Change the input transliteration scheme"""
        if not scheme:
            print(f"Input scheme: {self.input_scheme}")
        else:
            if scheme not in self.schemes:
                print(f"Invalid scheme. (valid schemes are {self.schemes}")
            else:
                self.input_scheme = scheme
                print(f"Input scheme: {self.input_scheme}")

    # ----------------------------------------------------------------------- #

    def do_forms(self, line):
        """Get forms of a dhatu by providing dhatu index"""

        self.show_forms(self.dhatupatha.get(line),
                        self.dhatupatha.get_forms(line))

    # ----------------------------------------------------------------------- #

    def default(self, line):
        search_matches = []
        if self.input_scheme != 'devanagari':
            dn_line = transliterate(line, self.input_scheme, 'devanagari')
            search_matches.append((dn_line, self.dhatupatha.search(dn_line)))
        search_matches.append((line, self.dhatupatha.search(line)))

        for search_term, matches in search_matches:
            for match in matches:
                output = {
                    'Search': search_term,
                    'Match-Type': DHATU_LANG[match['type']],
                }
                for k, v in match['dhatu'].items():
                    output[DHATU_LANG[k]] = (
                        VALUES_LANG[k][v] if k in VALUES_LANG else v
                    )
                output['Description'] = match['desc']
                self.show_result(output)

    # ----------------------------------------------------------------------- #

    def cmdloop(self, intro=None):
        print(self.intro)
        print(self.desc)
        while True:
            try:
                super(self.__class__, self).cmdloop(intro="")
                break
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt")

    # ----------------------------------------------------------------------- #

    def do_version(self, text):
        print(VERSION)

    # ----------------------------------------------------------------------- #

    @staticmethod
    def show_result(result):
        output = [
            '+' + '-' * 80 + '+',
            json.dumps(result, ensure_ascii=False, indent=2),
            '+' + '-' * 80 + '+'
        ]
        output_str = '\n'.join(output)
        print(output_str)
        return output_str

    @staticmethod
    def show_forms(dhatu, dhatu_forms):
        output = [
            '+' + '-' * 80 + '+',
            (f"{dhatu['dhatu']} ({dhatu['aupadeshik']}), "
             f"{dhatu['artha']}, {dhatu['artha_english']}"),
            (f"{VALUES_LANG['gana'][dhatu['gana']]}, "
             f"{VALUES_LANG['pada'][dhatu['pada']]}, "
             f"{dhatu['tags']}"),
            '+' + '-' * 80 + '+'
        ]
        for lakara, forms in dhatu_forms.items():
            if forms:
                output.append('')
                output.append(LAKARA_LANG[lakara])
                output.append('+' + '-' * 30 + '+')
                output.extend([str(row) for row in forms])
        output.append('+' + '-' * 80 + '+',)
        output_str = '\n'.join(output)
        print(output_str)
        return output_str

###############################################################################


if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    Shell = DhatuPathaShell(os.path.join(dirname, 'dhatu.json'))
    Shell.cmdloop()
