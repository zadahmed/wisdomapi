# import packages
import io
import string
import requests
import re
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from textblob import TextBlob
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

def abstractextracter(pdfurl):
    """
    Abstract extracter
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
        if "abstract" in retstr.getvalue().lower():
            break
    text = retstr.getvalue()
    content.append(text)
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


def pdfdocumentextracter(pdfurl):
    """
    Extract all text from PDF research document
    ------------------
    This function extracts and cleans all text from a PDF document
    
    INPUT:
    - pdfurl (string): url of PDF
    
    OUTPUT:
    - text (string): all text from PDF
    
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
    pagenos=set()
    # extract all text
    content = []
    for page in PDFPage.get_pages(fp=f, pagenos=pagenos, maxpages=0, caching=True, check_extractable=True):
        interpreter.process_page(page)
    text = retstr.getvalue()
    content.append(text)
    # close apps
    device.close()
    retstr.close()
    # remove noise and numbers at side of document
    text = []
    splits = content[0].split("\n\n")
    for chunk in splits:
        # if ocr has picked up annoying numbers along side with many "\n"
        if chunk.count("\n") >= 3:
            dummy = chunk.split("\n")
            dummy_cnt = 0
            for d in dummy:
                if len(d)>1:
                    dummy_cnt += 1
            if dummy_cnt > 2:
                text.append(chunk)
        else:
            text.append(chunk)
    # identify abstract
    if "abstract" in " ".join(i for i in text).lower():
        cnt = 0
        while True:
            if "abstract" in text[cnt].lower():
                if len(text[cnt].split()) < 2:
                    cnt += 1
                    break
                else:
                    if re.match("^abstract", text[cnt][:8].lower()):
                        text[cnt] = text[cnt][8:]
                    break
            cnt += 1
        text = text[cnt:]
    # identify references
    cnt = 0
    while True:
        if "References" in text[cnt] or "Appendix" in text[cnt] or "Bibliography" in text[cnt] or "REFERENCES" in text[cnt] or "acknowledgements" in text[cnt] or "ACKNOWLEDGEMENTS" in text[cnt]:
            if len(text[cnt].split()) < 3:
                break
            if "\n" in text[cnt]:
                break
        cnt += 1
    text = text[:cnt]
    # remove equation number references
    clean1 = []
    for t in text:
        if len(t.split()) == 1:
            if re.match("^\(\d\)", t):
                pass
            if re.match("\d", t):
                pass
        elif len(t.split()) == 0:
            pass
        else:
            clean1.append(t)
    # remove headers
    clean2 = []
    cnt = 0
    while cnt < len(clean1):
        if len(clean1[cnt].split()) < 10:
            dummy = re.sub("\d", "", clean1[cnt])
            dummy = dummy.strip()
            if len(dummy.split()) <= 1:
                pass
            elif dummy[-1] not in string.punctuation:
                dummy2 = re.sub("\d", "", clean1[cnt+1])
                dummy2 = re.sub('[^\w\s]','', dummy2)
                dummy2 = dummy2.strip()
                if dummy2:
                    if dummy2[0].isupper():
                        pass
                    else:
                        clean2.append(clean1[cnt])
                else:
                    pass
            else:
                clean2.append(clean1[cnt])
        else:
            clean2.append(clean1[cnt])
        cnt += 1
    # remove figure captions
    clean3 = []
    cnt = 0
    while cnt < len(clean2):
        if re.match('^Fig', clean2[cnt]) or re.match('^fig.', clean2[cnt].lower()) :
            pass
        else:
            clean3.append(clean2[cnt])
        cnt += 1
    # remove table data
    clean4 = []
    cnt = 0
    while cnt < len(clean3)-1:
        if clean3[cnt][-1] == ".":
            if re.sub("\d", "", clean3[cnt+1]).strip()[0].islower():
                pass
            else:
                clean4.append(clean3[cnt])
        elif clean3[cnt][-1] == "-" or clean3[cnt][-1] == "-":
            if clean3[cnt+1][0].islower():
                clean4.append(clean3[cnt])
            else:
                pass
        elif "©" in clean3[cnt]:
            pass
        else:
            clean4.append(clean3[cnt])
        cnt += 1
    # remove citations
    clean5 = " ".join(c for c in clean4)
    clean5 = re.sub("^\[\d\]", "", clean5)
    clean5 = re.sub("^\[\d\d\]", "", clean5)
    clean5 = re.sub("^\[\d\d\]", "", clean5)
    clean5 = re.sub("-\n", "", clean5)
    clean5 = re.sub("\n", " ", clean5)
    clean5 = re.sub("  ", " ", clean5)
    # return text
    text = clean5
    return text


def summarisepdfdocument(text):
    """
    Summarise PDF research document
    ------------------
    This function summarises the 5 key points from a PDF research document
    
    INPUT:
    - text (string): all extracted text from PDF research document
    
    OUTPUT:
    - doc_summary (list): summary containing top 5 points from PDF document. Points are ranked by important, 1st = most important.
    
    """
    # Summarisation of top 5 key points
    key_points = 5
    summary = []
    blob = TextBlob(text)
    sentences = [str(sentence) for sentence in blob.sentences]
    for sentence in sentences:
        if sentence.find(":", 0, 1) != -1 and sentence.find("-", 1, 3) != -1:
            pass
        else:
            if len(sentence)>2:
                if len(sentence.split()) < 150:
                    summary.append(sentence)
    parser = PlaintextParser.from_string(' '.join(str(sentence) for sentence in summary), Tokenizer("english"))
    summarizer = TextRankSummarizer()
    doc_summary = summarizer(parser.document, key_points)
    doc_summary = [str(sentence) for sentence in doc_summary]
    return doc_summary
    