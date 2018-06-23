#!/usr/bin/env python
#coding:UTF-8
import nltk

String = raw_input("please put on the sentence\n")
print String
words = nltk.word_tokenize(String)

print words
word_r=nltk.pos_tag(words)
length = len(words)
print word_r

if word_r[0][1] == 'VB' or word_r[0][1] == 'VBP':
    print "This is commad"

elif word_r[0][0] == 'Please' and word_r[0][1] == 'NNP':
    print "This is also command"
elif word_r[0][1] == 'WDT' or word_r[length][0] == '?':
    print "This is question"

else :
    score = 0
    for i in range(len(words)-1):
        sentence = word_r[i][1]
        if sentence == 'PRP' or sentence == 'PRP$' or sentence == 'NN' or sentence == 'NNS' or sentence == 'NNP' or sentence == 'NNPS':
            prescore = score + 3
        elif sentence == 'JJS' or sentence == 'JJR' or sentence == 'JJ':
            prescore = score + 2
        else:
            prescore = score

newscore = prescore
print newscore
if newscore <= 0:
    print "第一文型"
elif newscore == 3:
    print "第二文型"
elif newscore == 2:
    print "第三文型"
elif newscore == 4:
    print "第四文型"
elif newscore == 5:
    print "第五文型"
