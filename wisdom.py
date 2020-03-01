###########
# IMPORTS #
###########


import wptools
import arxiv
from flask import Flask, request, jsonify, render_template
from flask import session as login_session
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
from passlib.apps import custom_app_context as pwd_context


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
    db_bookmarks = db["bookmarks"]
    db_searches = db["searches"]
    db_search_terms = db["search_terms"]
    db_byod = db["byod"]
    db_highlights = db["highlights"]
    db_wikipedia = db["wikipedia"]
    db_summaries = db["summaries"]
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
    if request.method == 'GET':
        state = generateState(login_session, 'state')
        msg = {"status" : { "type" : "success" ,   "message" : "Generated state"}}
        return jsonify(msg)
    else:
        first_name = request.form['first_name']
        email = request.form['email']
        password = request.form['password']
        if name is None or email is None or password is None:
            msg = {"status" : { "type" : "success" ,   "message" : "Misding fields"}}
            return jsonify(msg)
        user = db_users.find_one({"email": email})
        if user:
            msg = {"status" : { "type" : "success" ,   "message" : "User already exists"}}
            return jsonify(msg)
        # hash password
        hashed_pw = pwd_context.hash(password)
        data = {"first_name": first_name, "email": email,
                "password": hashed_pw, "last_updated": datetime.utcnow()}
        x = db_users.insert(data, check_keys=False)
        #user.hash_password(password)
        msg = {"status" : { "type" : "success" ,   "message" : "User created"}}
        return jsonify(msg)


