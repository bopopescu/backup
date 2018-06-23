## coding=utf-8
from textblob import TextBlob


text = u"""
I am honored to be with you today at your commencement from one of the finest universities in the world.
I never graduated from college.
Truth be told, this is the closest I've ever gotten to a college graduation.
Today I want to tell you three stories from my life.
That's it. No big deal. Just three stories.
"""

blob = TextBlob(text)


# wordのリスト
print blob.words
# => WordList([u'I', u'am', u'honored', u'to', u'be', u'with', u'you', u'today', u'at', u'your', u'commencement', u'from', u'one', u'of', u'the', u'finest', u'universities', u'in', u'the', u'world', u'I', u'never', u'graduated', u'from', u'college', u'Truth', u'be', u'told', u'this', u'is', u'the', u'closest', u'I', u've', u'ever', u'gotten', u'to', u'a', u'college', u'graduation', u'Today', u'I', u'want', u'to', u'tell', u'you', u'three', u'stories', u'from', u'my', u'life', u'That', u's', u'it', u'No', u'big', u'deal', u'Just', u'three', u'stories'])

# sentenceのリスト
print blob.sentences
# => [Sentence('I am honored to be with you today at your commenc...sities in the world.'), Sentence('I never graduated from college.'), Sentence('Truth be told, this is the closest I've ever gotten to a college graduation.'), Sentence('Today I want to tell you three stories from my life.'), Sentence('That's it.'), Sentence('No big deal.'), Sentence('Just three stories.')]

# 出現回数
print blob.words.count("three")
# => 2

# 言語を検出
print blob.detect_language()
# => en

# 翻訳
translated = blob.translate(to="ja")
print translated.raw
# => 私は、世界でも有数の大学の一つからあなたの開始時、あなたと今日できることを光栄に思います。
# => 私は大学を卒業することはありません。
# => 真実を言えば、これは私が今までで大学卒業に近い経験ということになります。
# => 今日、私はあなたに私の人生から3話をお伝えしたいと思います。
# => それはそれだ。大したことはありません。わずか3話。


# htmlの除去
html = "<b>HAML</b> Ain't Markup <a href='/languages'>Language</a>"
clean = TextBlob(html, clean_html=True)
print clean
# => HAML Ain't Markup Language
