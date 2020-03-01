###########
# IMPORTS #
###########


import wptools
import arxiv
from flask import Flask, request, jsonify, render_template
import os
import wisdomaiengine
from urllib.parse import unquote
import pymongo
from io import BytesIO
import sys
from datetime import datetime
import base64
from PIL import Image
import numpy as np
import cv2
from dateutil import parser
import requests


##########################
# INSTANTIATE FLASK & DB #
##########################

app = Flask(__name__)
dir = os.path.abspath(os.path.dirname(__file__)) #  Directory
# user and pwd need to be environment variable os.environ["MONGO_DB_USER"]
user = "admin"
pwd = "admin123"
# connect to db
try:
    client = pymongo.MongoClient("mongodb://"+user+":"+pwd+"@localhost:27017/")
    db = client["wisdomdb"]
    print("connected to mongodb successfully!")
except:
    print("Unable to connect to database")
    sys.exit(1)
# instantiate collections
try:
    db_users = db["users"]
    db_searches = db["searches"]
    db_search_terms = db["search_terms"]
    db_byod = db["byod"]
    db_highlights = db["highlights"]
    db_wikipedia = db["wikipedia"]
    db_arxiv = db["arxiv"]
except:
    print("Unable to connect to collections")
    sys.exit(1)


##########
# ROUTES #
##########

# landing page
@app.route('/', methods=['GET'])
def home():
    return render_template("index.html")


########
# APIs #
########

# wisdom engine
@app.route('/wisdom/<string:search_me>/<path:pdfurl>', methods=['GET'])
def wisdom(search_me, pdfurl):
    search_me = search_me.strip()
    # check if pdfurl has been found before
    pdf = db_arxiv.find_one({"url": pdfurl})
    if pdf:
        text = pdf.get('text')
        summary = pdf.get('summary')
        topics = pdf.get('topics')
        # update in db if data is 7 days or older
        last_updated = datetime.utcnow() - pdf.get("last_updated")
        last_updated_diff = last_updated.days
        if last_updated_diff > 7:
            search_term = db_search_terms.find_one({"value": search_me.lower()})
            search_id = search_term.get("_id")
            data = {"search_id": search_id, "url": pdfurl, "text": text,
                    "summary": summary, "topics": topics, "last_updated": datetime.utcnow()}
            db_arxiv.update({"url": pdfurl}, {"$set": data})
        else:
            pass
    else:
        text = wisdomaiengine.pdfdocumentextracter(pdfurl)
        summary = wisdomaiengine.summarisepdfdocument(text)
        topics = wisdomaiengine.wordcloud(search_me, text)
        if topics is None:
            topics = ['No Topics Found']
        # write data to arxiv collection
        #search_term = db_search_terms.find_one({"value": search_me.lower()})
        #search_id = search_term.get("_id")
        #data = {"search_id": search_id, "url": pdfurl, "text": text,
        #        "summary": summary, "topics": topics, "last_updated": datetime.utcnow()}
        #x = db_arxiv.insert(data, check_keys=False)
    summaryjson = jsonify(wisdomtopics=topics,
                          wisdomsummary=summary)
    return summaryjson

