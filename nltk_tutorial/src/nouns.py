from textblob import TextBlob
from textblob.np_extractors import ConllExtractor

text = raw_input("Please fill out the sentence\n")
extractor = ConllExtractor()
blob = TextBlob(text, np_extractor=extractor)
blob2 = blob.noun_phrases
print blob2
