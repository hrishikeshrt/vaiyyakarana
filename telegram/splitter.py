#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 04 11:33:18 2021

@author: Hrishikesh Terdalkar

Sandhi and Samaasa Splitter by Oliver Hellwig
"""

import os
import sys
import tempfile
import functools

from indic_transliteration.sanscript import transliterate

from config import hellwig_splitter_dir

###############################################################################
# Sandhi Related

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()

sys.path.insert(0, hellwig_splitter_dir)

import configuration, helper_functions, data_loader

###############################################################################

MAX_CACHE = 1024

###############################################################################


class Splitter:
    def __init__(self, base_dir, tmp_dir=None):
        self.base_dir = base_dir
        self.tmp_dir = tempfile.gettempdir() if tmp_dir is None else tmp_dir
        self.sandhi_config = configuration.config
        self.sandhi_data = data_loader.DataLoader(
            os.path.join(self.base_dir, '..', 'data', 'input'),
            self.sandhi_config,
            load_data_into_ram=True,
            load_data=False
        )

        self.graph_pred = tf.Graph()
        with self.graph_pred.as_default():
            self.sess = tf.Session(graph=self.graph_pred)
            model_dir = model_dir = os.path.normpath(
                os.path.join(self.base_dir, self.sandhi_config['model_directory'])
            )
            tf.saved_model.loader.load(
                self.sess,
                [tf.saved_model.tag_constants.SERVING],
                model_dir
            )
            print('OK')

        self.x_ph = self.graph_pred.get_tensor_by_name('inputs:0')
        self.split_cnts_ph = self.graph_pred.get_tensor_by_name('split_cnts:0')
        self.dropout_ph = self.graph_pred.get_tensor_by_name('dropout_keep_prob:0')
        self.seqlen_ph = self.graph_pred.get_tensor_by_name('seqlens:0')
        self.predictions_ph = self.graph_pred.get_tensor_by_name('predictions:0')

    @functools.lru_cache(MAX_CACHE)
    def split(self, input_text):
        path_in = os.path.join(self.tmp_dir, "input_sandhied")
        path_out = os.path.join(self.tmp_dir, "outinput_unsandhied")
        with open(path_in, "w") as f:
            f.write(transliterate(input_text, 'devanagari', 'iast'))
        helper_functions.analyze_text(
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
        with open(path_out) as f:
            output_text = transliterate(f.read(), 'iast', 'devanagari')
        return output_text

###############################################################################
