#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python Interface for Inria Heritage Platform

Can query through web mirror and unix shell

UNIX Shell
- Heritage_Platform/ML/ contains the scripts
- export QUERY_STRING as shell variable
  (referred to as OPTION_STRING in this code alongwith the '&text=TEXT' part)
- execute various scripts, such as ./reader
- still produces HTML output that needs to be parsed

# Default input needs to be in the devanagari format
# HeritagePlatform.dn2vh() function will convert this to VH
"""

###############################################################################

import os
import re
import time
import random
import signal
import logging
import functools
import subprocess
import urllib.parse

from dataclasses import dataclass, field

import requests

from bs4 import BeautifulSoup

###############################################################################
# TODO: Do we need to use python-frozendict (PyPI)?


class frozendict(dict):
    def __hash__(self):
        return hash(frozenset(self.items()))


def freezeargs(func):
    """
    Transform mutable dictionnary arguments into immutable frozen ones

    Useful to be compatible with @cache. Should be added on top of @cache
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args = tuple([
            frozendict(arg) if isinstance(arg, dict) else arg
            for arg in args
        ])
        kwargs = {
            k: frozendict(v) if isinstance(v, dict) else v
            for k, v in kwargs.items()
        }
        return func(*args, **kwargs)
    for method in ['cache_info', 'cache_clear']:
        if callable(getattr(func, method, None)):
            setattr(wrapper, method, getattr(func, method))

    return wrapper

###############################################################################


def timeout_handler(signum, frame):
    raise TimeoutError("Time limit exceeded.")


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, timeout_handler)
    alarm = signal.alarm
else:
    def alarm(x): return x

###############################################################################

HERITAGE_LANG = {
    'gender': {
        'm': 'पुंलिङ्गम्',
        'f': 'स्त्रीलिङ्गम्',
        'n': 'नपुंसकलिङ्गम्',
        '*': 'त्रिलिङ्गम्'
    },
    'case': {
        'nom': 'प्रथमा',
        'acc': 'द्वितीया',
        'i': 'तृतीया',
        'dat': 'चतुर्थी',
        'abl': 'पञ्चमी',
        'g': 'षष्ठी',
        'loc': 'सप्तमी',
        'voc': 'सम्बोधनम्'
    },
    'number': {
        'sg': 'एकवचनम्',
        'du': 'द्विवचनम्',
        'pl': 'बहुवचनम्'
    }
}

# https://sanskrit.inria.fr/manual.html
HERITAGE_COLOURS = {
    'deep_sky': 'substantive/adjective forms',  # सुभन्त
    'red': 'finite verbal forms',  # तिङन्त
    'lawngreen': 'vocative',
    'mauve': 'indeclinable forms such as adverbs, conjunctions, prepositions',
    'light_blue': 'pronominal forms',
    'yellow': 'initial part of compounds',
    # Actually, complex compounds with n+1 components appear as a
    # sequence of n yellow segments denoting stems, followed by a blue
    # nominal inflected form.
    'cyan': 'exocentric compound',  # बहुव्रीहि समास
    # The cyan colour segment may not occur stand-alone,
    # it is mandatorily preceded by a yellow segment in order to form
    # an exocentric adjectival compound
    'lavender': 'first preposition of the compound',  # अव्ययीभाव
    'magenta': 'invariable form in the compound',  # अव्ययीभाव
    # There exists yet another variety of compound, the so-called avyayībhāva
    # "turned into undeclinable".
    # e.g. निर्मक्षिकम्
    # Here this input is analysed as a sequence of segments,
    # first the preposition nis, colored lavender, and then the stem makṣikā,
    # turned into an invariable form makṣikam, colored magenta.
    'grey': 'unrecognized',
    'orange': 'initial part of verbal compounds in periphrastic construction',
    # Verbal compounds exist, such as the periphrastic perfect construction,
    # used for secondary conjugations and nominative verbs. It builds a
    # special stem in -आम्, suffixed by a perfect form of one of the
    # auxiliaries कृ, अस् and भू.
    # e.g. First part of कथयाञ्चक्रे
    # The orange and red segments are mutually linked, thus selecting one
    # selects automatically the other.
    # Another periphrastic construction is the inchoative "cvi" verbal
    # compound. Its left part is a special substantival stem in ī or ū, and
    # its right part a finite verb form of one of the auxiliaries.
    # e.g. First part of मृदूभवति , खिलीभूतः etc.
    # Here, the right part is either red for verbal forms, e.g मृदूभवति
    # blue for participial forms, like कदर्थीकृतः
    # or mauve for absolutives and infinitives, like निमित्तीकृत्य
    'carmin': 'special infinitive form'
    # e.g. First part of वक्तुकामः
}


