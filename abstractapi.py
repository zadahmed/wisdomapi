# imports
import pdfplumber
from pathlib import Path
import requests
import re
import string
import os

def abstractextracter(pdfurl):
    # download pdf
    url_name = pdfurl.split("/")[-1]
    if ".pdf" not in url_name:
        pdf = Path(url_name+".pdf")
        url_name += ".pdf"
    else:
        pdf = Path(url_name)
    response = requests.get(pdfurl)
    pdf.write_bytes(response.content);
    # get page number for abstract
    pdf = pdfplumber.open(url_name)
    cnt = 0
    while True:
        try:
            page = pdf.pages[cnt]
            if "abstract" in page.extract_text().lower():
                break
            elif "introduction" in page.extract_text().lower():
                break
            else:
                cnt += 1
        except:
            cnt = 0
            break
        break
    # get bounding box for text
    page = pdf.pages[cnt]
    text = page.extract_words()
    x0 = []
    x1 = []
    top = []
    bottom = []
    for i in text:
        x0.append(float(i.get('x0')))
        x1.append(float(i.get('x1')))
        top.append(float(i.get('top')))
        bottom.append(float(i.get('bottom')))
    # identify abstract region
    x0.sort()
    x0 = list(set(x0))
    dist = []
    cnt = 0
    while cnt < len(x0)-1:
        dist.append(x0[cnt+1]-x0[cnt])
        cnt += 1
    if max(dist) == dist[0]:
        x_min = min([float(i.get('x1')) for i in text if float(i.get('x0')) == min(x0)])
    else: 
        x_min = min(x0)
    # if Author = IEEE split bounding box down the middle for double columns
    if pdf.metadata.get("Author") == "IEEE":
        coords = (35, min(top), float(page.width/2), max(bottom))
    else:
        coords = (35, min(top), max(x1), max(bottom))
    # crop pdf
    cropped = page.within_bbox(coords)
    content = cropped.extract_text(x_tolerance=1)
    # extract abstract
    abstract = []
    cnt = 0
    text = content.split("\n")
    while cnt < len(text):
        if "abstract" in text[cnt].lower():
            if "abstract" in text[cnt].lower() and len(text[cnt].split()) < 8:
                cnt += 1
            if "introduction" not in content.lower():
                while True:
                    if "*" in text[cnt] and len(text[cnt].split()) < 10:
                        cnt += 1
                    if "introduction" in text[cnt].lower():
                        break
                    elif len(text[cnt].split()) > 10:
                        if "introduction" in text[cnt][:20].lower() or "i ntroduction" in text[cnt][:20].lower():
                            break
                        abstract.append(text[cnt])
                        cnt +=1
                    elif len(text[cnt].split()) == 1:
                        if "introduction" in text[cnt].lower():
                            break
                        elif abstract[-1][-1] not in string.punctuation:
                            if text[cnt][-1] in string.punctuation:
                                abstract.append(text[cnt])
                            cnt += 1
                        else:
                            try:
                                int(text[cnt])
                            except:
                                break
                        break
                    else:
                        break
                break
            else:
                while True:
                    if "introduction" in text[cnt].lower():
                        break
                    abstract.append(text[cnt])
                    cnt += 1
                break
        else:
            cnt += 1
    if not abstract:
        stop = 0
        while True:
            #if "introduction" in text[stop].lower() and len(text[stop].split()) < 5:
            if "introduction" in text[stop].lower():
                break
            else:
                stop += 1
        cnt = 0
        while cnt < stop:
    #         if text[cnt] == " " or len(text[cnt]) < 2:
    #             if len(text[cnt+1].split()) < 10:
    #                 cnt += 1
    #             else:
    #                 abstract.append(text[cnt+1])
    #                 if text[cnt+1][-1] == "-" or text[cnt+1][:-1] == "-":
    #                     while True:
    #                         if text[cnt+2][0].islower():
    #                             abstract.append(text[cnt+2])
    #                             break
    #                         else:
    #                             cnt += 1
    #         cnt += 1
            abstract.append(text[cnt])
            cnt += 1
    # format abstract to present to user
    abstract_string = ""
    for a in abstract:
        a = re.sub("-\n", "", a)
        a = re.sub("\n", " ", a)
        if a[-1] not in string.punctuation:
            abstract_string += a+" "
        elif a[-1] == "-" or a[-1] == "-":
            abstract_string += a[:-1]
        elif a[-1] in string.punctuation:
            abstract_string += a+" "
    # remove word 'abstract' and date at start
    if "abstract" in abstract_string[:8].lower():
        abstract_string = abstract_string[8:]
    dummy1 = abstract_string.split(". ")
    dummy2 = abstract_string.split()
    if "abstract" in dummy1[0].lower():
        cnt = 0
        while True:
            if dummy2[cnt].lower().strip() != "abstract":
                cnt += 1
            else:
                cnt += 1
                break
        abstract_string = " ".join(word for word in dummy2[cnt:])
    if abstract_string[:1] in string.punctuation or abstract_string[:1] == "—":
        abstract_string = abstract_string[1:]
    abstract_string = abstract_string.strip()
    abstract_string = re.sub("  ", " ", abstract_string)
    # clean up and return abstract
    os.remove(url_name)
    return abstract_string
