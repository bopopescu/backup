from textblob import TextBlob
import nltk

text = raw_input("Please write down the sentence\n")
testimonial = TextBlob(text)
tes=testimonial.sentiment
print tes
