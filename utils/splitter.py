#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 04 11:33:18 2021

@author: Hrishikesh Terdalkar

Sandhi and Samaasa Splitter

In-memory class around Sanskrit Sandhi and Compound Splitter by Oliver Hellwig
https://github.com/OliverHellwig/sanskrit/tree/master/papers/2018emnlp

* git clone https://github.com/OliverHellwig/sanskrit/
* base_dir := GIT_CLONE_DIR / papers/2018emnlp/code
"""

import os
import sys
import logging
import tempfile
import functools
import contextlib

from indic_transliteration import sanscript

###############################################################################
# Sandhi Related

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()

###############################################################################

GIT_DIR = os.path.join(os.path.expanduser('~'), 'git', 'oliverhellwig')
INSTALL_DIR = os.path.join(GIT_DIR, 'papers', '2018emnlp', 'code')

###############################################################################

MAX_CACHE = 1024

###############################################################################


class Splitter:
    def __init__(self, base_dir, tmp_dir=None):
        self.base_dir = base_dir
        self.tmp_dir = tempfile.gettempdir() if tmp_dir is None else tmp_dir
        self.logger = logging.getLogger(self.__class__.__name__)

        # Import Helper Modules from Base Directory
        sys.path.insert(0, self.base_dir)
        import configuration, helper_functions, data_loader

        # Configuration
        self.sandhi_config = configuration.config
        self.sandhi_data = data_loader.DataLoader(
            os.path.join(self.base_dir, '..', 'data', 'input'),
            self.sandhi_config,
            load_data_into_ram=True,
            load_data=False
        )
        self.analyze_text = helper_functions.analyze_text

        self.graph = tf.Graph()
        with self.graph.as_default():
            self.sess = tf.Session(graph=self.graph)
            model_dir = model_dir = os.path.normpath(
                os.path.join(
                    self.base_dir,
                    self.sandhi_config['model_directory']
                )
            )
            tf.saved_model.loader.load(
                self.sess,
                [tf.saved_model.tag_constants.SERVING],
                model_dir
            )
            print('OK')

        self.x_ph = self.graph.get_tensor_by_name('inputs:0')
        self.split_cnts_ph = self.graph.get_tensor_by_name('split_cnts:0')
        self.dropout_ph = self.graph.get_tensor_by_name('dropout_keep_prob:0')
        self.seqlen_ph = self.graph.get_tensor_by_name('seqlens:0')
        self.predictions_ph = self.graph.get_tensor_by_name('predictions:0')

    def _perform_split(self, path_in, path_out):
        """Perform Sandhi-Samaasa split on IAST input file

        Parameters
        ----------
        path_in : str
            Path to input file
        path_out : str
            Path to output file
        """
        self.analyze_text(
            path_in,
            path_out,
            self.predictions_ph,
            self.x_ph,
            self.split_cnts_ph,
            self.seqlen_ph,
            self.dropout_ph,
            self.sandhi_data,
            self.sess,
            verbose=False
        )

    @functools.lru_cache(MAX_CACHE)
    def split(self, input_text, input_scheme=sanscript.DEVANAGARI):
        """Split Sandhi and Samaasa from the Sanskrit text.

        Parameters
        ----------
        input_text : str
            Sanskrit text in a valid transliteration scheme.
        input_scheme : str, optional
            Transliteration scheme used by the input.
            Recommended to use canonical variable defined by the sanscript
            module, e.g. sanscript.DEVANAGARI, sanscript.IAST, ...
            The default is sanscript.DEVANAGARI

        Returns
        -------
        str
            Text with Sandhi-Samaasa split markers
        """
        path_in = os.path.join(self.tmp_dir, "input_sandhied")
        path_out = os.path.join(self.tmp_dir, "output_unsandhied")

        with contextlib.suppress(FileNotFoundError):
            os.remove(path_out)

        with open(path_in, "w") as f:
            if input_scheme != sanscript.IAST:
                input_text = sanscript.transliterate(
                    input_text, input_scheme, sanscript.IAST
                )
            f.write(input_text)

        self._perform_split(path_in, path_out)

        with open(path_out) as f:
            output_text = f.read()
            if input_scheme != sanscript.IAST:
                output_text = sanscript.transliterate(
                    output_text, sanscript.IAST, input_scheme
                )

        return output_text

    def split_file(self, path_in, path_out, input_scheme=sanscript.DEVANAGARI):
        """Split Sandhi and Samaasa from a file

        Parameters
        ----------
        path_in : str
            Path to the input file
        path_out : str
            Path to the output file
        input_scheme : str, optional
            Transliteration scheme used by the input.
            Recommended to use canonical variable defined by the sanscript
            module, e.g. sanscript.DEVANAGARI, sanscript.IAST, ...
            The default is sanscript.DEVANAGARI
        """
        with open(path_in) as f:
            input_text = f.read()
        output_text = self.split(input_text, input_scheme=input_scheme)
        with open(path_out, "w") as f:
            f.write(output_text)

###############################################################################