# log in
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Log In page.
    Contains form to log in to an existing users profile.
    """
    if request.method == 'GET':
        state = generateState(login_session, 'state')
        msg = {"status" : { "type" : "success" ,   "message" : "Login page loaded"}}
        return jsonify(msg)
    else:
        # check the state variable for extra security
        if login_session['state'] != request.args.get('state'):
            message = "cookie was {0} and request was {1}. Invalid state parameter".format(login_session['state'], request.args.get('state'))
            response = make_response(json.dumps(message), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        # check if already logged in with cookie
        cookie = login_session.get('email')
        state = login_session['state']
        if cookie is not None:
            user = db_users.find_one({"email": cookie})
            if user:
                msg = {"status" : { "type" : "success" ,   "message" : "User already logged in"}}
                return jsonify(msg)
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
        login_session['first_name'] = first_name
        login_session['email'] = email
        login_session['profile_id'] = profile_id
        msg = {"status" : { "type" : "success" ,   "message" : "Successful login"}}
        return jsonify(msg)


# log out
@app.route('/logout')
def logout():
    """
    Log Out route.
    Log the user out of their Wisdom account and clear the
    session cookie stored.
    """
    login_session.clear()
    msg = {"status" : { "type" : "success" ,   "message" : "Logged out, bye"}}
    return jsonify(msg)


########
# APIs #
########

# search
@app.route('/search/<string:category>/<string:search_me>', methods=['GET'])
def search(category, search_me):
    """
    Wisdom search.
    User gives a search string and Wisdom finds the definitions,
    associated research papers and a topical word cloud.
    """
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
    except:
        wiki_def = "Oops... couldn't find {}!".format(search_me)
    research_papers = {}
    all_papers = []
    # get arxiv results
    try:
        arxiv_results = arxiv.query(query=search_me.lower(), id_list=[],
                                    max_results=10, start = 0, sort_by="relevance",
                                    sort_order="descending", prune=False,
                                    iterative=False, max_chunk_results=10)
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
    results = db_search_terms.find_one({"value": search_me.lower()})
    if results:
        search_id = results.get('_id')
    else:
        # write data to search_terms collection
        data = {"value": search_me.lower()}
        search_id = db_search_terms.insert(data, check_keys=False)

    # write data to searches collection
    data = {"search_id": search_id, "user": login_session["profile_id"],
            "datetime": datetime.utcnow()}
    x = db_searches.insert(data, check_keys=False)

    # save data to wikipedia collection
    wiki = db_wikipedia.find_one({"search_id": search_id})
    if wiki:
        # update in db if data is 1 days or older
        last_updated = datetime.utcnow() - wiki.get("datetime")
        last_updated_diff = last_updated.days
        if last_updated_diff > 1:
            data = {"search_id": search_id, "wiki_summary": wiki_def,
                    "datetime": datetime.utcnow()}
            db_wikipedia.update({"search_id": search_id}, {"$set": data})
        else:
            pass
    else:
        data = {"search_id": search_id,
                "wiki_summary": wiki_def, 
                "datetime": datetime.utcnow()}
        x = db_wikipedia.insert(data, check_keys=False)

    # return json object
    jsonob = jsonify(search=search_me,
                     summary=wiki_def, 
                     papers=research_papers,
                     wordcloud=wordcloud)
    return jsonob


# wisdom engine
@app.route('/wisdom/<string:search_me>/<string:source>/<path:pdfurl>', methods=['GET'])
def wisdom(search_me, source, pdfurl):
    """
    Wisdom AI engine.
    This extracts insights from documents and returns key points,
    abstracts, wordclouds and PDF viewer if possible.
    """
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
            data = {"search_id": search_id, "url": pdfurl, "source": source, "text": text,
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
        data = {"search_id": search_id, "url": pdfurl, "source": source, "text": text,
                "summary": summary, "topics": topics, "last_updated": datetime.utcnow()}
        x = db_summaries.insert(data, check_keys=False)
    # return json
    summaryjson = jsonify(wisdomtopics=topics, wisdomsummary=summary)
    return summaryjson


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
    if request.method == "POST":
        if content_type == "gallery":
            data = request.form.get('image')
            name = request.form.get('name')
            nparr = np.fromstring(base64.b64decode(data), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            text = wisdomaiengine.bringyourowndocument(img)
            save = {"profile_id": login_session["profile_id"],
                    "content_type": content_type,
                    "doc_name": name,
                    "text": text,
                    "datetime_uploaded": datetime.utcnow()}
            x = db_byod.insert(data, check_keys=False)
            jsonob = jsonify(img=text)
            return jsonob
        if content_type == "camera":
            return None
        if content_type == "webpage":
            page = request.form.get('data')
            name = request.form.get('name')
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
            save = {"profile_id": login_session["profile_id"],
                    "content_type": content_type,
                    "doc_name": name,
                    "text": text,
                    "datetime_uploaded": datetime.utcnow()}
            x = db_byod.insert(data, check_keys=False)
            jsonob = jsonify(text=text)
            return jsonob


# highlighter
@app.route('/highlight/<string:word>')
def highlight(word):
    """
    Wisdom highlighting insights.
    When user highlights a word on the Wisdom screen,
    this route will provide a definition of that word.
    """
    word = word.strip()
    results = wisdomaiengine.highlighter(word)
    jsonob = jsonify(results=results)
    return jsonob


# bookmark content
@app.route("bookmark/<string:search_me>/<string:source>/<path:url>")
def bookmark(search_me, source, url):
    """
    Bookmarker.
    This route is used to save documents to a user
    profile, so that they can revisit it easily.
    """
    email = login_session["email"]
    data = {"email": email, "search_term": search_me,
            "source": source, "url": url, 
            "date_saved": datetime.utcnow()}
    x = db_bookmarks.insert(data, check_keys=False)


### Need a profile route to return all their bookmarks and previous searches...
# email = login_session["email"]
# bookmarks = list(db_bookmarks.find({"email": email}))
# jsonob = jsonify(bookmarks=bookmarks)
# return jsonob


# profile page
@app.route('/profile')
def profile():
    """
    Profile page.
    This route will return all stored information
    within Wisdom that the user needs when logging
    into the application.
    """
    state = generateState(login_session, 'state')
    try:
        first_name = login_session['first_name']
        email = login_session['email']
        user = db_users.find_one({"email": email})
        if user:
            return "Need to return user's data"
        msg = {"status" : { "type" : "success" ,   "message" : "Please log in"}}
        return jsonify(msg)
    except KeyError:
        msg = {"status" : { "type" : "success" ,   "message" : "Please log in"}}
        return jsonify(msg)

                                                                                    
# run server
if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, port=5000)