# search
@app.route('/search/<string:category>/<string:search_me>', methods=['GET'])
def search(category, search_me):
    search_me = search_me.strip()
    # get wikipedia
    try:
        # see if it is saved in db
        search_term = db_search_terms.find_one({"value": search_me.lower()})
        if search_term:
            search_id = search_term.get("_id")
            wiki = db_wikipedia.find_one({"search_id": search_id})
            if wiki:
                wiki_def = wiki.get('wiki_summary')
        # if not, use mediawiki API
        else:
            wiki_def = wisdomaiengine.factualsearch(category, search_me.lower())
            # summarise into 5 bullet points
            #wiki_key_points = wisdomaiengine.summarisepdfdocument(wiki_def["wikipedia"])
    except:
        wiki_def = "Oops... couldn't find {}!".format(search_me)
        #wiki_key_points = ""

    research_papers = {}
    # get arxiv results
    try:
        arxiv_results = arxiv.query(query=search_me.lower(), id_list=[],
                             max_results=10, start = 0, sort_by="relevance",
                             sort_order="descending", prune=False,
                             iterative=False, max_chunk_results=10)
        papers = []
        all_papers = []
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
            all_papers.append(summary)
        research_papers["arxiv"] = papers
    except:
        research_papers["arxiv"] = ""

    # get google scholar results
    try:
        google_scholar = wisdomaiengine.getgooglescholar(search_me.lower())
        research_papers["google scholar"] = google_scholar
        for paper in google_scholar:
            all_papers.append(paper[-1])
    except:
        research_papers["google scholar"] = ""

    # get DOAJ articles
    try:
        doaj = wisdomaiengine.getdoajarticles(search_me.lower())
        research_papers["DOAJ"] = doaj
        for article in doaj:
            all_papers.append(article[2])
    except:
        research_papers["DOAJ"] = ""

    # get wordcloud of all papers
    try:
        all_papers_text = " ".join(a for a in all_papers)
        wordcloud = wisdomaiengine.wordcloud(search_me, all_papers_text)
    except:
        wordcloud = "No topics found!..."
    # check if search_term has been run before
    #results = db_search_terms.find_one({"value": search_me.lower()})
    #if results:
    #    search_id = results.get('_id')
    #else:
        # write data to search_terms collection
    #    data = {"value": search_me.lower()}
        #search_id = db_search_terms.insert(data, check_keys=False)
    # write data to searches collection
    #data = {"search_id": search_id, "datetime": datetime.utcnow()}
    #x = db_searches.insert(data, check_keys=False)
    # save data to wikipedia collection
    #wiki = db_wikipedia.find_one({"search_id": search_id})
    # if wiki:
    #     # update in db if data is 7 days or older
    #     last_updated = datetime.utcnow() - wiki.get("datetime")
    #     last_updated_diff = last_updated.days
    #     if last_updated_diff > 1:
    #         data = {"search_id": search_id, "wiki_summary": wiki_def,
    #                 #"wiki_key_points": wiki_key_points, 
    #                 "datetime": datetime.utcnow()}
    #         db_wikipedia.update({"search_id": search_id}, {"$set": data})
    #     else:
    #         pass
    # else:
    #     data = {"search_id": search_id,
    #             "wiki_summary": wiki_def, 
    #             #"wiki_key_points": wiki_key_points, 
    #             "datetime": datetime.utcnow()}
        #x = db_wikipedia.insert(data, check_keys=False)
    # return json object
    jsonob = jsonify(search=search_me,
                     summary=wiki_def, 
                     #key_points=wiki_key_points,
                     papers=research_papers,
                     wordcloud=wordcloud)
    return jsonob

# bring your own document
@app.route('/byod/<string:content_type>', methods=['GET' , 'POST'])
def byod(content_type):
    if request.method == "GET":
        print('Hi')
    if request.method == "POST":
        if content_type == "gallery":
            data = request.form.get('image')
            nparr = np.fromstring(base64.b64decode(data), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            text = wisdomaiengine.bringyourowndocument(img)
            jsonob = jsonify(img=text)
            return jsonob
        if content_type == "camera":
            return None
        if content_type == "webpage":
            page = request.form.get('data')
            r = requests.get(page)
            html = r.text
            soup = BeautifulSoup(html, 'html.parser')
            #soup = BeautifulSoup(html, 'lxml')
            body = soup.body
            # remove footer
            while body.footer:
                soup.footer.decompose()
            # remove scripts
            while body.script:
                soup.script.decompose()
            # get p tags
            main_body = body.find_all(["p"])
            text = ""
            for m in main_body:
                text += m.get_text()+" "
            text = text.strip()
            jsonob = jsonify(text=text)
            return jsonob


@app.route('/highlight/<string:word>')
def highlight(word):
    word = word.strip()
    results = wisdomaiengine.highlighter(word)
    jsonob = jsonify(results=results)
    return jsonob

                                                                                       
# run server
if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, port=5000)