###############################################################################


@dataclass
class HeritageAnalysis:
    case: str = field(default=None)
    number: str = field(default=None)
    gender: str = field(default=None)
    tense: str = field(default=None)


@dataclass
class Token:
    pass

###############################################################################


class HeritageOutput:
    """
    Heritage Output Parser

    Parse output generated by various utilities from Heritage Platform
    """
    CLASSES = {
        'footer': ['enpied']
    }

    def __init__(self, html):
        self.logger = logging.getLogger(__name__)
        self.html = html
        self.soup = BeautifulSoup(html, 'html.parser')
        self.process()

    def process(self, html=None):
        """Process the html and extract basic information"""
        # Allow re-using of the class
        if html is not None:
            self.html = html
            self.soup = BeautifulSoup(html, 'html.parser')

        self.body = self.soup.find('body')
        self.footer = self.body.find('div', class_=self.CLASSES['footer'])

        # Extract Meta Information
        self.meta = {}
        for meta in self.soup.find_all('meta'):
            if meta.get('name', ''):
                self.meta[meta.get('name')] = meta.get('content', '')
            if meta.get('property', ''):
                self.meta[meta.get('property')] = meta.get('content', '')

        # Extract Title
        self.title = self.soup.find('title')
        self.inner_title = self.body.find('h1', class_='title')

        # Find Relevant Body Children
        self.blocks = self.body.find_all()

    def extract_analysis(self, meta=False):
        """
        Extract analysis from HTML

        Parameters
        ----------
        meta : bool
            If True, include meta information, i.e, parse options, classes
            The default is False.
        """
        if self.title.text != 'Sanskrit Reader Companion':
            self.logger.error("Invalid output page.")
            return None

        hr_blocks = self.html.split('<hr>')
        if len(hr_blocks) < 2:
            self.logger.error("No solutions found.")
            return None

        solutions = {}
        for block in hr_blocks[2:]:
            if 'Solution' not in block:
                break

            solution = {}

            soup = BeautifulSoup(block, 'html.parser')
            first_span = soup.find('span')
            solution_id = int(first_span.text.split()[1])

            solution['id'] = solution_id
            solution['words'] = []

            if meta:
                parser_url = first_span.find('a')['href']
                # TODO: Better parsing of options
                parser_options = dict([
                    e.split('=')
                    for e in re.split(r'&amp;|&|;', parser_url.split('?')[1])
                ])
                solution['parser_options'] = parser_options

            tables = soup.find_all('table')
            for table in tables:
                if table.find('table'):
                    word = {}
                    word['text'] = table.previous_sibling.get_text()
                else:
                    # Inner table contains analysis and it occurs after
                    # the original word
                    self.logger.debug(table.get_text())
                    analyses = self.parse_analysis(table)
                    self.logger.debug(analyses)
                    css_classes = table.get('class', [])
                    if meta:
                        word['classes'] = css_classes
                    word['category'] = [
                        HERITAGE_COLOURS.get(css_class.split('_back')[0], None)
                        for css_class in css_classes
                    ]
                    word_analyses = []
                    for analysis in analyses:
                        word_copy = word.copy()
                        word_copy.update(analysis)
                        word_analyses.append(word_copy)
                    solution['words'].append(word_analyses)

            solutions[solution_id] = solution
        return solutions

    def extract_parse(self):
        """Extract parse from HTML"""
        if self.title.text != 'Sanskrit Reader Assistant':
            self.logger.error("Invalid output page.")
            return None

        word_nodes = self.soup.find_all('table', class_='yellow_back')
        roles = []
        for word_node in word_nodes:
            word_text = word_node.get_text().strip()
            word_row = word_node.find_parent('tr')
            tables = word_row.find_all('table')
            # analysis_table = tables[1]
            # word_id_table = tables[2]
            semantic_table = tables[3]
            semantic_rows = semantic_table.find_all('tr')
            word_roles = [row.get_text() for row in semantic_rows]
            roles.append({'text': word_text, 'roles': word_roles})
        return roles

    def extract_declensions(self, headers=True):
        """Extract declensions from HTML"""
        if self.title.text != 'Sanskrit Grammarian Declension Engine':
            self.logger.error("Invalid output page.")
            return None
        table = self.soup.find('table', class_='inflexion')
        rows = table.find_all('tr')
        output = []
        for row in rows:
            cols = [col.get_text(' ').split() for col in row.find_all('th')]
            output.append(cols)
        output = output[:2] + output[3:] + [output[2]]
        if not headers:
            output = [row[1:] for row in output[1:]]
        return output

    def extract_conjugations(self, headers=True):
        """Extract conjugations from HTML"""
        if self.title.text != 'Sanskrit Grammarian Conjugation Engine':
            self.logger.error("Invalid output page.")
            return None
        tables = self.soup.find_all('table', class_='gris_cent')
        forms = {}
        for table in tables:
            header = table.find('span').get_text()
            forms[header] = {}
            inner_tables = table.find_all('table', class_='inflexion')

            for inner_table in inner_tables:
                rows = inner_table.find_all('tr')
                output = []
                for row in rows:
                    cols = [
                        col.get_text(' ').split() for col in row.find_all('th')
                    ]
                    output.append(cols)
                forms[header][output[0][0][0]] = output

        return forms

    def extract_sandhi(self):
        """Extract Sandhi from HTML"""
        if self.title.text != 'Sanskrit Sandhi Engine':
            self.logger.error("Invalid output page.")
            return None
        pattern = r'\s*([^\s\|]*)\s*\|\s*([^\s=]*)\s*=\s*([^\s]*)\s*'
        for span in self.body.find_all('span'):
            match = re.match(pattern, span.get_text(' '), flags=re.DOTALL)
            if match:
                return match.group(3)

    def extract_lexicon_entry(self, word_id):
        """Extract entry from a lexicon"""
        if 'Monier-Williams Sanskrit-English' not in self.title.text:
            self.logger.error("Invalid dictionary page.")
            return None
        marker = self.soup.find('a', attrs={'name': word_id})
        parent = marker.find_parent()
        # TODO: complete

    @staticmethod
    def parse_analysis(table):
        """
        Parse analysis of a single word
        Analysis Format is: [root]{analysis_1 | analysis_2 | ..}

        Parameters
        ----------
        table : bs4.element.Tag
            Valid `table` element

        Returns
        -------
        analysies : list
        """
        # pattern = r'\[([^\]]*)\]\{([^\}]*)\}'
        pattern = r'\[(.*?)\]\{([^\}]*)\}'
        rows = table.find_all('tr')
        analyses = []
        for row in rows:
            analysis = {}
            if row is None:
                analyses.append(analysis)
                continue

            link = row.find('a')
            if link is not None:
                link_parts = link['href'].split('/')[-1].split('#')
                file_name, word_id = link_parts[0], link_parts[1]
            else:
                file_name, word_id = None, None

            match = re.match(pattern, row.get_text().strip(), flags=re.DOTALL)
            analysis['lexicon'] = (file_name, word_id)
            analysis['root'] = match.group(1).split()[0].strip()
            analysis['analyses'] = [
                [abbrev.replace('.', '') for abbrev in an.split()]
                for an in match.group(2).split('|')
            ]
            analyses.append(analysis)
        return analyses

    def __repr__(self):
        return repr(self.soup)

