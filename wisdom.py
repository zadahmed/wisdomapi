###########
# IMPORTS #
###########

import os
import wptools
import arxiv
from flask import Flask , request , jsonify
import os
import wisdomaiengine
from urllib.parse import unquote
import pymongo
#from pymongo import Binary
import sys
from datetime import datetime

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
@app.route('/wisdom/<path:pdfurl>', methods=['GET'])
def wisdom(pdfurl):
    # check if pdfurl has been found before
    pdf = db_arxiv.find_one({"url": pdfurl})
    if pdf:
        text = pdf.get('text')
        abstract = pdf.get('abstract')
        summary = pdf.get('summary')
        topics = pdf.get('topics')
    else:
        text = wisdomaiengine.pdfdocumentextracter(pdfurl)
        abstract = wisdomaiengine.abstractextracter(pdfurl)
        summary = wisdomaiengine.summarisepdfdocument(text)
        topics = wisdomaiengine.wordcloud(text)
        if topics is None:
            topics = ['No Topics Found']
        # write data top arxiv collection
        data = {"url": pdfurl, "text": text, "abstract": abstract, "summary": summary, "topics": topics, "last_updated": datetime.utcnow()}
        x = db_arxiv.insert(data)
    summaryjson = jsonify(wisdomtopics=topics, wisdomabstract=abstract, wisdomsummary=summary)
    return summaryjson

# search
@app.route('/search/<string:search_me>', methods=['GET'])
def search(search_me):
    page = wptools.page(search_me.lower())
    r = page.get()
    f_what_summary = r.data['extext']
    result = arxiv.query(query=search_me,
                            id_list=[],
                            max_results=10,
                            start = 0,
                            sort_by="relevance",
                            sort_order="descending",
                            prune=False,
                            iterative=False,
                            max_chunk_results=10)
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
    jsonob = jsonify(search= search_me , summary= f_what_summary , papers= papers ,wordcloud = wordcloud )
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
    return jsonob
                                                                                                                                                                                                   
# bring your own document
@app.route('/wisdom/byod/<string:img_location>', methods=['GET'])
def byod(img_location):
    # save img from local device to Wisdom db
    #binary_img = Binary(img_location)
    #data = {"document_name": "name", "binary_image": binary_img, "datetime": datetime.utcnow()}
    #x = byod.insert_one(data)
    # get image from db
    #img_id = x.inserted_id
    #image = byod.findOne({"_id": img_id})
    # run through engine
    text = wisdomaiengine.bringyourowndocument(image)
    summary = wisdomaiengine.summarisepdfdocument(text)
    topics = wisdomaiengine.wordcloud(text)
    return text, summary, topics
                                                                                                
# run server
if __name__ == '__main__':
    app.run(host='0.0.0.0',threaded=True, port=5000)
