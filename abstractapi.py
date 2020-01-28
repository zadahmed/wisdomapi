# imports
import textract
import string
import re
from pathlib import Path
import requests
import os
import pytesseract
from wand.image import Image


def abstractextracter(pdfurl):
    # download pdf from url
    url_name = pdfurl.split("/")[-1]
    if ".pdf" not in url_name:
        pdf = Path(url_name+".pdf")
    pdf = Path(url_name)
    response = requests.get(pdfurl)
    pdf.write_bytes(response.content)
    # extract text and stop after abstract
    text = ""
    # Iterate through all the pages stored above 
    with(Image(filename=pdf, resolution=300)) as source: 
        for i, image in enumerate(source.sequence):
            Image(image).save(filename="temp.jpg")
            out = pytesseract.image_to_string("temp.jpg")
            text += out
            os.remove("temp.jpg")
            # stop when abstract has been found
            if "abstract" in out.lower():
                break
    # split at double breaks
    text = text.split("\n\n")
    # collect abstract text
    abstract = []
    cnt = 0
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
    # clean up and return abstract
    os.remove(pdf)
    return abstract_string