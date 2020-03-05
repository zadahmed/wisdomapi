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
from nltk.corpus import stopwords 
from nltk.stem.wordnet import WordNetLemmatizer
from nltk import sent_tokenize
import gensim
from gensim import corpora
import pandas as pd
import numpy as np
# from easy_ocr import ocr_image
import cv2
import pytesseract
from pytesseract import Output
import os
import scholarly
from bs4 import BeautifulSoup
from mediawikiapi import MediaWikiAPI
from mediawiki import MediaWiki
from pysummarization.nlpbase.auto_abstractor import AutoAbstractor
from pysummarization.tokenizabledoc.simple_tokenizer import SimpleTokenizer
from pysummarization.abstractabledoc.top_n_rank_abstractor import TopNRankAbstractor
import arxiv
from dateutil import parser


pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


# global variables and functions
stop = set(stopwords.words("english"))
exclude = set(string.punctuation) 
lemma = WordNetLemmatizer()
avoid = "§‡¶@∗"
symbols = "ΔΩπϴλθ°αβγδεζηθικλμνξοπρςστυφχψωΓΔΘΛΞΠΣΦΨΩϴ∂γβ∈"
math = "≥∞<≤√=>+×"
mediawikiapi = MediaWikiAPI()
wikipedia = MediaWiki()

# Object of automatic summarization.
auto_abstractor = AutoAbstractor()
# Set tokenizer.
auto_abstractor.tokenizable_doc = SimpleTokenizer()
# Set delimiter for making a list of sentence.
auto_abstractor.delimiter_list = [".", "\n"]
# Object of abstracting and filtering document.
abstractable_doc = TopNRankAbstractor()

extras = ["et", "al", "le", "eg"]
for extra in extras:
    stop.add(extra)
    
extras = ["•", "−"]
for extra in extras:
    exclude.add(extra)

def clean(doc):
    stop_free = " ".join([i for i in doc.lower().split() if i not in stop])
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
    normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
    return normalized

def frequency_processor(corpus):
    all_text = corpus
    formatted_all_text = all_text.lower()
    formatted_all_text = re.sub(r'[^\w\s]',' ',formatted_all_text)
    formatted_all_text = " ".join(x for x in formatted_all_text.split() if x not in stop)
    all_text_sent = all_text
    # If there is no data
    if not formatted_all_text or not all_text:
        frequency = None
        return frequency
    # Otherwise
    sentence_list = sent_tokenize(all_text_sent)
    split_words = [f for f in formatted_all_text.split(" ") if len(f) > 2]
    frequency = pd.value_counts(split_words).reset_index()
    frequency.columns = ["words", "frequency"]
    frequency = frequency[frequency["words"] != "-"]
    frequency = frequency[frequency["words"] != "_"]
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

def summarisetext(text, key_points=5, complexity=5):
    # check if text exists
    if text:
        # Summarisation of top 5 key points
        sentence_length = complexity*30
        summary = []
        blob = TextBlob(text)
        sentences = [str(sentence) for sentence in blob.sentences]
        summary_dummy = []
        # clean up sentences
        for sent in sentences:
            try:
                if "•" in sent and ":" in sent:
                    sentence = re.sub("•", "", sent)
                    summary_dummy.append(sentence)
                elif "•" in sent[:3]:
                    sentence = re.sub("•", ".", sent)
                    summary_dummy.append(sentence)
                else:
                    summary_dummy.append(sent)
            except:
                pass
        # a bit more cleaning
        sentences = summary_dummy
        for sentence in sentences:
            try:
                if sentence.find(":", 0, 1) != -1 and sentence.find("-", 1, 3) != -1:
                    pass
                else:
                    if len(sentence)>2:
                        if len(sentence.split()) < sentence_length:
                            summary.append(sentence)
            except:
                pass
        # identify key points
        parser = PlaintextParser.from_string(' '.join(str(sentence) for sentence in summary), Tokenizer("english"))
        summarizer = TextRankSummarizer()
        doc_summary = summarizer(parser.document, key_points)
        doc_summary = [str(sentence) for sentence in doc_summary]
        summary = []
        for sent in doc_summary:
            try:
                summary.append("• "+sent)
            except:
                pass
        doc_summary = summary
    else:
        doc_summary = None
    return doc_summary

