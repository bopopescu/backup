#!/usr/bin/env python
import nltk

print "sentence"
String = raw_input()
print String
words = nltk.word_tokenize(String)

print words

word_r=nltk.pos_tag(words)
print word_r


