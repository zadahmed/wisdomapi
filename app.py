import os
import wptools
import arxiv
from flask import Flask , request , jsonify
import os
import wisdomaiengine
from urllib.parse import unquote


app = Flask(__name__)
dir = os.path.abspath(os.path.dirname(__file__)) #  Directory



@app.route('/',methods = ['GET'])
def home():
    return jsonify({'msg':'Hello World'})

@app.route('/wisdom/<path:pdfurl>',methods=['GET'])
def wisdom(pdfurl):
    text = wisdomaiengine.pdfdocumentextracter(pdfurl)
    summary = wisdomaiengine.summarisepdfdocument(text)
    topics = wisdomaiengine.topicsindocument(text)
    print(text)
    print(summary)
    print(topics)
    summaryjson = jsonify(wisdomsummary = summary , wisdomtopics = topics)
    return summaryjson

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
                pdf_url = paper['pdf_url']
                print('\nSummary ' + title)
                print('\nTitle ' + value)
                print('\nPDF Url' + pdf_url)
                papers.append([title,value,pdf_url])
                wordpapers.append([title])
            # jsonobject = s.factualSummary(search_me, summary_points, f_what_summary)
            # wordcloud = wisdomaiengine.wordcloud(search_me,wordpapers)
            print(wordpapers)
            jsonob = jsonify(search= search_me , summary= f_what_summary , papers= papers )
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
