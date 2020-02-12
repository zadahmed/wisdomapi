import requests
import os
import time
import re
import time
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium import webdriver
from lxml import html
import spacy
from nltk.tokenize import sent_tokenize


def YoutubeCleaner():
    """
    Cleaning function for Youtube
    
    Parameters
    ----------
    """
    # Locate and read the .vtt subtitle files in the cwd()
    to_watch = []
    t_video_corpus = []
    t_video_entities = []
    for file in os.listdir(os.getcwd()):
        if file.endswith(".vtt"):
            to_watch.append(file)
    if to_watch:
        try:
            for i in to_watch:
                try:
                    print("    - Cleaning:", i)
                    new_text = []
                    final_text = []
                    with open(i, "r") as f:
                        for line in f:
                            new_text.append(line)
                            new_text = [j.translate({ord('\f') : ' ', ord('\t') : ' ', ord('\n') : '', ord('\r') : None}) for j in new_text]
                            new_text = [j for j in new_text if not ((j[0:1].isdigit()) and (j[3:4].isdigit()) and (j[6:7].isdigit()))]
                            new_text = [j for j in new_text if not ((j[2:3].isdigit()) and (j[5:6].isdigit()) and (j[8:9].isdigit()))]
                            new_text = [j for j in new_text if not ((j[3:4].isdigit()) and (j[6:7].isdigit()) and (j[9:10].isdigit()))]
                            new_text = [j for j in new_text if j!=' ']
                            new_text = [j for j in new_text if j!='']
                            new_text = [j.strip() for j in new_text]
                    # Remove preamble sentences at the top of .vtt file
                    new_text = new_text[3:]
                    # Remove duplicating sentences
                    n=1
                    m=0
                    indices_to_remove = []
                    while n<len(new_text)-1:
                        if " ".join(new_text[n].split()[:3]) in new_text[m]:
                            indices_to_remove.append(n)
                            n+=1
                        elif " ".join(new_text[n].split()[:3]) not in new_text[m]:
                            m=n
                            n+=1
                        else:
                            pass
                    for index in sorted(indices_to_remove, reverse=True):
                        del new_text[index]
                    # Another layer of duplicate sentence removal
                    n=0
                    m=1
                    indices_to_remove = []
                    while n<len(new_text)-2:
                        if new_text[n] in new_text[m]:
                            indices_to_remove.append(n)
                            n+=1
                            m+=1
                        elif new_text[n] not in new_text[m]:
                            n+=1
                            m+=1
                        else:
                            pass
                    for index in sorted(indices_to_remove, reverse=True):
                        del new_text[index]
                    # Final layer of duplicate sentence removal
                    new_text1 = set()
                    new_text2 = [] 
                    for j in new_text:
                        if j not in new_text1:
                            new_text1.add(i)
                            new_text2.append(i)
                        else:
                            pass
                    n=0
                    m=1
                    indices_to_remove = []
                    while n<len(new_text2)-2:
                        if new_text2[n] in new_text2[m]:
                            indices_to_remove.append(n)
                            n+=1
                            m+=1
                        elif new_text2[n] not in new_text2[m]:
                            n+=1
                            m+=1
                        else:
                            pass
                    for index in sorted(indices_to_remove, reverse=True):
                        del new_text2[index]
                    new_text = new_text2
                    # Recreate sentence structure
                    new_text = [''.join(str(j) + " " for j in new_text)] # join sentences together
                    html_parsed_text = BeautifulSoup(new_text[0], "html.parser") # remove html tags
                    html_parsed_text = html_parsed_text.get_text() # remove html tags
                    html_parsed_text = html_parsed_text.replace("&gt;", "") # remove strange '&gt;'
                    new_text = [html_parsed_text]
                    new_text = [sent_tokenize(j) for j in new_text] # break into sentences
                    new_text = new_text[0]
                    new_text = [re.sub('[<>]', "", j) for j in new_text]
                    new_text = [j for j in new_text if "><" not in j]
                    new_text = [re.sub('\d\d:\d\d:\d\d.\d\d\d', "", j) for j in new_text]
                    new_text = [re.sub(".vtt", "", j) for j in new_text]
                    new_text = [re.sub("vtt", "", j) for j in new_text]
                    new_text = [''.join(str(j) + " " for j in new_text)] # join sentences back together
                    new_text = [sent_tokenize(j) for j in new_text][0] # break into sentences
                    new_text1 = set()
                    new_text2 = []
                    # Remove duplicated sentences
                    for j in new_text:
                        if j not in new_text1:
                            new_text1.add(j)
                            new_text2.append(j)
                        else:
                            pass
                    if '' in new_text2:
                        new_text2.remove('') # remove any leftover '' empty strings
                    else:
                        pass
                    new_text2 = [j.lstrip() for j in new_text2] # remove leading whitespace
                    if len(new_text2)>1 and (new_text2[0] in new_text2[1]):
                        new_text2 = new_text2[0::2]
                    else:
                        pass
                    # Remove trailing sentneces that repeat several words
                    new_text = []
                    for j in new_text2:
                        for k in sent_tokenize(j):
                            new_text.append(k)
                    # Final cleaning
                    new_text = [''.join(str(j) + " " for j in new_text)]
                    new_text = [sent_tokenize(j) for j in new_text] # break into sentences
                    new_text = new_text[0]
                    # Only select shorter sentences
                    new_text = [j for j in new_text if len(j)<500]
                    new_text = [''.join(str(j) + " " for j in new_text)] # join sentences back together
                    new_text = [j.lstrip() for j in new_text] # remove leading whitespace
                    new_text = [j.rstrip() for j in new_text] # remove trailing whitespace
                    # Add '.' to the end of the final sentence if needs be
                    if len(new_text)>0 and (new_text[0][-1]) == ".":
                        final_text.append(new_text[0])
                    elif len(new_text)>0 and (new_text[0][-1]) != ".":
                        new_text = [new_text[0]+str(".")]
                        final_text.append(new_text[0])
                    elif new_text[0] == '':
                        new_text.remove('')
                        if len(new_text)==0:
                            pass
                        else:
                            final_text.append(new_text[0])
                    else:
                        pass
                    # Get rid of all capitalised and gibberish text
                    x=0
                    for j in final_text[0].split("."):
                        if (len(j)>20) and (j.isupper()):
                            x+=1
                        else:
                            pass
                    if x>0:
                        pass
                    else:  
                        # Get entities using NER
                        nlp=spacy.load('en')
                        text=final_text[0]
                        ents = nlp(text)
                        for j in ents.ents:
                            t_video_entities.append(j)
                        t_video_corpus.append(final_text[0])
                except Exception as e:
                    print("    ----> Error with:", i, "moving onto the next one...")
                    print(e)
        except:
            print("----> No videos found...")
    print("- Video content added to corpus :)")
    if not t_video_corpus:
        t_video_corpus = []
    if not t_video_entities:
        t_video_entities = []
    return t_video_corpus, t_video_entities


def GoogleNewsCleaner(t_article_links, t_news_articles):
    # Create corpus
    punctuation = [".", "?", "!"]
    t_news_corpus = []
    t_news_entities = []
    m=0
    n=1
    for link in t_article_links:
        try:
            print("    "+str(n)+". Reading:", t_news_articles[m])
            t_news_url = requests.get(link, timeout=5)
            raw_data = t_news_url.text
            news_soup = BeautifulSoup(raw_data, 'html.parser')
            news = news_soup.find_all("p")
            nlp = spacy.load('en')
            for i in news:
                try:
                    text = i.get_text()
                    text = re.sub("\n", "", text)
                    if text[-1] in punctuation:
                        entities = nlp(text)
                        for j in entities.ents:
                            t_news_entities.append(j)
                        t_news_corpus.append(text)
                except:
                    pass
            n += 1
            m += 1
        except:
            print("    ----> Faulty link, moving onto the next one...")
            n += 1
            m += 1
    return t_news_corpus, t_news_entities