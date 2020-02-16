###########
# IMPORTS #
###########


import wptools
import arxiv
from flask import Flask, request, jsonify
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
    return jsonify({'msg':'Hello World'})

# wisdom engine
@app.route('/wisdom/<string:search_me>/<path:pdfurl>', methods=['GET'])
def wisdom(search_me, pdfurl):
    # check if pdfurl has been found before
    pdf = db_arxiv.find_one({"url": pdfurl})
    if pdf:
        text = pdf.get('text')
        abstract = pdf.get('abstract')
        summary = pdf.get('summary')
        topics = pdf.get('topics')
        # update in db if data is 7 days or older
        last_updated = datetime.utcnow() - pdf.get("last_updated")
        last_updated_diff = last_updated.days
        if last_updated_diff > 7:
            search_term = db_search_terms.find_one({"value": search_me.lower()})
            search_id = search_term.get("_id")
            data = {"search_id": search_id, "url": pdfurl, "text": text, "abstract": abstract,
                    "summary": summary, "topics": topics, "last_updated": datetime.utcnow()}
            db_arxiv.update({"url": pdfurl}, {"$set": data})
        else:
            pass
    else:
        text = wisdomaiengine.pdfdocumentextracter(pdfurl)
        abstract = wisdomaiengine.abstractextracter(pdfurl)
        summary = wisdomaiengine.summarisepdfdocument(text)
        topics = wisdomaiengine.wordcloud(text)
        if topics is None:
            topics = ['No Topics Found']
        # write data to arxiv collection
        search_term = db_search_terms.find_one({"value": search_me.lower()})
        search_id = search_term.get("_id")
        data = {"search_id": search_id, "url": pdfurl, "text": text, "abstract": abstract,
                "summary": summary, "topics": topics, "last_updated": datetime.utcnow()}
        x = db_arxiv.insert(data)
    summaryjson = jsonify(wisdomtopics=topics, wisdomabstract=abstract, wisdomsummary=summary)
    return summaryjson

# search
@app.route('/search/<string:search_me>', methods=['GET'])
def search(search_me):
    # get wikipedia
    try:
        # see if it is saved in db
        search_term = db_search_terms.find_one({"value": search_me.lower()})
        if search_term:
            search_id = search_term.get("_id")
            wiki = db_wikipedia.find_one({"search_id": search_id})
            if wiki:
                what_summary = wiki.get('wiki_summary')
        # if not, use wiki API
        else:
            page = wptools.page(search_me.lower())
            r = page.get()
            what_summary = r.data['extext']
    except:
        what_summary = "Couldn't find Wikipedia page!..."
    # get arxiv results
    try:
        result = arxiv.query(query=search_me.lower(), id_list=[],
                             max_results=10, start = 0, sort_by="relevance",
                             sort_order="descending", prune=False,
                             iterative=False, max_chunk_results=10)
    except:
        result = None
    # get wordcloud
    if result:
        papers = []
        wordpapers = []
        for paper in result:
            title = paper['summary']
            title = title.replace('\n', ' ')
            value = paper['title_detail']['value']
            value = value.replace('\n', ' ')
            pdf_url = paper['pdf_url']
            papers.append([title,value,pdf_url])
            wordpapers.append(title)
        wordpapers = " ".join(w for w in wordpapers)
        wordcloud = wisdomaiengine.wordcloud(wordpapers)
    else:
        wordcloud = "No topics found!..."
    # check if search_term has been run before
    results = db_search_terms.find_one({"value": search_me.lower()})
    if results:
        search_id = results.get('_id')
    else:
        # write data to search_terms collection
        data = {"value": search_me.lower()}
        search_id = db_search_terms.insert(data)
    # write data to searches collection
    data = {"search_id": search_id, "datetime": datetime.utcnow()}
    x = db_searches.insert(data)
    # save data to wikipedia collection
    wiki = db_wikipedia.find_one({"search_id": search_id})
    if wiki:
        # update in db if data is 7 days or older
        last_updated = datetime.utcnow() - wiki.get("datetime")
        last_updated_diff = last_updated.days
        if last_updated_diff > 7:
            data = {"search_id": search_id, "wiki_summary": what_summary,
                    "datetime": datetime.utcnow()}
            db_wikipedia.update({"search_id": search_id}, {"$set": data})
        else:
            pass
    else:
        data = {"search_id": search_id, "wiki_summary": what_summary,
                "datetime": datetime.utcnow()}
        x = db_wikipedia.insert(data)
    # return json object
    jsonob = jsonify(search=search_me, summary=what_summary, papers=papers,
                     wordcloud=wordcloud)
    return jsonob

# bring your own document
@app.route('/byod', methods=['GET' , 'POST'])
def byod():
    if request.method == "GET":
        print('Hi')
    if request.method == "POST":
        data = request.form.get('image')
        with open(data, "rb") as f:
            imgdata = f.read()
        f.close()
        jpg_as_np = np.frombuffer(imgdata, dtype=np.uint8)
        img = cv2.imdecode(jpg_as_np, flags=1)
        text = wisdomaiengine.bringyourowndocument(img)
        #imgdata = base64.b64decode(data)
        #image = Image.open(BytesIO(imgdata))
        #print(image.format)
        #text = wisdomaiengine.bringyourowndocument(image)
        jsonob = jsonify(img=text)
        return jsonob
                                                                                                
# run server
if __name__ == '__main__':
    app.run(host='0.0.0.0',threaded=True, port=5000)
