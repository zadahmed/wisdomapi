###########
# IMPORTS #
###########


import wptools
from flask import Flask, request, jsonify, render_template
from flask import session as login_session
import os
import wisdomaiengine
from urllib.parse import unquote
import pymongo
from bson import ObjectId
from bson.son import SON
from bson.code import Code
from io import BytesIO
import sys
from datetime import datetime
import base64
from PIL import Image
import numpy as np
import cv2
import requests
from passlib.apps import custom_app_context as pwd_context
from bs4 import BeautifulSoup
from collections import Counter
import pandas as pd


##########################
# INSTANTIATE FLASK & DB #
##########################

app = Flask(__name__)
app.secret_key = "super secret key"
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
    db_bookmarks = db["bookmarks"]
    db_searches = db["searches"]
    db_search_terms = db["search_terms"]
    db_byod = db["byod"]
    db_highlights = db["highlights"]
    db_wikipedia = db["wikipedia"]
    db_summaries = db["summaries"]
    db_is_loggedin = db["is_loggedin"]
except:
    print("Unable to connect to collections")
    sys.exit(1)


#############
# FUNCTIONS #
#############

# Function used for generate state
def generateState(sess, key):
    """
    Generate state used for application cookie.
    Creates a random string of numbers and letters to encrypt the
    users session for use within a cookie.
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    sess[key] = state
    return state


##########
# ROUTES #
##########

# landing page
@app.route('/', methods=['GET'])
def home():
    """
    Route for Wisdom web page.
    Web page to show users what Wisdom is, how it works, about
    the company and how they can download the app.
    """
    return render_template("index.html")


# sign up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Sign Up page.
    Contains form to sign up as a user on Wisdom platform.
    """
    if request.method == "GET":
        print("Hi")
    else:
        first_name = request.form['first_name']
        email = request.form['email']
        password = request.form['password']
        print(first_name, email, password)
        if first_name is None or email is None or password is None:
            msg = {"status" : { "type" : "success" ,   "message" : "Missing fields"}}
            return jsonify(msg)
        user = db_users.find_one({"email": email})
        if user:
            msg = {"status" : { "type" : "success" ,   "message" : "User already exists"}}
            return jsonify(msg)
        # hash password
        hashed_pw = pwd_context.hash(password)
        data = {"first_name": first_name,
                "email": email,
                "password": hashed_pw,
                "last_updated": datetime.utcnow()}
        search_id = db_users.insert(data, check_keys=False)
        # create user in logged in table
        data = {"user": str(search_id),
                "is_loggedin": False}
        is_loggedin = db_is_loggedin.insert(data, check_keys=False)
        #user.hash_password(password)
        msg = {"id": str(search_id)}
        print(msg)
        return jsonify(msg)


