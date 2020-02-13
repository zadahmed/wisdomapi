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
from easy_ocr import ocr_image
import cv2
import pytesseract
from pytesseract import Output
import os
import scholarly


# global variables and functions
stop = set(stopwords.words("english"))
exclude = set(string.punctuation) 
lemma = WordNetLemmatizer()
escapes = "ΔΩπϴλθ°îĵk̂ûαβγδεζηθικλμνξοπρςστυφχψωΓΔΘΛΞΠΣΦΨΩϴ≤="

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
    all_text = ' '.join(i[0] for i in corpus)
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
    except:
        return "Unable to extract all text... try another document"
    try:
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
    except:
        print("Error when cleaning text: ", pdfurl)
    try:
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
    except:
        print("Error when identifying abstract: ", pdfurl)
    try:
        # identify references
        cnt = 0
        while True:
            if "References" in text[cnt] or "Appendix" in text[cnt] or "Bibliography" in text[cnt] or "REFERENCES" in text[cnt] or "acknowledgements" in text[cnt] or "ACKNOWLEDGEMENTS" in text[cnt]:
                if len(text[cnt].split()) < 3:
                    break
                if "\n" in text[cnt]:
                    break
            else:
                break
            cnt += 1
        if cnt == 0:
            text = text
        else:
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
    except:
        print("Error when identifying references: ", pdfurl)
    try:
        # remove headers
        clean2 = []
        cnt = 0
        while cnt < len(clean1)-1:
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
    except:
        print("Error when removing headers: ", pdfurl)
    try:
        # remove figure captions
        clean3 = []
        cnt = 0
        while cnt < len(clean2):
            if re.match('^Fig', clean2[cnt]) or re.match('^fig.', clean2[cnt].lower()) :
                pass
            else:
                clean3.append(clean2[cnt])
            cnt += 1
    except:
        print("Error when removing figrue captions: ", pdfurl)
    try:
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
    except:
        print("Error when removing table data: ", pdfurl)
    # remove superscripts
    try:
        clean5 = []
        for c in clean4:
            dummy = re.sub("  ", " ", c)
            # remove .X-Y superscripts
            if re.search(".\d-\d", dummy):
                text = re.sub(".\d-\d", "", dummy)
            else:
                text = dummy
            # remove X,Y mid sentence superscripts
            if re.search("\w\d,\d \w", text):
                text = re.sub("\d,\d", "", text)
            else:
                text = text
            # remove X,Y end of sentence superscripts
            if re.search("\w.\d,\d \w", text):
                text = re.sub("\d,\d", "", text)
            else:
                text = text
            # remove superscripts at end of sentence
            if re.search(".\d [A-Z]", text):
                text = re.sub(".\d ", ". ", text)
            elif re.search(".\d\d [A-Z]", text):
                text = re.sub(".\d\d ", ". ", text)
            else:
                text = text
            # remove mid sentence superscripts
            if re.search("\w\d \w", text):
                text = re.sub("\d ", "", text)
            else:
                text = text
            clean5.append(text)
    except:
        print("Error removing superscripts")
        clean5 = clean4
    try:
        # remove citations
        clean6 = " ".join(c for c in clean5)
        clean6 = re.sub("\(cid:\d\d\)", "", clean6)
        clean6 = re.sub("\(cid:\d\)", "", clean6)
        clean6 = re.sub("cid:", "", clean6)
        clean6 = re.sub("cid", "", clean6)
        clean6 = re.sub("\(\d\)", "", clean6)
        clean6 = re.sub("\(\d\d\)", "", clean6)
        clean6 = re.sub("^\[\d\]", "", clean6)
        clean6 = re.sub("^\[\d\d\]", "", clean6)
        clean6 = re.sub("^\[\d\d\]", "", clean6)
        clean6 = re.sub("-\n", "", clean6)
        clean6 = re.sub("\n", " ", clean6)
        clean6 = re.sub("  ", " ", clean6)
        # remove math and Figure text
        blob = TextBlob(clean6)
        sentences = [str(sentence) for sentence in blob.sentences]
        # remove sentences with math
        no_math = []
        for sentence in sentences:
            cnt = 0
            for symbol in escapes:
                if symbol in sentence:
                    cnt += 1
            if cnt == 0:
                no_math.append(sentence)
        # remove sentences with "Figure X:" or "Fig X:""
        no_figs = []
        for sentence in no_math:
            if re.search("Figure \d:", sentence):
                pass
            elif re.search("Fig. \d:", sentence):
                pass
            elif re.search("Fig \d:", sentence):
                pass
            else:
                no_figs.append(sentence)
        text = " ".join(n for n in no_figs)
    except:
        print("Error when removing citations and math: ", pdfurl)
    # removing final equations that are leftover as numbers
    final_sentences = []
    blob = TextBlob(text)
    sentences = [str(sentence) for sentence in blob.sentences]
    for sent in sentences:
        if re.search("\(\d\d\d\d\)", sent):
            pass
        else:
            final_sentences.append(sent)
    text = " ".join(f for f in final_sentences)
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
    return doc_summary


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
                        important_words.append(word)
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
    

def bringyourowndocument(filename):
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
        img = cv2.imread(filename)
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
    try:
        # perform OCR on thresholded image to extract text
        text = pytesseract.image_to_string(crop_img)
        #text = ocr_image(name, service='youdao')
        #text = " ".join(i for i in text)
        text = re.sub("-\n", "", text)
        text = re.sub("\n", " ", text)
        text = re.sub("- ", "", text)
        return text
    except:
        return "Error with extracting text... try another one"


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
        titles = []
        e_docs = []
        urls = []
        abstracts = []
        cnt = 1
        for i in search_query:
            if cnt > quantity:
                break
            else:
                result = next(search_query)
                #result = next(search_query).fill()
                # titles
                try:
                    result.bib['title']
                    titles.append(result.bib['title'])
                except:
                    titles.append("")
                # e documents
                try:
                    result.bib['eprint']
                    e_docs.append(result.bib['eprint'])
                except:
                    e_docs.append("")
                # urls
                try:
                    result.bib['url']
                    urls.append(result.bib['url'])
                except:
                    urls.append("")
                # abstracts
                try:
                    result.bib['abstract']
                    abstracts.append(result.bib['abstract'])
                except:
                    abstracts.append("")
                cnt += 1
        return titles, e_docs, urls, abstracts
    except:
        return "Unable to collect Google Scholar results..."

