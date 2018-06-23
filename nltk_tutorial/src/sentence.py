#!/usr/bin/env python
#coding:UTF-8

import spacy
import sys
import nltk
from textblob import TextBlob
from textblob.taggers import NLTKTagger

nlp = spacy.load('en_core_web_sm')
text = raw_input("please write down sentences\n").decode('utf8')
doc = nlp(text)
words = nltk.word_tokenize(text)
word_pos = nltk.pos_tag(words)
length = len(words)
print word_pos

if word_pos[0][1] == 'VB' or word_pos[0][1] == 'VBP' or word_pos[0][1] == 'IN':
    print "This is commad"
elif word_pos[0][0] == 'Please' and word_pos[0][1] == 'NNP':
    print "This is also command"
elif word_pos[0][1] == 'WP': #or word_pos[length][0] == '?':
    print "This is question"

else:
    #score = 0
    count_o = 0
    count_c = 0
    realscore = 0
    for token in doc:
        print "---"
        print token.dep_
        print "---"
        if token.dep_ == "appos":
            print "mmm"
            realscore = realscore + 2
            count_c = count_c + 1
        elif token.dep_ == "dobj" or token.dep_ == "dative" or token.dep_ == "compound":
            realscore = realscore + 3
            count_o = count_o + 1
            print "aaa"
        elif token.dep_ == "atter" or token.dep_ == "attr" or token.dep_ == "oprd" or token.dep_ == "pobj":
            realscore = realscore + 2
            count_c = count_c + 1
            print "bbb"
        else:
            print "ccc"

    print realscore
    if realscore <= 0:
        print "第一文型"
    elif realscore == 2:
        print "第二文型"
    elif realscore == 3:
        print "第三文型"
    elif realscore == 6:
        print "第四文型"
    elif realscore == 5:
        print "第五文型"
    else:
        print "目的語の個数："
        print count_o
        print "\n補語の個数："
        print count_c
