import spacy
import sys

nlp = spacy.load('en_core_web_sm')
text = raw_input("please put on the sentence\n").decode('utf8')

doc = nlp(text)

for token in doc:
    print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
          token.shape_, token.is_alpha, token.is_stop)
