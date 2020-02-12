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


def wikiCleaner(main_data, history_data, history_type, search_me):
    """
    Cleaning function for Wikipedia

    Parameters
    ----------
    main_data : str
        HTML string parsed by BeautifulSoup for WHAT
    history_data : str
        HTML string parsed by BeautifulSoup for WHEN
    history_type: str
        Either timeline or history that was collected
    search_me : str
        Search term
    """
    # 1. Create text files to contain soup text
    file = open("{}_wikipedia.txt".format(search_me), "w")
    for i in main_data:
        file.write(str(i))
    file.close()
    # 2. Clean original text file
    with open("{}_wikipedia.txt".format(search_me), "r") as f:
        file = open("{}_wikipedia_cleaned.txt".format(search_me), "w")
        for line in f:
            if "h1" in line:
                file.write("%&|"+line)
            elif "<p>" in line:
                file.write(line)
            elif "<h2>" in line:
                file.write("%&|"+line)
            else:
                pass
    file.close()
    # 3. Create final text file
    corpus_checker = []
    with open("{}_wikipedia_cleaned.txt".format(search_me), "r") as f:
        file = open("{}_wikipedia_final.txt".format(search_me), "w")
        for line in f:
            line = line.rstrip()
            line = "'"+str(line)+"'"
            if "mw-parser-output" in line:
                pass
            elif "%&|" in line:
                text = BeautifulSoup(line, "html.parser").get_text().upper().replace("%&|", "")
            else:
                text = BeautifulSoup(line, "html.parser").get_text()
            if text not in corpus_checker:
                text = text[1:]
                text = text[:-1]
                text = re.sub("[\\[].*?[\\]]", "", text)
                file.write(text)
                file.write("\n")
                corpus_checker.append(text) 
            else:
                pass
    file.close()
    # 4. Extract WHAT and WHEN from Wiki page
    what_summary = []
    when_summary = []
    headers = []
    with open("{}_{}_final.txt".format(search_me, "wikipedia"), "r") as f:
        n=0
        while True:
            for line in f:
                if line.isupper():
                    headers.append(line)
                    n+=1
                elif "HISTORY" in headers[-1]:
                    when_summary.append(line)
                else:
                    if n<2:
                        try:
                            what_summary.append(line)
                        except:
                            pass
                    else:
                        break
            break
    # 5. Initial timeline extraction from Wiki page
    old_history_summary = {}
    history_summary = {}
    events = []
    n = 1
    m = 1
    for i in when_summary:
        try:
            check = re.sub("\n", "", i)
            if check[-1] == ".":
                stripped_history = re.sub(r'[^\w\s]', '', i)
                if "th century" in i.lower():
                    stripped_history = re.sub('th', '', stripped_history)
                    stripped_history = re.sub('  ', '', stripped_history)
                    dates = [s for s in stripped_history.split() if s.isdigit() and len(s)==2]
                    if dates:
                        for date in dates:
                            if i not in events:
                                old_history_summary[m] = {str(date)+"th century":re.sub("\n", " ", i)}
                                events.append(i)
                                m += 1               
                else: 
                    stripped_history = re.sub('s', '', stripped_history)
                    stripped_history = re.sub('  ', '', stripped_history)
                    dates = [s for s in stripped_history.split() if s.isdigit() and 3<=len(s)<=4 and 1000<int(s)<2100]
                    if dates:
                        for date in dates:
                            if i not in events:
                                history_summary[n] = {date:re.sub("\n", " ", i)}
                                events.append(i)
                                n += 1
        except:
            pass
    old_history_summary_sorted = []
    history_summary_sorted = []
    if "history" in history_type.lower():
        # 6. Extraction of data from "History of..." Wiki page
        history = []
        try:
            for i in history_data.find_all('p'):
                text = i.get_text()
                text = re.sub("[\\[].*?[\\]]", "", text)
                history.append(text)
        except:
            pass
        # 7. Extraction of temporal data from "History of..." Wiki page 
        for i in history:
            try:
                check = re.sub("\n", "", i)
                if check[-1] == ".":
                    stripped_history = re.sub(r'[^\w\s]', '', i)
                    if "th century" in i.lower():
                        stripped_history = re.sub('th', '', stripped_history)
                        stripped_history = re.sub('  ', '', stripped_history)
                        dates = [s for s in stripped_history.split() if s.isdigit() and len(s)==2]
                        if dates:
                            for date in dates:
                                if i not in events:
                                    old_history_summary[m] = {str(date)+"th century":re.sub("\n", " ", i)}
                                    events.append(i)
                                    m += 1               
                    else: 
                        stripped_history = re.sub('s', '', stripped_history)
                        stripped_history = re.sub('  ', '', stripped_history)
                        dates = [s for s in stripped_history.split() if s.isdigit() and 3<=len(s)<=4 and 1000<int(s)<2100]
                        if dates:
                            for date in dates:
                                if i not in events:
                                    history_summary[n] = {date:re.sub("\n", " ", i)}
                                    events.append(i)
                                    n += 1
            except:
                pass
        # 8. Sort history data ready for presentation  
        try:
            for i in old_history_summary:
                event = old_history_summary.get(i)
                for j in event:
                    old_history_summary_sorted.append(str(j)+" - "+str(event[j]))
            old_history_summary_sorted.sort()
        except:
            pass
        try:
            for i in history_summary:
                event = history_summary.get(i)
                for j in event:
                    history_summary_sorted.append(str(j)+" - "+str(event[j]))
            history_summary_sorted.sort()
        except:
            pass
    elif "timeline" in history_type.lower():
        # 1. Create text files to contain soup text
        file = open("{}_wikipedia_timeline.txt".format(search_me), "w")
        for i in history_data.find_all(['p', 'li', 'h2', 'h3']):
            text = i.get_text()
            text = re.sub("[\\[].*?[\\]]", "", text)
            text = text.split("\n")
            for j in text:
                file.write(str(j))
                file.write("\n")
        file.close()
        # 2. Clean timeline data within text file
        corpus_checker = []
        with open("{}_wikipedia_timeline.txt".format(search_me), "r") as f:
            for line in f:
                text = re.sub("[\\[].*?[\\]]", "", line)
                text = re.sub("\n", "", text)
                if len(text) == 5:
                    pass
                elif len(text) == 4:
                    try:
                        corpus_checker.append(int(text))
                    except:
                        pass
                else:
                    corpus_checker.append(text)
        file.close()
        # 3. Create list of timeline for presentation
        timeline_checker = []
        while True:
            for i in corpus_checker:
                if isinstance(i, int):
                    year = i
                elif "this is a timeline of" in i.lower():
                    pass
                elif "See also" in i:
                    pass
                elif "References" in i:
                    pass
                elif "^" in i:
                    break
                elif "List of" in i:
                    break
                elif len(i) > 15:
                    event = i
                    if event not in timeline_checker:
                        history_summary_sorted.append(str(year)+" - "+str(event))
                        timeline_checker.append(event)
            break
    return what_summary, old_history_summary_sorted, history_summary_sorted