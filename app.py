import os
# Import classes
from MontGomery.BaseMonty import BaseMonty
import wptools
import arxiv
from flask import Flask , request , jsonify
import os
import abstractapi
import urllib

# Instantiate Monty
s = BaseMonty()

# Init App
app = Flask(__name__)
dir = os.path.abspath(os.path.dirname(__file__)) #  Directory



@app.route('/',methods = ['GET'])
def home():
    return jsonify({'msg':'Hello World'})

@app.route('/wisdom/<string:pdfurl>',methods=['GET'])
def wisdom(pdfurl):
    abstra = urllib.decode(pdfurl)
    updf = 'https://' + abstra
    print(updf)
    abstract = abstractapi.abstractextracter(updf)
    abstractjson = jsonify(wisdomabstract = abstract)
    return abstractjson

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

            for paper in result:
                title = paper['summary']
                value = paper['title_detail']['value']
                pdf_url = paper['pdf_url']
                print('\nSummary ' + title)
                print('\nTitle ' + value)
                print('\nPDF Url' + pdf_url)
                papers.append([title,value,pdf_url])
            # jsonobject = s.factualSummary(search_me, summary_points, f_what_summary)
            jsonob = jsonify(search= search_me , summary= f_what_summary , papers= papers)
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

#Run Server
if __name__ == '__main__':
    app.run(threaded=True, port=5000)
