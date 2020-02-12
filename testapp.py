import os
import wptools
import arxiv
from flask import Flask , request , jsonify
import os
import wisdomaiengine
from urllib.parse import unquote
import pymongo
from pymongo import Binary
import sys
from datetime import datetime

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
    print("Unable to conenct to database")
    sys.exit(1)

# instantiate collections
try:
    users = db["users"]
    searches = db["searches"]
    search_terms = db["search_terms"]
    byod = db["byod"]
    highlights = db["highlights"]
    wikipedia = db["wikipedia"]
    arxiv = db["arxiv"]
except:
    print("Unable to connect to collections")
    sys.exit(1)

    
# home
@app.route('/',methods = ['GET'])
def home():
    return jsonify({'msg':'Hello World'})

# abstract
@app.route('/wisdom/abstract/<path:pdfurl>',methods=['GET'])
def wisdomabstract(pdfurl ):
    print(pdfurl)
    results = arxiv.findOne({"url": pdfurl})
    if results:
        abstract = results.abstract
        topics = result.topics
    else:
        text = wisdomaiengine.pdfdocumentextracter(pdfurl)
        abstract = wisdomaiengine.abstractextracter(pdfurl)
        topics = wisdomaiengine.wordcloud( text)
        if topics is None:
            topics = ['No Topics Found']
        print(abstract)
        print(topics)
        # write data top arxiv collection
        data = {"url": pdfurl, "text": text, "abstract": abstract, "topics": topics, "last_updated": datetime.utcnow()}
        x = arxiv.insert_one(data)
    summaryjson = jsonify(wisdomtopics = topics , wisdomabstract = abstract)
    return summaryjson

# summary
@app.route('/wisdom/summary/<path:pdfurl>',methods=['GET'])
def wisdomsummary(pdfurl ):
    print(pdfurl)
    results = arxiv.findOne({"url": pdfurl})
    if results:
        summary = results.summary
    else:    
        text = wisdomaiengine.pdfdocumentextracter(pdfurl)
        summary = wisdomaiengine.summarisepdfdocument(text)
        print(summary)
        summaryjson = jsonify(wisdomsummary = summary )
        # write data to arxiv collection
        data = {"url": pdfurl, "text": text, "summary": summary, "last_updated": datetime.utcnow()}
        x = arxiv.insert_one(data)
    return summaryjson


# @app.route('/wisdom/<path:pdfurl>',methods=['GET'])
# def wisdombyod(pdfurl ):
#     summary = wisdomaiengine.summarisepdfdocument(text)
#     print(summary)
#     summaryjson = jsonify(wisdomsummary = summary )
#     return summaryjson


@app.route('/search/<string:search_me>/<string:search_topic>/<int:relevance>/<int:summary_points>',methods = ['GET'])
def search(search_me,search_topic , relevance,summary_points):
# Run
    try:
        if search_topic=="Factual":
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
                print('\nSummary ' + title)
                print('\nTitle ' + value)
                print('\nPDF Url' + pdf_url)
                papers.append([title,value,pdf_url])
                wordpapers.append([title])
            # jsonobject = s.factualSummary(search_me, summary_points, f_what_summary)
            wordcloud = wisdomaiengine.wordcloud(wordpapers)
            print(wordcloud)
            print(wordpapers)
            jsonob = jsonify(search= search_me , summary= f_what_summary , papers= papers ,wordcloud = wordcloud )
            
            # check if search_term has been run before
            results = search_terms.findOne({"value": search_me.lower()})
            if results:
                id = results.inserted_id
            else:
                # write data to search_terms collection
                data = {"value": search_me.lower()}
                id = search_terms.insert_one(data)
            # write data to searches collection
            data = {"search_id": id}
            x = searches.insert_one(data)
            
            return jsonob
        else:
            print("- Search topic error...")
    except Exception as e:
        print("\n~~~~> Monty had to exit... visit again soon! :)")
        print("\n Error received:")
        print(e)
        clean_up = []
        for file in os.listdir(os.getcwd()):
            if "{}_".format(search_me) in file:
                clean_up.append(file)
        for file in clean_up:
            os.remove(file)
        clean_up = []
        for file in os.listdir(os.getcwd()):
            if file.endswith(".vtt"):
                clean_up.append(file)
        for file in clean_up:
            os.remove(file)
        # driver.close()
                                                                                            
                                                                                                              
# bring your own document
@app.route('/wisdom/byod/<string:img_location>', methods=['GET'])
def byod(img_location):
    # save img from local device to Wisdom db
    binary_img = Binary(img_location)
    data = {"document_name": "name", "binary_image": binary_img, "datetime": datetime.utcnow()}
    x = byod.insert_one(data)
    # get image from db
    img_id = x.inserted_id
    image = byod.findOne({"_id": img_id})
    # run through engine
    text = wisdomaiengine.bringyourowndocument(image)
    summary = wisdomaiengine.summarisepdfdocument(text)
    topics = wisdomaiengine.wordcloud(text)
    return text, summary, topics
                                                                                                
# run server
if __name__ == '__main__':
    app.run(host='0.0.0.0',threaded=True, port=5000)
                                                                                                              
                                                                                                              