# Convolution kernels for OCR
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def remove_noise(image):
    return cv2.medianBlur(image,5)
 
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

def dilate(image):
    kernel = np.ones((5,5),np.uint8)
    return cv2.dilate(image, kernel, iterations = 1)
    
def erode(image):
    kernel = np.ones((5,5),np.uint8)
    return cv2.erode(image, kernel, iterations = 1)

def deskew(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated


# APIs
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
    try:
        if "https" in pdfurl:
            url = pdfurl.split("https:")
            if "//" != url[:2]:
                url = "https:/"+url[1]
                pdfurl = url
            else:
                pass
        elif "http" in pdfurl:
            url = pdfurl.split("http:")
            if "//" != url[:2]:
                url = "http:/"+url[1]
                pdfurl = url
            else:
                pass
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
    except:
        return "Unable to extract abstract text... try another document"
    try:
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
    except:
        return "Unable to extract abstract... try another document"
    try:
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
    except:
        return "Unable to format abstract... try another document"


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
    try:
        # get bytes stream of web pdf
        if "https" in pdfurl:
            url = pdfurl.split("https:")
            if "//" != url[1][:2]:
                url = "https:/"+url[1]
                pdfurl = url
            else:
                pass
        elif "http" in pdfurl:
            url = pdfurl.split("http:")
            if "//" != url[:2]:
                url = "http:/"+url[1]
                pdfurl = url
            else:
                pass 
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
        corpus = []
        for page in PDFPage.get_pages(fp=f, pagenos=pagenos, maxpages=0, caching=True, check_extractable=True):
            interpreter.process_page(page)
        text = retstr.getvalue()
        corpus.append(text)
        # close apps
        device.close()
        retstr.close()
        # join all text into string
        final_text = " ".join(i for i in corpus)
        final_text = re.sub("al.", "al", final_text)
        # remove citations 'cid'
        final_text = re.sub("\(cid:\d\d\d\)", "", final_text)
        final_text = re.sub("\(cid:\d\d\)", "", final_text)
        final_text = re.sub("\(cid:\d\)", "", final_text)
        # process into first pass sentences
        blob = TextBlob(final_text)
        sentences = [str(sentence) for sentence in blob.sentences]
        sentences = [s for s in sentences if len(s)>1]
        # remove figure text
        sentences = [s for s in sentences if not re.search('Fig', s)]
        # second pass of sentences
        sentences2 = []
        for sent in sentences:
            blob = TextBlob(sent)
            for s in blob.sentences:
                sentences2.append(str(s))
        sentences = sentences2
        # remove sentences with greek/foreign symbols
        no_symbols = []
        cnt = 0
        while cnt < len(sentences):
            counter = 0
            for symbol in symbols:
                if symbol in sentences[cnt]:
                    counter += 1
                    break
            if counter == 0:
                no_symbols.append(sentences[cnt])
            cnt += 1
        # remove sentences with math
        no_math = []
        cnt = 0
        while cnt < len(no_symbols):
            counter = 0
            for m in math:
                if m in no_symbols[cnt]:
                    counter += 1
                    break
            if counter == 0:
                no_math.append(no_symbols[cnt])
            cnt += 1
        # remove sentences with strange characters
        no_avoid = []
        cnt = 0
        while cnt < len(no_math):
            counter = 0
            for n in avoid:
                if n in no_math[cnt]:
                    counter += 1
                    break
            if counter == 0:
                no_avoid.append(no_math[cnt])
            cnt += 1
        # remove line breaks from remaining text
        main_text = " ".join(n for n in no_avoid)
        main_text = main_text.split("\n")
        main_text = [m.strip() for m in main_text]
        # remove text before abstract
        idx = 0
        cnt = 0
        for sent in main_text:
            if "Abstract" in sent or "ABSTRACT" in sent or "abstract" in sent:
                if len(sent.split()) < 3:
                    idx = cnt + 1
            else:
                cnt += 1
        main_text = main_text[idx:]
        # remove short leftover strings
        main_sent = []
        for m in main_text:
            if len(m)>5:
                main_sent.append(m)
        # identify references split text into main and references
        idx = 0
        cnt = 0
        for sent in main_sent:
            if "References" in sent or "REFERENCES" in sent or "Appendix" in sent or "APPENDIX" in sent or "Bibliogrpahy" in sent or "BIBLIOGRAPHY" in sent:
                idx = cnt
            cnt += 1
        if idx > 0:
            main_sent_wo_ref = main_sent[:idx]
            references = main_sent[idx:]
        else:
            main_sent_wo_ref = main_sent
            references = None
        # third pass of sentences to remove headers
        sentences3 = []
        for sent in main_sent_wo_ref:
            blob = TextBlob(sent)
            for s in blob.sentences:
                sentences3.append(str(s))
        sentences = sentences3
        # remove headers from text
        main_sent_wo_headers = []
        for sent in sentences:
            cnt = 0
            dummy = re.sub(r'[^\w\s]', '', sent)
            dummy = re.sub("\d", "", dummy)
            dummy = dummy.strip()
            for i in dummy.split():
                if i[0].isupper():
                    cnt += 1
            if len(dummy.split()) != 0:
                ratio = cnt/len(dummy.split())
                if ratio < 0.5:
                    main_sent_wo_headers.append(sent)
        # remove noise at start and end of sentences with blank sentences being concatenated
        main_sent_wo_headers = [m for m in main_sent_wo_headers if m[-2:] != " ."]
        main_sent_final = []
        for m in main_sent_wo_headers:
            if m[:2] == ". ":
                main_sent_final.append(m[2:])
            else:
                main_sent_final.append(m)
        # join all remaining sentences
        all_sentences = " ".join(m for m in main_sent_final)
        # fourth pass of sentences and keep only ones that start with capitalised letter
        blob = TextBlob(all_sentences)
        last_split = [str(sentence) for sentence in blob.sentences if sentence[0].isupper()]
        # join remaining text
        text = " ".join(s for s in last_split)
    except Exception as e:
        text = None
        print(e)
    # return text
    return text


def summarisepdfdocument(text, key_points=5, complexity=5):
    """
    Summarise PDF research document
    ------------------
    This function summarises the 5 key points from a PDF research document
    
    INPUT:
    - text (string): all extracted text from PDF research document
    - key_points (int), optional: number of key points to return as summary
    - complexity (int), optional: length of sentences to return in summary
    
    OUTPUT:
    - doc_summary (list): summary containing top 5 points from PDF document. Points are ranked by important, 1st = most important.
    
    """
    # check if text exists
    if text:
        # Summarisation of top 5 key points
        sentence_length = complexity*30
        summary = []
        blob = TextBlob(text)
        sentences = [str(sentence) for sentence in blob.sentences]
        summary_dummy = []
        # clean up sentences
        for sent in sentences:
            try:
                if "•" in sent and ":" in sent:
                    sentence = re.sub("•", "", sent)
                    summary_dummy.append(sentence)
                elif "•" in sent[:3]:
                    sentence = re.sub("•", ".", sent)
                    summary_dummy.append(sentence)
                else:
                    summary_dummy.append(sent)
            except:
                pass
        # a bit more cleaning
        sentences = summary_dummy
        for sentence in sentences:
            try:
                if sentence.find(":", 0, 1) != -1 and sentence.find("-", 1, 3) != -1:
                    pass
                else:
                    if len(sentence)>2:
                        if len(sentence.split()) < sentence_length:
                            summary.append(sentence)
            except:
                pass
        # identify key points
        parser = PlaintextParser.from_string(' '.join(str(sentence) for sentence in summary), Tokenizer("english"))
        summarizer = TextRankSummarizer()
        doc_summary = summarizer(parser.document, key_points)
        doc_summary = [str(sentence) for sentence in doc_summary]
        summary = []
        for sent in doc_summary:
            try:
                # remove word abstract from start of sentence if present
                if "abstract" in sent.lower():
                    if "abstract" in sent.lower()[:15]:
                        sentence = re.sub("abstract", "", sent)
                        sentence = re.sub("Abstract", "", sentence)
                        sentence = re.sub("ABSTRACT", "", sentence)
                        sentence = sentence.strip()
                        if sentence[0] in string.punctuation or sentence[0] == "—":
                            sentence = sentence[1:]
                            sentence = sentence.strip()
                        summary.append("• "+sentence)
                    else:
                        summary.append("• "+sent)
                else:
                    summary.append("• "+sent)
            except:
                pass
        doc_summary = summary
    else:
        doc_summary = None
    return doc_summary
    # if text:
    #     # summarize document.
    #     result_dict = auto_abstractor.summarize(text, abstractable_doc)
    #     summary = []
    #     for sentence in result_dict["summarize_result"]:
    #         summary.append(sentence)
    #     doc_summary = []
    #     for sent in summary:
    #         try:
    #             # remove word abstract from start of sentence if present
    #             if "abstract" in sent.lower():
    #                 if "abstract" in sent.lower()[:15]:
    #                     sentence = re.sub("abstract", "", sent)
    #                     sentence = re.sub("Abstract", "", sentence)
    #                     sentence = re.sub("ABSTRACT", "", sentence)
    #                     sentence = sentence.strip()
    #                     if sentence[0] in string.punctuation or sentence[0] == "—":
    #                         sentence = sentence[1:]
    #                         sentence = sentence.strip()
    #                     doc_summary.append("• "+sentence)
    #                 else:
    #                     doc_summary.append("• "+sent)
    #             else:
    #                 doc_summary.append("• "+sent)
    #         except:
    #             pass
    # else:
    #     doc_summary = None
    # return doc_summary


def topicsindocument(text):
    """
    Topical analysis of PDF research document
    ------------------
    This function extracts key topics within PDF research document
    
    INPUT:
    - text (string): all extracted text from PDF research document
    
    OUTPUT:
    - topics (list): list of up to 5 topics from document. Each topic consists of up to 5 words.
    
    """
    if text:
        # global variables
        num_topics = 5
        num_words = 5
        # normalize text
        topics = []
        try:
            text_normalized = clean(text).split()
            text_normalized = [[i for i in text_normalized if i not in stop]]
            # create document term matrix
            dictionary = corpora.Dictionary(text_normalized)
            doc_term_matrix = [dictionary.doc2bow(doc) for doc in text_normalized]
            # fit LDA model
            LDA = gensim.models.ldamodel.LdaModel
            LDA_fit = LDA(doc_term_matrix, num_topics=num_topics, id2word=dictionary, passes=300)
            # create list of topics and remove duplicates
            topics_list = [t for t in LDA_fit.print_topics(num_topics=-1, num_words=num_words)]
            for topic in topics_list:
                t = topic[1]
                topics.append(t)
            topics = set(topics)
            # clean up topics for presentation
            final_topics = []
            for topic in topics:
                t = topic.replace('"', '')
                t = t.split('*')[1:]
                t = [j.split(" + ")[0] for j in t]
                new_topic = []
                for j in t:
                    if j == ' ':
                        pass
                    elif j == '':
                        pass
                    else:
                        new_topic.append(j.strip())
                final_topics.append(new_topic)
            # format topics and return
            if final_topics[0][0] == "":
                final_topics = None
            else:
                final_topics = [' '.join(word for word in topic) for topic in final_topics]
            return final_topics
        except:
            return "Error when calculating topics..."
    else:
        return "Unable to extract topics, no text..."


def wordcloud(search_term, corpus):
    """
    Word cloud for summary of all research documents returned by ArXiv API
    ------------------
    This function creates a word cloud using the short summary of all the research
    documents returned from the ArXiv API.
    
    INPUT:
    - search_term (string): search term entered.
    - corpus (list): list of strings containing all the short summaries of the documents
                     returned by ArXiv API.   
    
    OUTPUT:
    - words (list): list containing top 10 words across documents and their weighting by tf_idf.
    
    """
    if corpus:
        # frequency processing
        frequency = frequency_processor(corpus)
        important_words = []
        if frequency is not None:
            try:
                # create dataframe of top N
                top_N = pd.DataFrame(frequency.groupby("lemmatized word")["tf_idf"].sum())
                top_N = top_N.sort_values(by=["tf_idf"], ascending=False)
                split = search_term.lower().split()
                counter1=0
                counter2=1
                #num_words = 10
                #while counter1<(num_words):
                    # word = top_N.index[counter1]
                    # value = top_N.values[counter1]
                    # important_words.append(word)
                    # counter1 += 1
                # remove words that are within search term
                num_words = 10
                while counter2<(num_words+1):
                    word = top_N.index[counter1]
                    value = top_N.values[counter1]
                    thresh=0
                    for i in split:
                        if i in word:
                            thresh+=1
                        else:
                            pass
                    if thresh>0:
                        counter1+=1
                    else:
                        important_words.append(word.capitalize())
                        counter1+=1
                        counter2+=1
                if important_words[0] == "":
                    important_words = None
                return important_words
            except:
                return "Error with word cloud..."
        else:
            return "Error with frequency processor..."
    else:
        return "Unable to find topics..."
    

def bringyourowndocument(img):
    """
    Extract text from your own document.
    ------------------
    Take a picture of your own document and extract text.
    
    INPUT:
    - filename (string): name of jpg file.  
    
    OUTPUT:
    - text (string): all text extracted from document.
    
    """
    try:
        # read image file
        #img = cv2.imread(filename)
        # Adding custom options
        custom_config = r'--oem 3 --psm 6'
        # process image to create binary mask
        gray = get_grayscale(img)
        no_noise = remove_noise(gray)
        eroded = erode(no_noise)
        dilated = dilate(eroded)
        deskewed = deskew(dilated)
        thresh = thresholding(deskewed)
        # switch colours of binary mask
        thresh[thresh == 255] = 128
        thresh[thresh == 0] = 255
        thresh[thresh == 128] = 0
        # get dimensions of original image
        height = thresh.shape[0]
        width = thresh.shape[1]
        middle_column = round(width/2)
        middle_row = round(height/2)
    except:
        return "Error when loading document... try another one"
    try:
        # calculate left boundary
        left = middle_column
        gap = 0
        cnt = 0
        tracker = 0
        exit = False
        while cnt < left:
            for i in range(middle_row, height):
                if tracker > 1000:
                    exit = True
                    break
                elif thresh[i][left] == 0:
                    gap += 1
                else:
                    tracker = gap
                    gap = 0
                    break
            if exit == True:
                break
            else:
                left -= 1
        # calculate right boundary
        right = middle_column
        gap = 0
        tracker = 0
        exit = False
        while right < width:
            for i in range(middle_row, height):
                if tracker > 1000:
                    exit = True
                    break
                elif thresh[i][right] == 0:
                    gap += 1
                else:
                    tracker = gap
                    gap = 0
                    break
            if exit == True:
                break
            else:
                right += 1
        # slice left and right side off
        if left > 50:
            left -= 50
        if right < width-50:
            right += 50
        crop_img = thresh[:height, left:right]
    except:
        return "Error finding vertical boundaries... try another one"
    try:
        # calculate top boundary
        end = crop_img.shape[0]
        cnt = 0
        top = end-1
        values = []
        while cnt < top:
            if sum(crop_img[cnt]) == 0:
                values.append(cnt)
            else:
                values.append(0)    
            cnt += 1
        idx = [i for i,x in enumerate(values) if x != 0]
        try:
            top = min(idx)
        except:
            top = 0
        # slice off the top
        crop_img = thresh[top:, left:right]
        # calculate the bottom boundary
        end = crop_img.shape[0]
        cnt = 0
        bottom = end-1
        values = []
        while cnt < bottom:
            if sum(crop_img[cnt]) == 0:
                values.append(cnt)
            else:
                values.append(0)    
            cnt += 1
        bottom = max(values)
        # final slice of the bottom
        crop_img = crop_img[:bottom, :]
        # switch colours back
        crop_img[crop_img == 255] = 128
        crop_img[crop_img == 0] = 255
        crop_img[crop_img == 128] = 0
    except:
        return "Error finding vertical boundaries... try another one"
    # try:
        # perform OCR on thresholded image to extract text
    text = pytesseract.image_to_string(thresh)
    #text = ocr_image(name, service='youdao')
    #text = " ".join(i for i in text)
    text = re.sub("-\n", "", text)
    text = re.sub("\n", " ", text)
    text = re.sub("- ", "", text)
    return text
    # except:
        # return "Error with extracting text... try another one"


def getarxivresults(search_term, quantity=10):
    """
    Get search page results for documents on ArXiv
    ------------------
    Return top N results from ArXiv based on search term
    
    INPUT:
    - search_term (string): topic being searched.
    - quantity (int), optional: number of documents to return
    
    OUTPUT:
    - papers (list):
        - titles (list): titles of papers
        - summary (list): abstract of document
        - date (string): formatted date
        - authors (string): formatted authors string
        - pdf_url (string): link to PDF of document
    
    """
    arxiv_results = arxiv.query(query=search_term,
                                id_list=[],
                                max_results=quantity,
                                start=0,
                                sort_by="relevance",
                                sort_order="descending",
                                prune=False,
                                iterative=False,
                                max_chunk_results=10)
    papers = []
    for paper in arxiv_results:
        # title
        title = paper['title_detail']['value']
        title = title.replace('\n', '')
        # abstract summary
        summary = paper['summary']
        summary = summary.replace('\n', ' ')
        # publish date
        publish_date = str(paper["published"])
        dt = parser.parse(publish_date)
        date = str(dt.strftime('%B')) + " " + str(dt.day) + ", " + str(dt.year)
        # authors
        authors_list = paper["authors"]
        authors = ""
        if len(authors_list) == 1:
            authors += authors_list[0]
        else:
            for idx, author in enumerate(authors_list):
                if idx == 0:
                    authors += author+","
                elif idx == len(authors_list)-1:
                    authors += " "+author
                else:
                    authors += " "+author+","
        # url
        pdf_url = paper['pdf_url']
        papers.append([title, summary, date, authors, pdf_url])
    return papers


def getgooglescholar(search_term, quantity=10):
    """
    Get search page results for docuements on Google Scholar
    ------------------
    Return top N results from Google Scholar based on search term
    
    INPUT:
    - search_term (string): topic being searched.
    - quantity (int), optional: number of documents to return
    
    OUTPUT:
    - titles (list): titles of papers
    - e_docs (list): links to e-documents
    - urls (list): links to document
    - abstracts (list): condensed abstracts of documents
    
    """
    try:
        # create generator containing results
        search_query = scholarly.search_pubs_query(search_term)
    except:
        return "Unable to find Google Scholar results..."
    try:
        # loop for 'quantity' and write results into lists
        papers = []
        cnt = 1
        for i in search_query:
            data = []
            if cnt > quantity:
                break
            else:
                result = next(search_query)
                #result = next(search_query).fill()
                # titles
                try:
                    data.append(result.bib['title'])
                except:
                    data.append("")
                # author
                try:
                    authors = result.bib["author"]
                    if " and " in authors:
                        all_authors = authors.split(" and ")
                        authors = ", ".join(a for a in all_authors)
                    data.append(authors)
                except:
                    data.append("")
                # cited_by
                try:
                    data.append(result.bib['citedby'])
                except:
                    data.append("")
                # e documents
                try:
                    data.append(result.bib['eprint'])
                except:
                    data.append("")
                # urls
                try:
                    data.append(result.bib['url'])
                except:
                    data.append("")
                # abstracts
                try:
                    data.append(result.bib['abstract'])
                except:
                    data.append("")
                cnt += 1
            papers.append(data)
        return papers
    except:
        return "Unable to collect Google Scholar results..."


def factualsearch(category, search_me):
    """
    Get factual definition of the Wisdom search term
    ------------------
    Get multiple definitions of the search term
    
    INPUT:
    - category (string): search category, e.g. topic, company, author...
    - search_me (string): search term
    
    OUTPUT:
    - results (dict): nested dictionary of data sources and results
    
    """
    # get factual search pages
    if category == "topic":
        pages = wikipedia.allpages(search_me)
        final_pages = []
        for page in pages:
            try:
                #categories = wikipedia.page(page).categories
                #scan = " ".join(c for c in categories).lower()
                #if search_me in page.lower() or search_me in scan:
                if search_me == page.lower() or search_me == re.sub(" ", "", page.lower()) or search_me[:-1] == page.lower() or search_me[:-1] == re.sub(" ", "", page.lower()):
                    final_pages.append(page)
            except:
                pass
    if category == "company":
        pages = wikipedia.allpages(search_me)
        final_pages = []
        #matches = ["establishm", "compan"]
        matches = ["compan"]
        for page in pages:
            try:
                categories = wikipedia.page(page).categories
                scan = " ".join(c for c in categories).lower()
                if search_me in page.lower():
                    for match in matches:
                        if match in scan:
                            final_pages.append(page)
                            break
            except:
                pass
    if category == "author":
        try:
            search_query = scholarly.search_author(search_me)
            # loop for 'quantity' and write results into lists
            name = []
            affiliation = []
            cited_by = []
            interests = []
            cnt = 0
            while cnt < 5:
                try:
                    result = next(search_query)
                    #result = next(search_query).fill()
                    # names
                    name_split = search_me.split()
                    dummy = 0
                    for n in name_split:
                        if n in result.name.lower():
                            dummy += 1
                    if dummy == len(name_split):
                        try:
                            name.append(result.name)
                        except:
                            name.append("")
                        # affiliations
                        try:
                            affiliation.append(result.affiliation)
                        except:
                            affiliation.append("")
                        # cited by
                        try:
                            cited_by.append(result.citedby)
                        except:
                            cited_by.append("")
                        # interests
                        try:
                            interests.append(result.interests)
                        except:
                            interests.append("")
                    cnt += 1
                except:
                    break
            results = [name, affiliation, cited_by, interests]
            return results
        except:
            results = "Couldn't find author..."
            return results
    # get wikipedia summaries
    if final_pages:
        # get results
        results = []
        for page in final_pages:
            text = wikipedia.page(page).summary
            key_points = summarisetext(text)
            summary = "\n\n".join(k for k in key_points)
            results.append([page, text, summary])
        return results
    else:
        results = "Couldn't find it... try one of these: "
        alternatives = wikipedia.allpages(search_me)
        for alt in alternatives:
            results += alt + ", "
        results = results[:-2]
        return results


def highlighter(word):
    """
    Highlight a word and return the definition
    ------------------
    Return definition of a word when highlighting
    
    INPUT:
    - word (string): word for definition search
    
    OUTPUT:
    - results (dict): dictionary of definitions
    
    """
    url = "https://wordsapiv1.p.mashape.com/words/"+word
    headers = {"x-rapidapi-host": "wordsapiv1.p.rapidapi.com", "x-rapidapi-key": "fd1f8ffa7bmsh11a27ed783e94dbp19198cjsn072eae335940"}
    r = requests.get(url, headers=headers)
    r = r.json()
    results = []
    try:
        definitions = r["results"]
        for d in definitions:
            data = {}
            # definition
            if "definition" in d:
                data["definition"] = d["definition"]
            else:
                data["definition"] = ""
            # synonyms
            if "synonyms" in d:
                data["synonyms"] = d["synonyms"]
            else:
                data["synonyms"] = ""
            # in category
            if "inCategory" in d:
                data["inCategory"] = d["inCategory"]
            else:
                data["inCategory"] = ""
            # has category
            if "hasCategories" in d:
                data["hasCategories"] = d["hasCategories"]
            else:
                data["hasCategories"] = ""
            # has types
            if "hasTypes" in d:
                data["hasTypes"] = d["hasTypes"]
            else:
                data["hasTypes"] = ""
            # derivation
            if "derivation" in d:
                data["derivation"] = d["derivation"]
            else:
                data["derivation"] = ""
            results.append(data)
        return results
    except:
        search_terms = mediawikiapi.search(word.lower())
        if search_terms:
            results = {}
            wiki_data = {}
            for term in search_terms:
                text = mediawikiapi.summary(term, sentences=1)
                wiki_data[term] = text
            results["wikipedia"] = wiki_data
        else:
            results = "Oops... couldn't find a definition!"
        return results


def getdoajarticles(search_term, quantity=10):
    """
    Get search page results for articles on DOAJ
    ------------------
    Return top N results from DOAJ based on search term
    
    INPUT:
    - search_term (string): topic being searched.
    - quantity (int), optional: number of documents to return
    
    OUTPUT:
    - titles (list): titles of papers
    - e_docs (list): links to e-documents
    - urls (list): links to document
    - abstracts (list): condensed abstracts of documents
    
    """
    try:
        headers = {"search_query": search_term, "page": "1", "pageSize": str(quantity)}
        r = requests.get("https://doaj.org/api/v1/search/articles/"+search_term,
                        headers=headers)
        data = r.json()
        results = data["results"]
        articles = []
        for doc in results:
            try:
                info = []
                # journal name
                if "journal" in doc["bibjson"]:
                    text = doc["bibjson"]["journal"]["title"]
                    clean_text = BeautifulSoup(text, "html.parser").text
                    info.append(clean_text)
                else:
                    info.append("")
                # article title
                if "title" in doc["bibjson"]:
                    text = doc["bibjson"]["title"]
                    clean_text = BeautifulSoup(text, "html.parser").text
                    info.append(clean_text)
                else:
                    info.append("")
                # abstract
                if "abstract" in doc["bibjson"]:
                    text = doc["bibjson"]["abstract"]
                    #cleaner = re.compile('<.*?>')
                    #clean_text = re.sub(cleaner, '', text)
                    clean_text = BeautifulSoup(text, "html.parser").text
                    info.append(clean_text)
                else:
                    info.append("")
                # keywords
                if "keywords" in doc["bibjson"]:
                    text = doc["bibjson"]["keywords"]
                    clean_text = BeautifulSoup(text, "html.parser").text
                    info.append(clean_text)
                else:
                    info.append("")
                # author
                if "author" in doc["bibjson"]:
                    authors = []
                    affiliations = []
                    for author in doc["bibjson"]["author"]:
                        authors.append(author["name"])
                        affiliations.append(author["affiliation"])
                    author_string = ", ".join(a for a in list(set(authors)))
                    info.append(author_string)
                    info.append(list(set(affiliations)))
                else:
                    info.append("")
                    info.append("")
                # url
                if "link" in doc["bibjson"]:
                    info.append(doc["bibjson"]["link"][0]["url"])
                else:
                    info.append("")
                # date created
                if "created_date" in doc:
                    publish_date = str(doc["created_date"])
                    dt = parser.parse(publish_date)
                    date = str(dt.strftime('%B')) + " " + str(dt.day) + ", " + str(dt.year)
                    info.append(date)
                else:
                    info.append("")
                # add to articles list
                articles.append(info)
            except:
                pass
        # return list of articles from DOAJ
        return articles
    except:
        return "Unable to collect DOAJ articles..."
        


  
            