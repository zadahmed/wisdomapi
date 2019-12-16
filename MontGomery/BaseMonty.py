# Base class for Monty start, sumamrisation and cleanup

# Imports
import os
import time
import re
import nltk
import pandas as pd
import string
import numpy as np
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from nltk.corpus import stopwords 
from nltk.stem.wordnet import WordNetLemmatizer
from flask import jsonify

# global variables
stop = set(stopwords.words("english"))
exclude = set(string.punctuation) 
lemma = WordNetLemmatizer()


def clean(doc):
    stop_free = " ".join([i for i in doc.lower().split() if i not in stop])
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
    normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
    return normalized
def frequency_processor(corpus):
    article_text = [''.join(str(i) + " " for i in corpus)]
    formatted_article_text = article_text[0].lower()
    formatted_article_text = re.sub(r'[^\w\s]',' ',formatted_article_text)
    formatted_article_text = " ".join(x for x in formatted_article_text.split() if x not in stop)
    sentence_list = nltk.sent_tokenize(article_text[0])
    frequency = pd.value_counts(formatted_article_text.split(" ")).reset_index()
    frequency.columns = ["words", "frequency"]
    frequency = frequency[frequency["words"] != "-"]
    frequency = frequency[frequency["words"] != "_"]
    frequency = frequency[frequency["words"] != '–']
    frequency = frequency[frequency["words"] != '—']
    maximum_frequency = max(frequency["frequency"].values)
    frequency["weighted_frequency"] = frequency["frequency"]/maximum_frequency
    for i, word in enumerate(frequency["words"]):
        frequency.loc[i, 'idf'] = np.log(len(sentence_list)/len([x for x in sentence_list if word in x.lower()]))
    for i, word in enumerate(frequency["words"]):
        try:
            frequency.loc[i, 'lemmatized word'] = lemma.lemmatize(word)
        except:
            frequency.loc[i, 'lemmatized word'] = " "
    frequency['tf_idf'] = frequency['frequency'] * frequency['idf']
    return frequency


class BaseMonty():
    

    def factualSummary(self, search_me, Z, f_what_summary):
        f_what_final_summary = []
        for i in f_what_summary:
            dummy = i.split(".")
            for j in dummy:
                if j.find(":", 0, 1) != -1 and j.find("-", 1, 3) != -1:
                    pass
                else:
                    if len(j) > 1:
                        f_what_final_summary.append(j+".")
        parser = PlaintextParser.from_string(' '.join(str(i) for i in f_what_final_summary), Tokenizer("english"))
        summarizer = TextRankSummarizer()
        f_summary = summarizer(parser.document, Z)
        dummy = []
        for i in f_summary:
            if i not in dummy:
                dummy.append(i)
            else:
                pass
        f_summary = dummy
        # Factual summary
        print("\n============================== What is [{}] \n".format(search_me))
        f_summary = [''.join(str(i) + " " for i in f_summary)]
        if "may refer to:" in f_summary[0]:
            print("----> Ambiguous search term, try another term...")
        else:
            print(f_summary[0])
        return jsonify(search=search_me,summary=f_summary)

        
  