# log in
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Log In page.
    Contains form to log in to an existing users profile.
    """
    if request.method == "GET":
        print("hi")
    else:
        # # check the state variable for extra security
        # if login_session['state'] != request.args.get('state'):
        #     message = "cookie was {0} and request was {1}. Invalid state parameter".format(login_session['state'], request.args.get('state'))
        #     response = make_response(json.dumps(message), 401)
        #     response.headers['Content-Type'] = 'application/json'
        #     return response
        # # check if already logged in with cookie
        # cookie = login_session.get('email')
        # state = login_session['state']
        # if cookie is not None:
        #     user = db_users.find_one({"email": cookie})
        #     if user:
        #         msg = {"status" : { "type" : "success" ,   "message" : "User already logged in"}}
        #         return jsonify(msg)
        # otherwise, log in
        email = request.form['email']
        password = request.form['password']
        user = db_users.find_one({"email": email})
        if not user:
            msg = {"status" : { "type" : "success" ,   "message" : "User does not exist, please sign up"}}
            return jsonify(msg)
        stored_pw = user.get("password")
        if not pwd_context.verify(password, stored_pw):
            msg = {"status" : { "type" : "success" ,   "message" : "Invalid password, try again"}}
            return jsonify(msg)
        first_name = user.get("first_name")
        profile_id = user.get("_id")
        # save login details in cookie
        # login_session['first_name'] = first_name
        # login_session['email'] = email
        # login_session['profile_id'] = str(profile_id)
        # set is_loggedin = True
        is_loggedin = db_is_loggedin.find_one({"user": str(profile_id)})
        if is_loggedin:
            if is_loggedin.get("is_loggedin") == False:
                data = {"is_loggedin": True}
                db_is_loggedin.update({"user": str(profile_id)}, {"$set": data})
                msg = {"id": str(profile_id)}
                return jsonify(msg)
            else:
                msg = {"status" : { "type" : "success" ,   "message" : "Already logged in"}}
                return jsonify(msg)
        else:
            msg = {"status" : { "type" : "success" ,   "message" : "User not found, please sign up"}}
            return jsonify(msg)


# log out
@app.route('/logout/<string:userid>')
def logout(userid):
    """
    Log Out route.
    Log the user out of their Wisdom account and clear the
    session cookie stored.
    """
    if userid:
        is_loggedin = db_is_loggedin.find_one({"user": str(userid)})
        if is_loggedin:
            if is_loggedin.get("is_loggedin") == True:
                data = {"is_loggedin": False}
                db_is_loggedin.update({"user": str(userid)}, {"$set": data})
                msg = {"status" : { "type" : "success" ,   "message" : "Logged out"}}
                return jsonify(msg)
            else:
                msg = {"status" : { "type" : "success" ,   "message" : "Already logged out"}}
                return jsonify(msg)
        else:
            msg = {"status" : { "type" : "success" ,   "message" : "User not found, sign up"}}
            return jsonify(msg)
    else:
        msg = {"status" : { "type" : "success" ,   "message" : "Provide userid"}}
        return jsonify(msg)


########
# APIs #
########

# log out
@app.route('/logincheck/<string:userid>')
def logincheck(userid):
    """
    Check whether user is logged in.
    """
    if userid:
        is_loggedin = db_is_loggedin.find_one({"user": str(userid)})
        if is_loggedin:
            if is_loggedin.get("is_loggedin") == True:
                msg = {str(userid)}
                return jsonify(msg)
            else:
                msg = {"status" : { "type" : "success" ,   "message" : "User is logged out"}}
                return jsonify(msg)
        else:
            msg = {"status" : { "type" : "success" ,   "message" : "User not found, sign up"}}
            return jsonify(msg)
    else:
        msg = {"status" : { "type" : "success" ,   "message" : "Provide userid"}}
        return jsonify(msg)


# factual
@app.route('/definition/<string:category>/<string:search_me>/<string:userid>', methods=['GET'])
def definitionsearch(category, search_me, userid):
    """
    Factual search.
    Returns factual definitions of the search term.
    """
    if userid:
        user_id = userid
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
            # else use wikipedia API
            else:
                wiki_def = wisdomaiengine.factualsearch(category, search_me.lower())
        except:
            wiki_def = "Oops... couldn't find {}!".format(search_me)
        # check if search_term has been run before
        results = db_search_terms.find_one({"value": search_me.lower()})
        if results:
            search_id = results.get('_id')
        else:
            data = {"value": search_me.lower()}
            search_id = db_search_terms.insert(data, check_keys=False)
        # write data to searches collection
        data = {"search_id": search_id,
                "user": userid,
                "datetime": datetime.utcnow()}
        x = db_searches.insert(data, check_keys=False)
        # save data to wikipedia collection
        wiki = db_wikipedia.find_one({"search_id": search_id})
        if wiki:
            if wiki.get("wiki_summary") != wiki_def:
                data = {"search_id": search_id,
                        "wiki_summary": wiki_def,
                        "datetime": datetime.utcnow()}
                db_wikipedia.update({"search_id": search_id}, {"$set": data})
                # last_updated = datetime.utcnow() - wiki.get("datetime")
                # last_updated_diff = last_updated.days
                # if last_updated_diff > 1:
                #     data = {"search_id": search_id,
                #             "wiki_summary": wiki_def,
                #             "datetime": datetime.utcnow()}
                #     db_wikipedia.update({"search_id": search_id}, {"$set": data})
                # else:
                #     pass
        else:
            data = {"search_id": search_id,
                    "wiki_summary": wiki_def, 
                    "datetime": datetime.utcnow()}
            x = db_wikipedia.insert(data, check_keys=False)
        # return json
        jsonob = jsonify(search=search_me,
                         factual=wiki_def)
        return jsonob
    else:
        msg = {"status" : { "type" : "success" ,   "message" : "Please log in"}}
        return jsonify(msg)

    
# research papers
@app.route('/research/<string:category>/<string:search_me>/<string:userid>', methods=['GET'])
def papersearch(category, search_me, userid):
    """
    Research paper search.
    Returns research papers of the search term.
    """
    if userid:
        user_id = userid
        search_me = search_me.strip()
        research_papers = {}
        all_papers = []
        # get arxiv results
        try:
            papers = wisdomaiengine.getarxivresults(search_me.lower())
            for paper in papers:
                all_papers.append(paper[1])
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
        # return json object
        jsonob = jsonify(papers=research_papers,
                         wordcloud=wordcloud)
        return jsonob
    else:
        msg = {"status" : { "type" : "success" ,   "message" : "Please log in"}}
        return jsonify(msg)


# wisdom engine
@app.route('/wisdom/<string:search_me>/<string:source>/<path:pdfurl>/<string:userid>', methods=["GET"])
def wisdom(search_me, source, pdfurl, userid):
    """
    Wisdom AI engine.
    This extracts insights from documents and returns key points,
    abstracts, wordclouds and PDF viewer if possible.
    """
    if userid:
        ### source needs to be name of data source ("arxiv", "google scholar", "doaj")
        search_me = search_me.strip()
        # check if pdfurl has been found before
        pdf = db_summaries.find_one({"url": pdfurl})
        if pdf:
            text = pdf.get('text')
            summary = pdf.get('summary')
            topics = pdf.get('topics')
            # update in db if data is 1 days or older
            last_updated = datetime.utcnow() - pdf.get("last_updated")
            last_updated_diff = last_updated.days
            if last_updated_diff > 1:
                search_term = db_search_terms.find_one({"value": search_me.lower()})
                search_id = search_term.get("_id")
                data = {"search_id": search_id,
                        "url": pdfurl, "source": source, "text": text,
                        "summary": summary, "topics": topics, "last_updated": datetime.utcnow()}
                db_summaries.update({"url": pdfurl}, {"$set": data})
            else:
                pass
        else:
            text = wisdomaiengine.pdfdocumentextracter(pdfurl)
            summary = wisdomaiengine.summarisepdfdocument(text)
            topics = wisdomaiengine.wordcloud(search_me, text)
            if topics is None:
                topics = ['No Topics Found']
            # write data to arxiv collection
            search_term = db_search_terms.find_one({"value": search_me.lower()})
            search_id = search_term.get("_id")
            data = {"search_id": search_id,
                    "url": pdfurl,
                    "source": source,
                    "text": text,
                    "summary": summary,
                    "topics": topics,
                    "last_updated": datetime.utcnow()}
            x = db_summaries.insert(data, check_keys=False)
        # return json
        summaryjson = jsonify(wisdomtopics=topics, wisdomsummary=summary)
        return summaryjson
    else:
        msg = {"status" : { "type" : "success" ,   "message" : "Please log in"}}
        return jsonify(msg)


# bring your own document
@app.route('/byod/<string:content_type>', methods=['GET' , 'POST'])
def byod(content_type):
    """
    Bring Your Own Document.
    Make use of the Wisdom AI engine on yoru own
    documents. Upload an image from your gallery, take
    a picture or supply a webpage.
    """
    if request.method == "GET":
        print("Hi")
    else:
        user_id = request.form['userid']
        if user_id:
            if content_type == "gallery":
                data = request.form['image']
                name = request.form['name']
                nparr = np.fromstring(base64.b64decode(data), np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                text = wisdomaiengine.bringyourowndocument(img)
                save = {"user": user_id,
                        "content_type": content_type,
                        "doc_name": name,
                        "text": text,
                        "datetime_uploaded": datetime.utcnow()}
                x = db_byod.insert(save, check_keys=False)
                jsonob = jsonify(img=text)
                return jsonob
            if content_type == "camera":
                return None
            if content_type == "webpage":
                page = request.form['data']
                name = request.form['name']
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
                save = {"user": user_id,
                        "content_type": content_type,
                        "doc_name": name,
                        "text": text,
                        "datetime_uploaded": datetime.utcnow()}
                x = db_byod.insert(save, check_keys=False)
                jsonob = jsonify(text=text)
                return jsonob
        else:
            msg = {"status" : { "type" : "success" ,   "message" : "Please log in"}}
            return jsonify(msg)


# highlighter
@app.route('/highlight/<string:search_me>/<string:word>/<string:userid>', methods=["GET"])
def highlight(search_me, word, userid):
    """
    Wisdom highlighting insights.
    When user highlights a word on the Wisdom screen,
    this route will provide a definition of that word.
    """
    if userid:
        word = word.strip()
        results = wisdomaiengine.highlighter(word)
        search_term = db_search_terms.find_one({"value": search_me.lower()})
        search_id = search_term.get("_id")
        data = {"user": userid,
                "search_id": search_id,
                "highlighted_word": word,
                "results": results,
                "date_saved": datetime.utcnow()}
        x = db_highlights.insert(data, check_keys=False)
        jsonob = jsonify(results=results)
        return jsonob
    else:
        msg = {"status" : { "type" : "success" ,   "message" : "Please log in"}}
        return jsonify(msg)


# bookmark content
@app.route("/bookmark/<string:search_me>/<string:source>/<path:url>", methods=["POST"])
def bookmark(search_me, source, url):
    """
    Bookmarker.
    This route is used to save documents to a user
    profile, so that they can revisit it easily.
    """
    user_id = request.form['userid']
    if user_id:
        search_term = db_search_terms.find_one({"value": search_me.lower()})
        search_id = search_term.get("_id")
        data = {"user": user_id,
                "search_id": search_id,
                "source": source,
                "url": url, 
                "date_saved": datetime.utcnow()}
        x = db_bookmarks.insert(data, check_keys=False)
        msg = {"status" : { "type" : "success" ,   "message" : "Bookmark created"}}
        return jsonify(msg)
    else:
        msg = {"status" : { "type" : "success" ,   "message" : "Please log in"}}
        return jsonify(msg)


### Need a profile route to return all their bookmarks and previous searches...
# email = login_session["email"]
# bookmarks = list(db_bookmarks.find({"email": email}))
# jsonob = jsonify(bookmarks=bookmarks)
# return jsonob


# profile page
@app.route('/profile/<string:userid>', methods=["GET"])
def profile(userid):
    """
    Profile page.
    This route will return all stored information
    within Wisdom that the user needs when logging
    into the application.
    """
    if userid:
        #first_name = login_session['first_name']
        bookmarks = db_bookmarks.find({"user": userid})
        bookmarks = [{"search_term": db_search_terms.find_one({"_id": b["search_id"]}).get("value"), "source": b["source"], "url": b["url"], "date_saved": b["date_saved"].strftime("%H:%M %B %d, %Y")} for b in bookmarks]
        searches = db_searches.find({"user": userid})
        searches = [{"search_term": db_search_terms.find_one({"_id": s["search_id"]}).get("value"), "datetime": s["datetime"].strftime("%H:%M %B %d, %Y")} for s in searches]
        byod = db_byod.find({"user": userid})
        byod = [{"content_type": b["content_type"], "doc_name": b["doc_name"], "text": b["text"], "datetime_uploaded": b["datetime_uploaded"].strftime("%H:%M %B %d, %Y")} for b in byod]
        highlights = db_highlights.find({"user": userid})
        highlights = [{"search_term": db_search_terms.find_one({"_id": h["search_id"]}).get("value"), "highlighted_word": h["highlighted_word"], "results": h["results"], "date_saved": h["date_saved"].strftime("%H:%M %B %d, %Y")} for h in highlights]
        # top 10 searches in community
        # agg = db_searches.aggregate([
        #             {"$group": {"_id": "$search_id",
        #                         "count": {"$sum": 1}
        #                         }
        #             }])
        agg = [s["search_id"] for s in db_searches.find()]
        table = pd.DataFrame()
        table["searches"] = Counter(agg).keys()
        table["count"] = Counter(agg).values()
        table = table.sort_values("count", ascending=False)
        table = table[:10]
        search_ids = table["searches"].values
        counts = table["count"].values
        n = 0
        top_n = []
        while n < len(search_ids):
            top_n.append([str(db_search_terms.find_one({"_id": search_ids[n]}).get("value")), str(counts[n])])
            n += 1
        jsonob = jsonify(bookmarks=bookmarks,
                         searches=searches,
                         byod=byod,
                         highlights=highlights,
                         top_n=top_n)
        return jsonob
    else:
        msg = {"status": {"type": "success", "message": "Please log in"}}
        return jsonify(msg)

                                                                                    
# run server
if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, port=5000)
