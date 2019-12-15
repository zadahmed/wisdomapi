# Base class for Monty start, sumamrisation and cleanup

# Imports
import os
import time
import re
import time
from selenium import webdriver
import nltk
#nltk.download('wordnet')
#nltk.download('averaged_perceptron_tagger')
#nltk.download('maxent_ne_chunker')
#nltk.download('words')
import pandas as pd
import string
import numpy as np
from datetime import datetime
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import spacy
from nltk.corpus import stopwords 
from nltk.stem.wordnet import WordNetLemmatizer
import gensim
from gensim import corpora
from flask import jsonify

# global variables
stop = set(stopwords.words("english"))
exclude = set(string.punctuation) 
lemma = WordNetLemmatizer()

CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
GOOGLE_CHROME_SHIM = os.getenv('GOOGLE_CHROME_SHIM',"chromedriver")

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
    
    def liftOff(self):
        start_datetime = datetime.today().strftime('%d-%m-%Y %H:%M:%S')
        start = time.time()
        options = webdriver.ChromeOptions()
        options.binary_location = '/app/.apt/usr/bin/google-chrome-stable'
        options.add_argument("mute-audio")
        options.add_argument("start-fullscreen")
        options.add_argument("--disable-gpu")
        options.add_argument('no-sandbox')
        options.add_argument("disable-dev-shm-usage")
        options.add_argument("headless")
        options.add_experimental_option(
            'prefs', {
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True
            }
        )
        driver = webdriver.Chrome(options=options)
        max_screen_width = driver.get_window_size().get('width')
        max_screen_height = driver.get_window_size().get('height')
        return start_datetime, start, driver, max_screen_width, max_screen_height


    def factualSummary(self, search_me, Z, f_what_summary, f_old_history_summary_sorted, f_history_summary_sorted):
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
        # Factual timeline
        print("\n============================== Timeline of [{}] \n".format(search_me))
        if not f_old_history_summary_sorted:
            print("----> No timeline by Century:\n")
        else:
            print("----> By Century:")
            if f_old_history_summary_sorted:
                for i in f_old_history_summary_sorted:
                    print("-", i, "\n")
        if not f_history_summary_sorted:
            print("----> No timeline by Year:\n")
        else:
            print("----> By Year:")
            if f_history_summary_sorted:
                for i in f_history_summary_sorted:
                    print("-", i, "\n")
        return jsonify(search=search_me,summary=f_summary,old_history=f_old_history_summary_sorted,history=f_history_summary_sorted)

        
    def topicalSummary(self, search_me, t_news_corpus, t_video_corpus, Z):
        for i in t_news_corpus:
            t_video_corpus.append(i)
        if len(t_video_corpus)>0:
            frequency = frequency_processor(t_video_corpus)
            # Topic modelling
            doc_clean = [clean(doc).split() for doc in t_video_corpus]
            # Creating the term dictionary of our corpus, where every unique term is assigned an index. 
            dictionary = corpora.Dictionary(doc_clean)
            # Converting list of documents (corpus) into Document Term Matrix using dictionary prepared above.
            doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]
            # Creating the object for LDA model using gensim library
            Lda = gensim.models.ldamodel.LdaModel
            # Running and Training LDA model on the document term matrix.
            ldamodel = Lda(doc_term_matrix, num_topics=5, id2word = dictionary, passes=200)
            t0, t1, t2, t3, t4 = ldamodel.print_topics(num_topics=-1, num_words=5)
            key_topics = []
            topics_list = [t0, t1, t2, t3, t4]
            for i in topics_list:
                topic = i[1]
                key_topics.append(topic)
            # Summary
            print("============================== Topics in the media\n")
            n=1
            for i in key_topics:
                try:
                    topic = i.replace('"', '')
                    topic = topic.split('*')[1:]
                    topic = [j.split(" + ")[0] for j in topic]
                    new_topic = []
                    for j in topic:
                        if j == '–':
                            pass
                        elif j == '—':
                            pass
                        elif j == ' ':
                            pass
                        elif j == '':
                            pass
                        else:
                            new_topic.append(j.strip())
                    topic = " + ".join(word for word in new_topic)
                    print(str(n)+". "+topic)
                    n+=1
                except:
                    n+=1
            # Important words processing 
            t_top_N = pd.DataFrame(frequency.groupby("lemmatized word")["tf_idf"].sum())
            t_top_N = t_top_N.sort_values(by=["tf_idf"], ascending=False)
            maxi = max(t_top_N.values)[0]
            print("\n============================== Important words in the media\n")
            n=0
            m=1
            split = search_me.split()
            while m<6:
                try:
                    word = t_top_N.index[n]
                    value = t_top_N.values[n]
                    y=0
                    for i in split:
                        if i in word:
                            y+=1
                        else:
                            pass
                    if y>0:
                        n+=1
                    else:
                        print(str(m)+". "+str(word)+" ---> Monty Score: "+str(round((value[0]/maxi)*100, 2)))
                        n+=1  
                        m+=1
                except:
                    n+=1
                    m+=1
            # Interesting words processing    
            t_top_N = pd.DataFrame(frequency.groupby("lemmatized word")["idf"].sum())
            t_top_N = t_top_N.sort_values(by=["idf"], ascending=False)
            maxi = max(t_top_N.values)[0]
            print("\n============================== Interesting words in the media\n")
            n=0
            m=1
            split = search_me.split()
            while m<6:
                try:
                    word = t_top_N.index[n]
                    value = t_top_N.values[n]
                    y=0
                    for i in split:
                        if i in word:
                            y+=1
                        else:
                            pass
                    if y>0:
                        n+=1
                    else:
                        print(str(m)+". "+str(word)+" ---> Monty Score: "+str(round((value[0]/maxi)*100, 2)))
                        n+=1  
                        m+=1
                except:
                    n+=1
                    m+=1
        else:
            print("\n============================== Couldn't find any media content for [{}]\n".format(search_me))
        return jsonify(search=search_me,news_corpus=t_news_corpus,video_corpuse=t_video_corpus,summarypoints=Z)
            

    def influentialSummary(self, search_me, Z, i_blogs_corpus, i_blogs_authors, i_research_abstracts, i_research_authors):
        # Influential (bloggers) summary
        if i_blogs_corpus:
            frequency = frequency_processor(i_blogs_corpus)
            # Topic modelling
            doc_clean = [clean(doc).split() for doc in i_blogs_corpus]
            # Creating the term dictionary of our corpus, where every unique term is assigned an index. 
            dictionary = corpora.Dictionary(doc_clean)
            # Converting list of documents (corpus) into Document Term Matrix using dictionary prepared above.
            doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]
            # Creating the object for LDA model using gensim library
            Lda = gensim.models.ldamodel.LdaModel
            # Running and Trainign LDA model on the document term matrix.
            ldamodel = Lda(doc_term_matrix, num_topics=5, id2word = dictionary, passes=200)
            t0, t1, t2, t3, t4 = ldamodel.print_topics(num_topics=-1, num_words=5)
            key_topics = []
            topics_list = [t0, t1, t2, t3, t4]
            n=1
            for i in topics_list:
                topic = i[1]
                key_topics.append(topic)
                n+=1
            print("\n============================== Topics by influencers\n")
            n=1
            for i in key_topics:
                try:
                    topic = i.replace('"', '')
                    topic = topic.split('*')[1:]
                    topic = [j.split(" + ")[0] for j in topic]
                    new_topic = []
                    for j in topic:
                        if j == '–':
                            pass
                        elif j == '—':
                            pass
                        elif j == ' ':
                            pass
                        elif j == '':
                            pass
                        else:
                            new_topic.append(j.strip())
                    topic = " + ".join(word for word in new_topic)
                    print(str(n)+". "+topic)
                    n+=1
                except:
                    n+=1
            # Important words processing
            t_top_N = pd.DataFrame(frequency.groupby("lemmatized word")["tf_idf"].sum())
            t_top_N = t_top_N.sort_values(by=["tf_idf"], ascending=False)
            maxi = max(t_top_N.values)[0]
            print("\n============================== Important words by influencers\n")
            n=0
            m=1
            split = search_me.split()
            while m<6:
                try:
                    word = t_top_N.index[n]
                    value = t_top_N.values[n]
                    y=0
                    for i in split:
                        if i in word:
                            y+=1
                        else:
                            pass
                    if y>0:
                        n+=1
                    else:
                        print(str(m)+". "+str(word)+" ---> Monty Score: "+str(round((value[0]/maxi)*100, 2)))
                        n+=1  
                        m+=1
                except:
                    n+=1
                    m+=1
            # Interesting words processing
            t_top_N = pd.DataFrame(frequency.groupby("lemmatized word")["idf"].sum())
            t_top_N = t_top_N.sort_values(by=["idf"], ascending=False)
            maxi = max(t_top_N.values)[0]
            print("\n============================== Interesting words by influencers\n")
            n=0
            m=1
            split = search_me.split()
            while m<6:
                try:
                    word = t_top_N.index[n]
                    value = t_top_N.values[n]
                    y=0
                    for i in split:
                        if i in word:
                            y+=1
                        else:
                            pass
                    if y>0:
                        n+=1
                    else:
                        print(str(m)+". "+str(word)+" ---> Monty Score: "+str(round((value[0]/maxi)*100, 2)))
                        n+=1  
                        m+=1
                except:
                    n+=1
                    m+=1
        else:
            print("\n============================== Couldn't find any influential content for [{}]\n".format(search_me))
        # Influential (researchers) summary
        if i_research_abstracts:
            frequency = frequency_processor(i_research_abstracts)
            # Prepare list of abstracts for topic modelling
            doc_clean = [clean(doc).split() for doc in i_research_abstracts]
            # Creating the term dictionary of our courpus, where every unique term is assigned an index. 
            dictionary = corpora.Dictionary(doc_clean)
            # Converting list of documents (corpus) into Document Term Matrix using dictionary prepared above.
            doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]
            Lda = gensim.models.ldamodel.LdaModel
            # Running and Trainign LDA model on the document term matrix.
            ldamodel = Lda(doc_term_matrix, num_topics=5, id2word = dictionary, passes=200)
            t0, t1, t2, t3, t4 = ldamodel.print_topics(num_topics=-1, num_words=5)
            key_topics = []
            topics_list = [t0, t1, t2, t3, t4]
            for i in topics_list:
                topic = i[1]
                key_topics.append(topic)
            print("\n============================== Topics in research\n")
            n=1
            for i in key_topics:
                try:
                    topic = i.replace('"', '')
                    topic = topic.split('*')[1:]
                    topic = [j.split(" + ")[0] for j in topic]
                    new_topic = []
                    for j in topic:
                        if j == '–':
                            pass
                        elif j == '—':
                            pass
                        elif j == ' ':
                            pass
                        elif j == '':
                            pass
                        else:
                            new_topic.append(j.strip())
                    topic = " + ".join(word for word in new_topic)
                    print(str(n)+". "+topic)
                    n+=1
                except:
                    n+=1
            # Most frequent words/topics    
            t_top_N = pd.DataFrame(frequency.groupby("lemmatized word")["tf_idf"].sum())
            t_top_N = t_top_N.sort_values(by=["tf_idf"], ascending=False)
            maxi = max(t_top_N.values)[0]
            print("\n============================== Important words in research\n")
            n=0
            m=1
            split = search_me.split()
            while m<6:
                try:
                    word = t_top_N.index[n]
                    value = t_top_N.values[n]
                    y=0
                    for i in split:
                        if i in word:
                            y+=1
                        else:
                            pass
                    if y>0:
                        n+=1
                    else:
                        print(str(m)+". "+str(word)+" ---> Monty Score: "+str(round((value[0]/maxi)*100, 2)))
                        n+=1  
                        m+=1
                except:
                    n+=1
                    m+=1
            # Most frequent words/topics    
            t_top_N = pd.DataFrame(frequency.groupby("lemmatized word")["idf"].sum())
            t_top_N = t_top_N.sort_values(by=["idf"], ascending=False)
            maxi = max(t_top_N.values)[0]
            print("\n============================== Interesting words in research\n")
            n=0
            m=1
            split = search_me.split()
            while m<6:
                try:
                    word = t_top_N.index[n]
                    value = t_top_N.values[n]
                    y=0
                    for i in split:
                        if i in word:
                            y+=1
                        else:
                            pass
                    if y>0:
                        n+=1
                    else:
                        print(str(m)+". "+str(word)+" ---> Monty Score: "+str(round((value[0]/maxi)*100, 2)))
                        n+=1  
                        m+=1
                except:
                    n+=1
                    m+=1
            # Who are the influencers
            blogs_authors = pd.value_counts(i_blogs_authors).reset_index()
            blogs_authors.columns = ["authors", "count"]
            i_top_N = pd.DataFrame(blogs_authors.groupby("authors")["count"].sum())
            i_top_N = i_top_N.sort_values(by=["count"], ascending=False)[:5]
            print("\n============================== Who are the influencers\n")
            n=0
            m=1
            while n<5:
                try:
                    print(str(m)+". "+str(i_top_N.index[n])+" ---> appeared "+str(i_top_N.values[n][0])+" times")
                    n+=1
                    m+=1
                except:
                    n+=1
                    m+=1
            # Research authors processing
            authors = []
            for i in i_research_authors:
                for j in i.split(", "):
                    authors.append(j)
            authors = pd.value_counts(authors).reset_index()
            authors.columns = ["authors", "count"]
            i_top_N = pd.DataFrame(authors.groupby("authors")["count"].sum())
            i_top_N = i_top_N.sort_values(by=["count"], ascending=False)[:5]
            print("\n============================== Who are the researchers\n")
            n=0
            m=1
            while n<5:
                try:
                    print(str(m)+". "+str(i_top_N.index[n])+" ---> appeared "+str(i_top_N.values[n][0])+" times")
                    n+=1  
                    m+=1
                except:
                    n+=1
                    m+=1
        else:
            print("\n============================== Couldn't find any research content for [{}]".format(search_me))
        print("\n")
        return jsonify(search=search_me, summary = Z, blogs_corpus = i_blogs_corpus, blogs_author = i_blogs_authors,research_abstracts =  i_research_abstracts,research_authors =  i_research_authors)
            
            
    def contextSummary(self, t_news_entities, t_video_entities, t_video_dates, i_blogs_entities, i_blogs_dates, t_news_dates, t_news_locations, t_video_locations, t_related_searches, search_me):
        # Associated People & Companies using Named Entity Recognition
        for i in t_news_entities:
            t_video_entities.append(i)
        for i in i_blogs_entities:
            t_video_entities.append(i)
        final_entities = list(set(t_video_entities))
        final_entities = ["{}".format(i) for i in final_entities]
        nlp=spacy.load('en')
        people = []
        companies = []
        for i in final_entities:
            values = []
            ent = nlp(i)
            for j in ent:
                values.append(j.ent_type_)
            if "PERSON" in values:
                if i not in people:
                    people.append(i)
                else:
                    pass
            elif "ORG" in values:
                if i not in companies:
                    companies.append(i)
                else:
                    pass
            else:
                pass
        t_topical_people = list(set(people))
        t_topical_people = [i for i in t_topical_people if len(i)>1]
        t_topical_people = [i for i in t_topical_people if i!='']
        t_topical_people = [i.translate({ord('\f') : ' ', ord('\t') : ' ', ord('\n') : '', ord('\r') : None}) for i in t_topical_people]
        t_topical_companies = list(set(companies))
        t_topical_companies = [i for i in t_topical_companies if len(i)>1]
        t_topical_companies = [i for i in t_topical_companies if i!='']
        t_topical_companies = [i.translate({ord('\f') : ' ', ord('\t') : ' ', ord('\n') : '', ord('\r') : None}) for i in t_topical_companies]
        print("\n============================== People & Organisations")
        print("\n----> People:")
        print(', '.join(t_topical_people))
        print("\n----> Organisations:")
        print(', '.join(t_topical_companies))
        # Time Series Analysis
        all_dates = []
        if t_video_dates:
            for i in t_video_dates:
                try:
                    all_dates.append(i.split("on ")[1])
                except:
                    pass
        if t_news_dates:
            try:
                for i in t_news_dates:
                    all_dates.append(i.split("-")[1])
            except:
                pass
        final_dates = []
        for i in all_dates:
            try:
                if len(i.split())==1:
                    pass
                elif i.split()[1]=="Jan":
                    i = str(i.split()[0])+"-01-"+str(i.split()[2])
                    final_dates.append(i)
                elif i.split()[1]=="Feb":
                    i = str(i.split()[0])+"-02-"+str(i.split()[2])
                    final_dates.append(i)
                elif i.split()[1]=="Mar":
                    i = str(i.split()[0])+"-03-"+str(i.split()[2])
                    final_dates.append(i)
                elif i.split()[1]=="Apr":
                    i = str(i.split()[0])+"-04-"+str(i.split()[2])
                    final_dates.append(i)
                elif i.split()[1]=="May":
                    i = str(i.split()[0])+"-05-"+str(i.split()[2])
                    final_dates.append(i)
                elif i.split()[1]=="Jun":
                    i = str(i.split()[0])+"-06-"+str(i.split()[2])
                    final_dates.append(i)
                elif i.split()[1]=="Jul":
                    i = str(i.split()[0])+"-07-"+str(i.split()[2])
                    final_dates.append(i)
                elif i.split()[1]=="Aug":
                    i = str(i.split()[0])+"-08-"+str(i.split()[2])
                    final_dates.append(i)
                elif i.split()[1]=="Sep":
                    i = str(i.split()[0])+"-09-"+str(i.split()[2])
                    final_dates.append(i)
                elif i.split()[1]=="Oct":
                    i = str(i.split()[0])+"-10-"+str(i.split()[2])
                    final_dates.append(i)
                elif i.split()[1]=="Nov":
                    i = str(i.split()[0])+"-11-"+str(i.split()[2])
                    final_dates.append(i)
                elif i.split()[1]=="Dec":
                    i = str(i.split()[0])+"-12-"+str(i.split()[2])
                    final_dates.append(i)
                elif "ago" in i:
                    i = datetime.today().strftime('%d-%m-%Y')
                    final_dates.append(i)
                else:
                    pass
            except:
                pass
        for i in i_blogs_dates:
            try:
                date = re.sub(",", "", i)
                if len(date.split())==3:
                    month = date.split()[0]
                    day = date.split()[1]
                    year = date.split()[2]
                    if month == "Jan":
                        final_dates.append(day+"-01-"+year)
                    elif month == "Feb":
                        final_dates.append(day+"-02-"+year)
                    elif month == "Mar":
                        final_dates.append(day+"-03-"+year)
                    elif month == "Apr":
                        final_dates.append(day+"-04-"+year)
                    elif month == "May":
                        final_dates.append(day+"-05-"+year)
                    elif month == "Jun":
                        final_dates.append(day+"-06-"+year)
                    elif month == "Jul":
                        final_dates.append(day+"-07-"+year)
                    elif month == "Aug":
                        final_dates.append(day+"-08-"+year)
                    elif month == "Sep":
                        final_dates.append(day+"-09-"+year) 
                    elif month == "Oct":
                        final_dates.append(day+"-10-"+year)
                    elif month == "Nov":
                        final_dates.append(day+"-11-"+year)
                    elif month == "Dec":
                        final_dates.append(day+"-12-"+year)
            except:
                pass
        t_topical_dates = pd.DataFrame(columns=["dates"])
        t_topical_dates["dates"] = final_dates
        t_topical_dates["dates"] = pd.to_datetime(t_topical_dates["dates"], dayfirst=True) 
        dates_monthly = t_topical_dates["dates"].astype(str)
        final_dates_monthly = []
        for i in dates_monthly:
            final_dates_monthly.append(i[:-3])
        t_topical_dates["dates_monthly"] = final_dates_monthly
        t_topical_dates["count"] = 1
        t_topical_dates = t_topical_dates.sort_values(by=["dates"], ascending=True)
        t_topical_dates = pd.DataFrame(t_topical_dates.groupby("dates_monthly", as_index=False)["count"].sum())
        print("\n============================== Monthly time series analysis\n")
        n=0
        while n<len(t_topical_dates):
            print("-", t_topical_dates["dates_monthly"][n], "---> appeared", t_topical_dates["count"][n], "times")
            n+=1   
        # Geographical analysis
        for i in t_news_locations:
            t_video_locations.append(i)
        final_locations = []
        for i in t_video_locations:
            if "UK" in i:
                final_locations.append("United Kingdom")
            elif "US" in i:
                final_locations.append("United States")
            elif "FR" in i:
                final_locations.append("FRANCE")
            elif "GB" in i:
                final_locations.append("United Kingdom")
            elif "REDACTED FOR PRIVACY" in i:
                final_locations.append("N/A")
            elif "Phone" in i:
                final_locations.append("N/A")
            elif "HK" in i:
                final_locations.append("Hong Kong")
            elif "PA" in i:
                final_locations.append("Panama")
            elif "CA" in i:
                final_locations.append("Canada")
            elif "IN" in i:
                final_locations.append("India")
            elif "IE" in i:
                final_locations.append("Ireland")
            elif "AU" in i:
                final_locations.append("Australia")
            elif "fr" in i:
                final_locations.append("France")
            elif "ES" in i:
                final_locations.append("Spain")
            elif "CO" in i:
                final_locations.append("Colombia")
            elif "ca" in i:
                final_locations.append("Canada")
            else:
                final_locations.append(i)
        t_topical_locations, t_topical_locations_count = np.unique(final_locations, return_counts=True)
        print("\n============================== Geographical topical analysis\n")
        n=0
        while n<len(t_topical_locations):
            print("-", t_topical_locations[n], "---> posted", t_topical_locations_count[n], "piece(s) of content")
            n+=1
        # Recommended searches
        print("\n============================== Recommended searches\n")
        for i in t_related_searches:
            print("- "+i)
        print("\n")
        
    
                 
    def topicalAppendix(self, t_video_ids, t_video_urls, t_video_dates, t_news_articles, t_news_dates, t_article_links):
        print("\n============================== APPENDIX:\n")
        print("----> "+str(len(t_video_urls))+" videos watched:")
        p=1
        q=0
        if t_video_urls:
            for i in t_video_ids:
                try:
                    print(str(p)+". "+i+" - URL: "+t_video_urls[q], "- Date: "+t_video_dates[q].split("Published on ")[1])
                    p+=1
                    q+=1
                except:
                    print("- Error with {}".format(i))
                    p+=1
                    q+=1
        print("\n"+"----> "+str(len(t_article_links))+" articles read:")
        r=1
        h=0
        if t_article_links:
            for i in t_article_links:
                try:
                    print(str(r)+". "+t_news_articles[h]+" - URL: "+i+" - Date: "+t_news_dates[h].split("-")[1])
                    r+=1
                    h+=1
                except:
                    print("- Error with {}".format(i))
                    r+=1
                    h+=1


    def influentialAppendix(self, i_blogs_links, i_research_titles, i_research_authors):
        print("\n"+"----> "+str(len(i_blogs_links))+" blogs read:")
        m=1
        if i_blogs_links:
            for i in i_blogs_links:
                try:
                    print("- "+str(m)+". "+i)
                    m+=1
                except:
                    print("- Error with {}".format(i))
                    m+=1

        print("\n"+"----> "+str(len(i_research_titles))+" research papers read:")
        n=0
        m=1
        if i_research_titles:
            for i in i_research_titles:
                try:
                    title = i
                    print("- "+str(m)+". "+title+": "+i_research_authors[n])
                    n+=1
                    m+=1
                except:
                    print("- Error with {}".format(i))
                    n+=1
                    m+=1


    def finish(self, driver, start_datetime, start, search_topic, search_me, Z):
        end = time.time()
        duration_min = round((end-start)/60, 2)
        print("\n============================== Montgomery's summary was completed in", duration_min, "minutes :) \n")
        clean_up = []
        driver.close()
        print("~"*50, " Wisdom ", "~"*50)
        print("\nCreated with love by AGP :)\n")
        for file in os.listdir(os.getcwd()):
            if "{}_".format(search_me) in file:
                clean_up.append(file)
        for file in clean_up:
            os.remove(file)
        clean_up = []
        for file in os.listdir(os.getcwd()):
            if file.endswith(".vtt"):
                clean_up.append(file)
        for file in clean_up:
            os.remove(file)
        if os.path.isfile("MontgomeryLog.txt"):
            log = open("MontgomeryLog.txt", "a")
            while True:
                try:
                    rating = int(input("- Before you go, would you kindly leave a rating for my analysis? (0=terrible, 10=amazing) "))
                    break
                except:
                    print("- Please enter a numerical value, try again...")
        else:
            log = open("MontgomeryLog.txt", "w")
            while True:
                try:
                    rating = int(input("- Before you go, would you kindly leave a rating for my analysis? (0=terrible, 10=amazing) "))
                    break
                except:
                    print("- Please enter a numerical value, try again...")
        print("- Thank you :)\n")
        log_data = "Datetime: "+str(start_datetime)+" - Topic: "+str(search_topic)+" - Search: "+str(search_me)+" - Summary Points: "+str(Z)+" - Rating: "+str(rating)
        log.write("\n")
        log.write(log_data)
        log.close()

