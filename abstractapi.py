# Imports
import string
import re
import requests
import io
from PyPDF2 import PdfFileReader

def abstractextracter(pdfurl):
    
    ######## Get all text from PDF url
    r = requests.get(pdfurl, stream=True)
    f = io.BytesIO(r.content)
    reader = PdfFileReader(f)
    # Iterate through each page and collect all text
    text = ""
    page = 0
    while True:
        try:
            content = reader.getPage(page).extractText()
            text += content
            page += 1
        except:
            break
    
    ######## Extract just the abstract text
    text = text.split("\n\n")
    abstract = []
    cnt = 0
    # Loop for PDF's that have weird "\n \n" breaks
    if "\n \n" in " ".join(i for i in text):
        content = []
        for i in text:
            for j in i.split("\n \n"):
                content.append(re.sub("\n", "", j))
        while cnt < len(content):
            if "abstract" in content[cnt].lower():
                if "abstract" in content[cnt].lower() and len(text[cnt].split()) < 10:
                    cnt += 1
                while True:
                    if "introduction" in content[cnt].lower():
                        break
                    abstract.append(content[cnt])
                    cnt += 1
                break
            else:
                cnt += 1
    # Loop for all other PDF's
    else:
        while cnt < len(text):
            if "abstract" in text[cnt].lower():
                if "abstract" in text[cnt].lower() and len(text[cnt].split()) < 10:
                    cnt += 1
                while True:
                    if "*" in text[cnt] and len(text[cnt].split()) < 10:
                        cnt += 1
                    elif len(text[cnt].split()) > 10:
                        if "introduction" in text[cnt][:20].lower() or "i ntroduction" in text[cnt][:20].lower():
                            break
                        abstract.append(text[cnt])
                        cnt +=1
                    elif len(text[cnt].split()) == 1:
                        try:
                            int(text[cnt])
                        except:
                            break
                        break
                    else:
                        break
                break
            else:
                cnt += 1
        if not abstract:
            stop = 0
            while True:
                if "introduction" in text[stop].lower() and len(text[stop].split()) < 5:
                    break
                else:
                    stop += 1
            cnt = 0
            while cnt < stop:
                if text[cnt] == " " or len(text[cnt]) < 2:
                    if len(text[cnt+1].split()) < 10:
                        cnt += 1
                    else:
                        abstract.append(text[cnt+1])
                        if text[cnt+1][-1] == "-" or text[cnt+1][:-1] == "-":
                            while True:
                                if text[cnt+2][0].islower():
                                    abstract.append(text[cnt+2])
                                    break
                                else:
                                    cnt += 1
                cnt += 1
                
    ######## Format abstract text for presentation
    abstract_string = ""
    for a in abstract:
        a = a.strip()
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
    return abstract_string