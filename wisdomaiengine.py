# import packages
import io
import string
import requests
import re
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

def abstractextracter(pdfurl):
    """
    Abstract Extracter
    ------------------
    This function extracts the abstract from a pdf from a web link
    
    INPUT:
    - pdfurl (string): url of PDF
    
    OUTPUT:
    - abstract (string): abstract of PDF
    
    """
    # get bytes stream of web pdf
    r = requests.get(pdfurl, stream=True)
    f = io.BytesIO(r.content)
    # set up pdfminer
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    # extract abstract
    content = []
    for page in PDFPage.get_pages(f, caching=True, check_extractable=True):
        interpreter.process_page(page)
        text = retstr.getvalue()
        content.append(text)
        if "abstract" in text.lower():
            break
    # close apps
    device.close()
    retstr.close()
    # concatenate all text together
    whole_text = " ".join(t for t in content)
    # split text based on double line breaks
    text = whole_text.split("\n\n")
    cnt = 0
    abstract_string = ""
    keywords_string = ""
    # if "abstract" header in text, use this block to extract abstract and keywords
    if "abstract" in whole_text.lower():
        while cnt < len(text)-1:
            if "introduction" in text[cnt].lower():
                break
            if "abstract" in text[cnt].lower():
                if len(text[cnt].split()) < 2:
                    cnt += 1
                abstract_string += text[cnt]
                cnt += 1
                if "keywords" in whole_text.lower() or "key-words" in whole_text.lower() or "keyword" in whole_text.lower() or "key word" in whole_text.lower():
                    while True:
                        if "keywords" in text[cnt].lower() or "key-words" in text[cnt].lower() or "keyword" in text[cnt].lower() or "key word" in text[cnt].lower():
                            if len(text[cnt].split()) < 2:
                                cnt += 1
                            keywords_string += text[cnt]
                            if text[cnt].strip()[-1] in (",", ";") and text[cnt+1].lower() not in ("i", "i.", "1", "introduction"):
                                keywords_string += text[cnt+1]
                            break
                        else:
                            cnt += 1
                    break
                break
            cnt += 1
    # if "abstract" header does not exist, use this block to extract abstract and keywords
    if not abstract_string:
        stop = 0
        # find break point to stop at introduction
        while True:
            if "introduction" in text[stop].lower():
                break
            else:
                stop += 1
        cnt = 0
        # iterate through each line up to introduction
        while cnt < stop:
            # if keywords, put this in keywords variable
            if "keywords" in text[cnt].lower() or "key-words" in text[cnt].lower() or "keyword" in text[cnt].lower() or "key word" in text[cnt].lower():
                if len(text[cnt].split()) < 2:
                    cnt += 1
                keywords_string += text[cnt]
            # if a number or a short piece of redundant text
            elif len(text[cnt].split()) < 2:
                pass
            # if ocr has picked up annoying numebrs along side with many "\n"
            elif text[cnt].count("\n") >= 3:
                dummy = text[cnt].split("\n")
                dummy_cnt = 0
                for d in dummy:
                    if len(d)>1:
                        dummy_cnt += 1
                if dummy_cnt > 2:
                    abstract_string += text[cnt]+" " 
            else:
                abstract_string += text[cnt]+" "
            cnt += 1
    # block to clean up keywords if it has appended extra text to the start
    keywords_string_2 = ""
    if "\n" in keywords_string:
        keywords_dummy = keywords_string.split("\n")
        if "keywords" in keywords_dummy[0].lower() or "key-words" in keywords_dummy[0].lower() or "keyword" in keywords_dummy[0].lower() or "key word" in keywords_dummy[0].lower():
            pass
        else:
            cnt = 0
            while cnt < len(keywords_dummy):
                if "keywords" in keywords_dummy[cnt].lower() or "key-words" in keywords_dummy[cnt].lower() or "keyword" in keywords_dummy[cnt].lower() or "key word" in keywords_dummy[cnt].lower():
                    if len(keywords_dummy[cnt].split()) < 2:
                        cnt += 1
                    keywords_string_2 += keywords_dummy[cnt]
                cnt += 1
            keywords_string = keywords_string_2
    # format abstract to present to user
    abstract = ""
    abstract = re.sub("-\n", "", abstract_string)
    abstract = re.sub("\n", " ", abstract)
    # remove word 'abstract' and date at start
    if "abstract" in abstract[:8].lower():
        abstract = abstract[8:]
    dummy1 = abstract.split(". ")
    dummy2 = abstract.split()
    if "abstract" in dummy1[0].lower():
        cnt = 0
        while True:
            if "abstract" not in dummy2[cnt].lower().strip():
                cnt += 1
            else:
                cnt += 1
                break
        abstract = " ".join(word for word in dummy2[cnt:])
    if abstract[:1] in string.punctuation or abstract[:1] == "—":
        abstract = abstract[1:]
    abstract = abstract.strip()
    abstract = re.sub("  ", " ", abstract)
    # clean up and return abstract
    return abstract

