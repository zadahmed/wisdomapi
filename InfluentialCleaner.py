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


def GoogleBlogsCleaner(i_blogs_links, i_blogs_articles):
    # Create corpus
    punctuation = [".", "?", "!", "..."]
    i_blogs_corpus = []
    i_blogs_entities = []
    m=0
    n=1
    for link in i_blogs_links:
        try:
            print("    "+str(n)+". Reading:", i_blogs_articles[m])
            i_blogs_url = requests.get(link, timeout=5)
            raw_data = i_blogs_url.text
            blog_soup = BeautifulSoup(raw_data, 'html.parser')
            blog = blog_soup.find_all("p")
            nlp = spacy.load('en')
            for i in blog:
                try:
                    text = i.get_text()
                    text = re.sub("\n", "", text)
                    if text[-1] in punctuation:
                        entities = nlp(text)
                        for j in entities.ents:
                            i_blogs_entities.append(j)
                        i_blogs_corpus.append(text)
                except:
                    pass
            n += 1
            m += 1
        except:
            print("    ----> Faulty link, moving onto the next one...")
            n += 1
            m += 1
    return i_blogs_corpus, i_blogs_entities


def MediumCleaner(i_medium_links):
    # Create corpus
    punctuation = [".", "?", "!", "..."]
    i_medium_corpus = []
    i_medium_entities = []
    i_medium_authors = []
    i_medium_dates = []
    m=0
    n=1
    for link in i_medium_links:
        try:
            i_medium_url = requests.get(link, timeout=5)
            raw_data = i_medium_url.text
            medium_soup = BeautifulSoup(raw_data, 'html.parser')
            header = medium_soup.find_all("h1")[0]
            print("    "+str(n)+". Reading:", header.get_text())
            author = medium_soup.find_all("a", class_="ds-link")
            i_medium_authors.append(author[0].get_text())
            date = medium_soup.find_all("time")
            i_medium_dates.append(date[0].get_text())
            blog = medium_soup.find_all("p")
            nlp = spacy.load('en')
            for i in blog:
                try:
                    text = i.get_text()
                    text = re.sub("\n", "", text)
                    if text[-1] in punctuation:
                        entities = nlp(text)
                        for j in entities.ents:
                            i_medium_entities.append(j)
                        i_medium_corpus.append(text)
                except:
                    pass
            n += 1
            m += 1
        except:
            print("    ----> Faulty link, moving onto the next one...")
            n += 1
            m += 1
    return i_medium_corpus, i_medium_entities, i_medium_authors, i_medium_dates


def ElsevierCleaner(i_elsevier_titles, i_elsevier_links, driver):
    m = 0
    n = 1
    try:
        # Get abstracts of filtered papers
        i_elsevier_abstracts = []
        for i in i_elsevier_links:
            try:
                driver.get(i)
                print("    "+str(n)+". Reading:", i_elsevier_titles[m])
                text = driver.find_element_by_class_name("Abstracts").text
                text = re.sub("Abstract\n", "", text)
                text = re.sub("Highlights\n", "", text)
                text = re.sub("•\n", "", text)
                text = re.sub("\n", "", text)
                i_elsevier_abstracts.append(text)
                n += 1
                m += 1
            except:
                print("    ----> Faulty link, moving onto the next one...")
                n += 1
                m += 1
    except:
        pass
    if not i_elsevier_abstracts:
        i_elsevier_abstracts = []
    return i_elsevier_abstracts


def ArXivCleaner(i_arxiv_links, i_arxiv_titles):
    # Create corpus
    punctuation = [".", "?", "!", "..."]
    i_arxiv_abstracts = []
    i_arxiv_authors = []
    m=0
    n=1
    for link in i_arxiv_links:
        try:
            i_arxiv_url = requests.get(link, timeout=5)
            raw_data = i_arxiv_url.text
            arxiv_soup = BeautifulSoup(raw_data, 'html.parser')
            print("    "+str(n)+". Reading:", i_arxiv_titles[m])
            authors = arxiv_soup.find_all("div", class_="authors")[0]
            authors = authors.get_text()
            authors = re.sub('Authors:', '', authors)
            authors = re.sub("\n", "", authors)
            i_arxiv_authors.append(authors)
            abstract = arxiv_soup.find_all("blockquote", class_="abstract")[0]
            abstract = abstract.get_text()
            abstract = re.sub('Abstract:  ', '', abstract)
            abstract = re.sub("\n", " ", abstract)
            i_arxiv_abstracts.append(abstract)
            n += 1
            m += 1
        except:
            print("    ----> Faulty link, moving onto the next one...")
            n += 1
            m += 1
    print("\n")
    return i_arxiv_abstracts, i_arxiv_authors