###############################################################################


class HeritagePlatform:
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
        'parser': {
            'shell': 'parser',
            'web': 'sktparser.cgi'
        },
        'search': {
            'shell': 'indexer',
            'web': 'sktindex.cgi'
        },
        'search_easy': {
            'shell': 'indexerd',
            'web': 'sktsearch.cgi'
        },
        'declension': {
            'shell': 'declension',
            'web': 'sktdeclin.cgi'
        },
        'conjugation': {
            'shell': 'conjugation',
            'web': 'sktconjug.cgi'
        },
        'lemma': {
            'shell': 'lemmatizer',
            'web': 'sktlemmatizer.cgi'
        },
        'sandhi': {
            'shell': 'sandhier',
            'web': 'sktsandhier.cgi'
        },
        'user': {
            'shell': 'user_aid',
            'web': 'sktuser.cgi'
        },
        'interface': {
            'shell': 'interface',
            'web': 'sktgraph.cgi'
        },
        'dictionary': {
            'shell': '../MW/',
            'web': '../../MW/'
        }
    }

    OPTIONS = {
        'lex': {
            'description': 'Lexicon',
            'values': {
                'MW': 'Monier-Williams Dictionary (English)',
                'SH': 'Sanskrit Heritage Dictionary (French)'
            },
            'default': 'MW'
        },
        'font': {
            'description': 'Font for Sanskrit output',
            'values': {
                'deva': 'Devanagari',
                'roma': 'Roman (IAST)'
            },
            'default': 'deva'
        },
        't': {
            'description': 'Internal Transliteration Scheme',
            'values': {
                'VH': 'Velthuis'
            },
            'default': 'VH'
        }
    }

    METHODS = ['shell', 'web']

    def __init__(self, base_dir='', base_url=None, method='shell', **kwargs):
        """
        Initialize Heritage Class

        Parameters
        ----------
        base_dir : str
            Path to the Heritage_Platform repository.
            The directory should contain 'ML' sub-directory,
            which further contains the scripts
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
        self.logger = logging.getLogger(__name__)
        self.base_url = self.INRIA_URL if base_url is None else base_url
        self.base_dir = base_dir
        self.scripts_dir = os.path.join(self.base_dir, 'ML')

        self.method = None
        self.set_method(method)

        if not self.valid_installation():
            self.logger.warning("Heritage Platform installation not found.")
            self.base_dir = ''
            self.scripts_dir = ''
            self.set_method('web')

        self.options = {}
        for option in self.OPTIONS:
            self.options[option] = self.OPTIONS[option]['default']

    ###########################################################################
    # Utilities (Actions)

    def get_analysis(self, input_text,
                     sentence=True, unsandhied=False, meta=False):
        """
        Utility to obtain morphological analyses using Reader Companion

        Parameters
        ----------

        Returns
        -------
        result : list
            List of valid morphological analyses
        """
        opt_st = 't' if sentence else 'f'
        opt_us = 't' if unsandhied else 'f'

        options = {
            'lex': self.get_lexicon(),
            'cache': 't',  # Use Cache (t)rue, (f)alse
            'st': opt_st,  # Sentence (t)rue, Word (f)alse
            'us': opt_us,  # Unsandhied (t)rue, (f)alse
                           # if 'us' is 'f', "ca eva" is parsed as "ca_eva",
                           # "tathā eva" as "tathā_eva" etc.
            'cp': 't',     # Full Parser Strength (t)rue, (f)alse
            't': self.get_option('t'),
            'mode': 'p',   # Parse Mode (p)arsing, (t)agging
                           # Tagging does not prune any solutions
            'font': self.get_font(),
                           # Output Display Font (deva)nagari (roma)n
            'topic': '',
            'corpmode': '',
            'corpdir': '',
            'sentno': '',
            'text': self.prepare_input(input_text)
        }
        result = self.get_result('reader', options)
        if result is None:
            return None

        output = HeritageOutput(result)
        # return output
        return output.extract_analysis(meta=meta)

    # ----------------------------------------------------------------------- #

    def get_parse(self, input_text, solution_id=None, sentence=True,
                  unsandhied=False):
        """
        Utility to obtain morphological analyses using Reader Companion

        Returns
        -------
        result : list
            List of valid morphological analyses
        """

        solutions = self.get_analysis(
            input_text, sentence=sentence, unsandhied=unsandhied, meta=True
        )

        # If solution ID not provided, use the first solution
        if solution_id is None:
            if not solutions:
                return None  # TODO: Change this to something ?

        solution_id = next(iter(solutions))

        # No need to manually give options again, since it does it for us
        # Internally parser is a re-run of reader until a specific solution
        # Remove following block in later versions

        # opt_st = 't' if sentence else 'f'
        # opt_us = 't' if unsandhied else 'f'

        # options = {
        #     'lex': self.get_lexicon(),
        #     'cache': 't',  # Use Cache (t)rue, (f)alse
        #     'st': opt_st,  # Sentence (t)rue, Word (f)alse
        #     'us': opt_us,  # Unsandhied (t)rue, (f)alse
        #                    # if 'us' is 'f', "ca eva" is parsed as "ca_eva",
        #                    # "tathā eva" as "tathā_eva" etc.
        #     'cp': 't',     # Full Parser Strength (t)rue, (f)alse
        #     't': self.get_option('t'),
        #     'mode': 'p',   # Parse Mode (p)arse, (g)raph, (s)ummary
        #     'font': self.get_font(),
        #                    # Output Display Font (deva)nagari (roma)n
        #     'topic': '',
        #     'n': solution_id,
        #     'abs': 'f',     # TODO: Find out what this does
        #     'text': self.prepare_input(input_text)
        # }

        solution = solutions[solution_id]
        options = solution['parser_options']
        result = self.get_result('parser', options)
        output = HeritageOutput(result)
        roles = output.extract_parse()
        solution['roles'] = roles

        return solution

    # ----------------------------------------------------------------------- #

    def sandhi(self, word_1, word_2, mode='internal'):
        """
        Join two words by forming a Sandhi

        Parameters
        ----------
        word_1 : str
            The first (left) word in the Sandhi
        word_2 : str
            The second (right) word in the Sandhi
        mode : str, optional
            Indicates whether the words join to form a single word or not
            Possible values are,
            * internal
            * external
            The default is 'internal'.

        Returns
        -------
        sandhi : str
            String obtained by forming the Sandhi
        """
        if mode not in ['internal', 'external']:
            self.logger.warning(f"Invalid mode: '{mode}'")

        options = {
            'lex': self.get_lexicon(),
            'l': self.prepare_input(word_1),
            'r': self.prepare_input(word_2),
            't': self.get_option('t'),
            'k': mode,
            'font': self.get_font()
        }
        result = self.get_result('sandhi', options)
        output = HeritageOutput(result)

        return output.extract_sandhi()

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
            't': self.get_option('t'),
            'q': self.prepare_input(word),
            'c': category,
            'font': self.get_font()
        }
        result = self.get_result('lemma', options)
        output = HeritageOutput(result)

        # TODO: Output Parsing
        return output

    # ----------------------------------------------------------------------- #

    def get_declensions(self, word, gender, headers=True, lexicon=None):
        options = {
            'lex': self.get_lexicon(),
            't': self.get_option('t'),
            'q': self.prepare_input(word),
            'g': self.identify_gender(gender),
            'font': self.get_font()
        }
        result = self.get_result('declension', options)
        output = HeritageOutput(result)

        return output.extract_declensions(headers=headers)

    # ----------------------------------------------------------------------- #

    def get_conjugations(self, word, gana, lexicon=None):
        options = {
            'lex': self.get_lexicon(),
            't': self.get_option('t'),
            'q': self.prepare_input(word),
            'c': gana,
            'font': self.get_font()
        }
        result = self.get_result('conjugation', options)
        output = HeritageOutput(result)

        # TODO: Output Parsing
        return output

    # ----------------------------------------------------------------------- #

    def search_lexicon(self, word, lexicon=None):
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
            'lex': self.get_lexicon(),
            't': self.get_option('t'),
            'q': self.prepare_input(word),
            'font': self.get_font()
        }
        result = self.get_result('search', options)
        output = HeritageOutput(result)

        # TODO: Output Parsing
        # TODO: Currently not using the lexicon keyword argument
        # Is there any use for that argument? For this function?
        return output

    ###########################################################################

    @functools.lru_cache(maxsize=None)
    def get_lexicon_entry(self, file_name, word_id):
        if self.method == 'shell':
            path = self.get_path('dictionary')
            file_path = os.path.join(path, file_name)
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
        elif self.method == 'web':
            url = self.get_url('dictionary')
            query_url = f'{url}{file_name}#{word_id}'
            content = self.__get(query_url)
        else:
            self.logger.error(f"Invalid method: '{self.method}'.")
            return

        output = HeritageOutput(content)
        return output.extract_lexicon_entry()

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
            HeritagePlatform.get_url() can be used to generate supported URLs
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

        query_string = self.build_query_string(options)
        query_url = f'{url}?{query_string}'
        return self.__get(query_url, attempts=attempts)

    @functools.lru_cache(maxsize=None)
    def __get(self, query_url, attempts=3):
        """
        Query web with exponential-backoff

        Parameters
        ----------
        query_url : str
            URL to query
        attempts : int, optional
            Number of attempts for the exponential backoff
            The default is 3.

        Returns
        -------
        str
            Result (HTML) obtained
        """
        # query with exponential-backoff
        r = requests.get(query_url)
        if r.status_code != 200:
            for n in range(attempts):
                if n == 0:
                    self.logger.warning(f"URL: {query_url}")

                self.logger.warning(f"Status Code: {r.status_code} (n = {n})")

                fn = n
                backoff = (2 ** fn) + random.random()
                time.sleep(backoff)
                r = requests.get(query_url)

                if r.status_code == 200:
                    self.logger.info(f"Resolved! (n = {n})")
                    break
            else:
                self.logger.warning(
                    f"Failed on '{query_url}' after {n} attempts."
                )
        return r.text

    # ----------------------------------------------------------------------- #

    def get_result_from_shell(self, path, options, timeout=30):
        """
        Get results from the Heritage Platform's local installation via shell

        Parameters
        ----------
        path : str
            Path to the executable script
            HeritagePlatform.get_path() can be used to generate supported paths
        options : dict
            Valid options for the script
        timeout : int, optional
            Timeout in seconds, after which the function will abort.
            The default is 30.

        Returns
        -------
        result : str
            Result (HTML) obtained
        """
        query_string = self.build_query_string(options)
        environment = frozendict({'QUERY_STRING': query_string})
        return self.__run(path, environment, timeout=timeout)

    @functools.lru_cache(maxsize=None)
    def __run(self, path, environment, timeout=30):
        """
        Get results from shell through a subprocess call

        Parameters
        ----------
        path : str
            Path to the executable script
        environment : dict
            Environment variables to set
        timeout : int, optional
            Timeout in seconds, after which the function will abort.
            The default is 30.

        Returns
        -------
        result : str
            Result (HTML) obtained
        """
        alarm(timeout)
        try:
            result_header = 'Content-Type: text/html\n\n'
            result = subprocess.check_output(
                path, env=environment
            ).decode('utf-8')
            result = result[len(result_header):]
        except TimeoutError:
            self.logger.error("TimeoutError")
            return None
        alarm(0)
        return result

    # ----------------------------------------------------------------------- #

    def get_result(self, action, options, *args, **kwargs):
        """
        High-level function to obtain result for various actions

        Avoids the hassle of generating the URL or PATH.
        Utilizes the HeritagePlatform.method attribute to determine
        whether to fetch through shell or web.

        Parameters
        ----------
        action : str
            Action value corresponding to the utility to be used.
            Refer to HeritagePlatform.ACTIONS
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
        self.logger.error(f"Invalid method: '{self.method}'.")

    ###########################################################################

    def get_method(self):
        """Get the current method"""
        return self.method

    def set_method(self, method):
        """
        Set method for fetching the output

        Valid methods are listed in HeritagePlatform.METHODS
        """
        if method.lower() in self.METHODS:
            self.method = method.lower()
            return True
        self.logger.warning(f"Invalid method: '{method}'")
        if self.method is None:
            self.method = 'shell'
        return False

    # ----------------------------------------------------------------------- #

    def get_option(self, opt_name):
        """Get the value of global options"""
        if opt_name not in self.OPTIONS:
            self.logger.warning("Invalid option: '{opt_name}'")
            return None
        return self.options.get(opt_name, None)

    def set_option(self, opt_name, opt_value):
        """Set global options

        Any of these options, if expected by a particular utility from the
        Heritage Platform, will be directly used in the QUERY_STRING while
        fetching the output from that utility

        class variable OPTIONS stores the default values for options

        Each option contains,
        - a 'description' of the option
        - 'values' it can take (and descriptions of those values)
        - 'default' value

        """

        opt_name = opt_name.lower()
        if opt_name not in self.OPTIONS:
            self.logger.warning("Invalid option: '{opt_name}'")
            return False

        if opt_value in self.OPTIONS[opt_name]['values']:
            self.options[opt_name] = opt_value
            return True

        self.logger.warning(
            f"Invalid value for option '{opt_name}': '{opt_value}'"
        )
        return False

    # ----------------------------------------------------------------------- #

    def get_font(self):
        """Get current font for Sanskrit Output"""
        return self.get_option('font')

    def set_font(self, font):
        """Set font for Sanskrit output"""
        return self.set_option('font', font.lower())

    # ----------------------------------------------------------------------- #

    def get_lexicon(self):
        """Get current lexicon"""
        return self.get_option('lex')

    def set_lexicon(self, lexicon):
        """Set lexicon"""
        return self.set_option('lex', lexicon.upper())

    ###########################################################################
    # URL or Path Builders

    def get_url(self, action):
        """URL Builder"""
        return urllib.parse.urljoin(self.base_url, self.ACTIONS[action]['web'])

    def get_path(self, action):
        """Path Builder"""
        return os.path.join(self.scripts_dir, self.ACTIONS[action]['shell'])

    ###########################################################################

    def valid_installation(self):
        """Check if the Heritage Platform installation exists"""
        # TODO: A better check may be checking for the required executables
        # * If the file exists
        # * If the file is executable
        return os.path.isdir(self.scripts_dir)

    ###########################################################################

    def __repr__(self):
        params = {
            'repository': self.base_dir,
            'url': self.base_url,
            'method': self.method,
        }
        repr_params = ', '.join([f'{k}="{v}"' for k, v in params.items()])
        return f'{self.__class__.__name__}({repr_params})'

    ###########################################################################

    def prepare_input(self, input_text):
        """
        Prepare Input
            * Convert Devanagari to Velthuis
            * Join words by '+' instead of by whitespaces
        """
        return '+'.join(self.dn2vh(input_text).split())

    @staticmethod
    def build_query_string(options):
        """Build QUERY_STRING"""
        return '&'.join([f'{k}={v}' for k, v in options.items()])

    @staticmethod
    def identify_gender(gender):
        genders = {
            'Mas': ['पु', 'm'],
            'Fem': ['स्त्री', 'f'],
            'Neu': ['नपु', 'n'],
            'Any': ['*', 'त्रि', 'a']
        }
        for gender_key, gender_list in genders.items():
            for g in gender_list:
                if gender.lower().startswith(g):
                    return gender_key

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
    home_dir = os.path.expanduser('~')
    heritage_dir = os.path.join(home_dir, 'git', 'heritage',
                                'Heritage_Platform')
    SH = HeritagePlatform(heritage_dir)
