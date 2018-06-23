 # coding=utf-8
from textblob import TextBlob
from textblob.taggers import NLTKTagger
import nltk
import identify_part_of_speech

text = raw_input("please put on the sentence\n")

blob = TextBlob(text)
String = nltk.word_tokenize(text)
String_pos=nltk.pos_tag(String)
blob_tag=blob.tags
# wordのリスト
print blob.words
print String
# => WordList([u'I', u'am', u'honored', u'to', u'be', u'with', u'you', u'today', u'at', u'your', u'commencement', u'from', u'one', u'of', u'the', u'finest', u'universities', u'in', u'the', u'world', u'I', u'never', u'graduated', u'from', u'college', u'Truth', u'be', u'told', u'this', u'is', u'the', u'closest', u'I', u've', u'ever', u'gotten', u'to', u'a', u'college', u'graduation', u'Today', u'I', u'want', u'to', u'tell', u'you', u'three', u'stories', u'from', u'my', u'life', u'That', u's', u'it', u'No', u'big', u'deal', u'Just', u'three', u'stories'])

print blob_tag
print String_pos
translated = blob.translate(to="ja")
print translated.raw
