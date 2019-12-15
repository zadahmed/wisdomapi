import os
# Import classes
from MontGomery.BaseMonty import BaseMonty
from MontGomery.Factual.FactualMonty import FactualMonty
from MontGomery.Topical.TopicalMonty import TopicalMonty
from MontGomery.Influential.InfluentialMonty import InfluentialMonty


from flask import Flask , request , jsonify
import os
import datetime

# Instantiate Monty
s = BaseMonty()
f = FactualMonty()
t = TopicalMonty()
i = InfluentialMonty()


# Init App
app = Flask(__name__)
dir = os.path.abspath(os.path.dirname(__file__)) #  Directory

# Start
start_datetime,  start, driver, max_screen_width, max_screen_height = s.liftOff()


# @app.route('/search',methods = ['GET'])
# def search():
#     searchterm = request.json['search']
#     sources = request.json['sources']


@app.route('/',methods = ['GET'])
def home():
    return jsonify({'msg':'Hello World'})



@app.route('/search/<string:search_me>/<string:search_topic>/<int:relevance>/<int:summary_points>',methods = ['GET'])
def search(search_me,search_topic , relevance,summary_points):
# Run
    try:
        if search_topic=="Factual":
            # Factual
            f.goWikipediaWhat(search_me, driver)
            f_wiki_soup = f.getWikipediaWhat(driver)
            f.goWikipediaWhen(search_me, driver)
            f_history_soup, f_history_type = f.getWikipediaWhen(driver, search_me)
            f_what_summary, f_old_history_summary_sorted, f_history_summary_sorted = f.wikiSummary(f_wiki_soup, f_history_soup, f_history_type, search_me)
            print("\n")
            print("~"*50, " Wisdom ", "~"*50)
            jsonobject = s.factualSummary(search_me, summary_points, f_what_summary, f_old_history_summary_sorted, f_history_summary_sorted)
            return jsonobject
        elif search_topic=="Topical":
            # Topical
            t.youtubeFilter(search_me, driver, max_screen_width, max_screen_height)
            #t.subtitlesFilter(driver, max_screen_width, max_screen_height)
            t_video_names, t_to_watch, t_video_urls = t.getVideos(search_me, driver, relevance)
            t_video_ids, t_video_dates, t_video_locations = t.watchVideos(driver, max_screen_width, t_video_urls)
            t_video_corpus, t_video_entities = t.montyWatchingTime()
            t_related_searches, t_article_links, t_news_articles, t_news_dates, t_news_entities, t_news_corpus, t_news_locations = t.montyReadingTime(search_me, driver, relevance)
            print("\n")
            print("~"*50, " Wisdom ", "~"*50)
            print("\n")
            jsonobject = s.topicalSummary(search_me, t_news_corpus, t_video_corpus, summary_points)    
            # Appendix
            print("\n")
            print("~"*50, " Wisdom ", "~"*50)
            s.topicalAppendix(t_video_ids, t_video_urls, t_video_dates, t_news_articles, t_news_dates, t_article_links)
            return jsonobject
        elif search_topic=="Influential":
            # Influential
            i_blogs_links, i_blogs_articles, i_blogs_dates = i.goGoogleBlogs(search_me, driver, relevance)
            i_blogs_corpus, i_blogs_entities = i.extractGoogleBlogs(i_blogs_links, i_blogs_articles)
            i.goMedium(search_me, driver)
            i_medium_links = i.getMedium(search_me, driver, relevance)
            i_medium_corpus, i_medium_entities, i_medium_authors, i_medium_dates = i.extractMedium(driver, i_medium_links, max_screen_width)
            i_blogs_corpus, i_blogs_entities, i_blogs_links, i_blogs_authors, i_blogs_dates = i.blogsMerge(i_blogs_corpus, i_blogs_entities, i_blogs_links, i_medium_corpus, i_medium_links, i_medium_entities, i_medium_authors, i_medium_dates)
            i_elsevier_titles, i_elsevier_links, i_elsevier_authors = i.goElsevier(search_me, driver)
            i_elsevier_abstracts = i.extractElsevier(i_elsevier_titles, i_elsevier_links, driver)
            i_arxiv_links, i_arxiv_titles = i.goArXiv(search_me, driver)
            i_arxiv_abstracts, i_arxiv_authors = i.extractArxiv(i_arxiv_links, i_arxiv_titles)
            i_research_titles, i_research_links, i_research_authors, i_research_abstracts = i.researchMerge(i_elsevier_titles, i_elsevier_links, i_elsevier_authors, i_elsevier_abstracts, i_arxiv_links, i_arxiv_titles, i_arxiv_abstracts, i_arxiv_authors)
            print("~"*50, " Wisdom ", "~"*50)
            jsonobject = s.influentialSummary(search_me, summary_points, i_blogs_corpus, i_blogs_authors, i_research_abstracts, i_research_authors)
            # Appendix
            print("~"*50, " Wisdom ", "~"*50)
            s.influentialAppendix(i_blogs_links, i_research_titles, i_research_authors)
            return jsonobject
        elif search_topic=="Everything":
            # Factual
            f.goWikipediaWhat(search_me, driver)
            f_wiki_soup = f.getWikipediaWhat(driver)
            f.goWikipediaWhen(search_me, driver)
            f_history_soup, f_history_type = f.getWikipediaWhen(driver, search_me)
            f_what_summary, f_old_history_summary_sorted, f_history_summary_sorted = f.wikiSummary(f_wiki_soup, f_history_soup, f_history_type, search_me)
            # Topical
            t.youtubeFilter(search_me, driver, max_screen_width, max_screen_height)
            #t.subtitlesFilter(driver, max_screen_width, max_screen_height)
            t_video_names, t_to_watch, t_video_urls = t.getVideos(search_me, driver, relevance)
            t_video_ids, t_video_dates, t_video_locations = t.watchVideos(driver, max_screen_width, t_video_urls)
            t_video_corpus, t_video_entities = t.montyWatchingTime()
            t_related_searches, t_article_links, t_news_articles, t_news_dates, t_news_entities, t_news_corpus, t_news_locations = t.montyReadingTime(search_me, driver, relevance)
            # Influential
            i_blogs_links, i_blogs_articles, i_blogs_dates = i.goGoogleBlogs(search_me, driver, relevance)
            i_blogs_corpus, i_blogs_entities = i.extractGoogleBlogs(i_blogs_links, i_blogs_articles)
            i.goMedium(search_me, driver)
            i_medium_links = i.getMedium(search_me, driver, relevance)
            i_medium_corpus, i_medium_entities, i_medium_authors, i_medium_dates = i.extractMedium(driver, i_medium_links, max_screen_width)
            i_blogs_corpus, i_blogs_entities, i_blogs_links, i_blogs_authors, i_blogs_dates = i.blogsMerge(i_blogs_corpus, i_blogs_entities, i_blogs_links, i_medium_corpus, i_medium_links, i_medium_entities, i_medium_authors, i_medium_dates)
            i_elsevier_titles, i_elsevier_links, i_elsevier_authors = i.goElsevier(search_me, driver)
            i_elsevier_abstracts = i.extractElsevier(i_elsevier_titles, i_elsevier_links, driver)
            i_arxiv_links, i_arxiv_titles = i.goArXiv(search_me, driver)
            i_arxiv_abstracts, i_arxiv_authors = i.extractArxiv(i_arxiv_links, i_arxiv_titles)
            i_research_titles, i_research_links, i_research_authors, i_research_abstracts = i.researchMerge(i_elsevier_titles, i_elsevier_links, i_elsevier_authors, i_elsevier_abstracts, i_arxiv_links, i_arxiv_titles, i_arxiv_abstracts, i_arxiv_authors)
            # Summary
            print("~"*50, " Wisdom ", "~"*50)
            s.factualSummary(search_me, summary_points, f_what_summary, f_old_history_summary_sorted, f_history_summary_sorted)
            s.topicalSummary(search_me, t_news_corpus, t_video_corpus, summary_points)
            s.influentialSummary(search_me, summary_points, i_blogs_corpus, i_blogs_authors, i_research_abstracts, i_research_authors)
            # Appendix
            print("~"*50, " Wisdom ", "~"*50)
            s.contextSummary(t_news_entities, t_video_entities, t_video_dates, i_blogs_entities, i_blogs_dates, t_news_dates, t_news_locations, t_video_locations, t_related_searches, search_me)
            print("~"*50, " Wisdom ", "~"*50)
            s.topicalAppendix(t_video_ids, t_video_urls, t_video_dates, t_news_articles, t_news_dates, t_article_links)
            s.influentialAppendix(i_blogs_links, i_research_titles, i_research_authors)
        else:
            print("- Search topic error...")
        # Finish
        s.finish(driver, start_datetime, start, search_topic, search_me, summary_points)
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
        driver.close()

#Run Server
if __name__ == '__main__':
    app.run(debug=True)