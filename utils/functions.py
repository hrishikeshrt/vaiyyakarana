#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 16:54:18 2023

@author: Hrishikesh Terdalkar
"""

###############################################################################


def fold(content, width=128):
    '''
    Fold content such that each line is no longer than 'width'
        - breaks only at complete words
        - if a word in the content exceeds `width`
            - added as a separate line
            - a warning is shown

    similar to linux command "fold -w `width` -s"
    except in the cases where there are spaces on the line boundaries
    '''
    lines = content.split('\n')
    folds = []
    for line in lines:
        if len(line) > width:
            words = line.split()
            linesplits = []
            curr_len = 0
            curr_line = ''
            idx = 0
            while idx < len(words):
                is_nonempty = int(bool(curr_line))
                new_len = curr_len + len(words[idx]) + is_nonempty
                if new_len <= width:
                    curr_line += ' ' * is_nonempty + words[idx]
                    curr_len = new_len
                    idx += 1
                else:
                    curr_len = 0
                    if curr_line:
                        linesplits.append(curr_line.strip())
                        curr_line = ''
                    if len(words[idx]) > width:
                        print(f"Warning: '{words[idx]}' longer than {width}.")
                        linesplits.append(words[idx])
                        idx += 1
                        continue
            linesplits.append(curr_line.strip())
            folds.append('\n'.join(linesplits))
        else:
            folds.append(line)
    output = '\n'.join(folds)
    return output


###############################################################################
