# Monty's topical class to crawl YouTube and Google News

# Imports
import os
import time
import re
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from nltk.tokenize import sent_tokenize
from bs4 import BeautifulSoup
import spacy
from TopicalCleaner import YoutubeCleaner, GoogleNewsCleaner

# global variables
def download_subs(video_url, lang="en"):
    # Download subtitles from YouTube video
    cmd = [
        "youtube-dl",
        "--skip-download",
        "--write-sub",
        "--quiet",
        "--no-warnings",
        "--sub-lang",
        lang,
        video_url
    ]
    os.system(" ".join(cmd))


class TopicalMonty():

    def youtubeFilter(self, search_me, driver, max_screen_width, max_screen_height):
        print("\n=====================================")
        print("MontGomery's Topical Tour...")
        print("=====================================\n")
        insert_search = search_me.replace(" ", "+")
        insert_search = '"'+insert_search+'"'
        insert_search = "/results?search_query="+insert_search+"&sp=EgQYASgB"
        driver.get("https://youtube.com"+insert_search)
        #driver.implicitly_wait(10)
        #search = driver.find_element_by_css_selector("#search-input.ytd-searchbox-spt input")
        #search.click()
        #search.send_keys(search_me)
        #search.send_keys(Keys.RETURN)
        #print("- Filtering videos...")
        #try:
            # Navigate to and click on filter button to filter by videos with CC
        #    driver.implicitly_wait(10)
        #    filt = driver.find_elements_by_xpath('//*[@id="text"]')
        #    matchword = 'FILTER'
        #    find_filt = [i.text for i in filt]
        #    position = find_filt.index(matchword)
        #    filt = filt[position]
        #    time.sleep(1)
        #    filt.click()
        #except:
        #    print("----> Error finding YouTube filter, trying again...")
        #    driver.refresh()
        #    driver.set_window_size(max_screen_width/0.75, max_screen_height/0.75)
        #    time.sleep(1)
        #    driver.set_window_size(max_screen_width, max_screen_height)
            # Navigate to and click on filter button to filter by videos with CC
        #    driver.implicitly_wait(10)
        #    filt = driver.find_elements_by_xpath('//*[@id="text"]')
        #    matchword = 'FILTER'
        #    find_filt = [i.text for i in filt]
        #    position = find_filt.index(matchword)
        #    filt = filt[position]
        #    time.sleep(1)
        #    filt.click()


    def subtitlesFilter(self, driver, max_screen_width, max_screen_height):
        print("- Finding the best videos to watch...")
        try:
            # Select videos with CC
            driver.implicitly_wait(10)
            subtitles = driver.find_elements_by_xpath('//*[@id="label"]/yt-formatted-string')
            matchword = 'Subtitles/CC'
            find_sub = [i.text for i in subtitles]
            position = find_sub.index(matchword)
            subtitles = subtitles[position]
            time.sleep(1)
            subtitles.click()
        except:
            print("----> Error finding quality videos, trying again...")
            driver.refresh()
            driver.set_window_size(max_screen_width/0.75, max_screen_height/0.75)
            time.sleep(1)
            driver.set_window_size(max_screen_width, max_screen_height)
            # Select videos with CC
            driver.implicitly_wait(10)
            subtitles = driver.find_elements_by_xpath('//*[@id="label"]/yt-formatted-string')
            matchword = 'Subtitles/CC'
            find_sub = [i.text for i in subtitles]
            position = find_sub.index(matchword)
            subtitles = subtitles[position]
            time.sleep(1)
            subtitles.click()
        time.sleep(0.5)
        # Filter by short videos
        try:
            # Navigate to and click on filter button to filter by videos with CC
            driver.implicitly_wait(10)
            filt = driver.find_elements_by_xpath('//*[@id="text"]')
            matchword = 'FILTER'
            find_filt = [i.text for i in filt]
            position = find_filt.index(matchword)
            filt = filt[position]
            time.sleep(1)
            filt.click()
        except:
            driver.refresh()
            driver.set_window_size(max_screen_width/0.75, max_screen_height/0.75)
            time.sleep(1)
            driver.set_window_size(max_screen_width, max_screen_height)
            # Navigate to and click on filter button to filter by videos with CC
            driver.implicitly_wait(10)
            filt = driver.find_elements_by_xpath('//*[@id="text"]')
            matchword = 'FILTER'
            find_filt = [i.text for i in filt]
            position = find_filt.index(matchword)
            filt = filt[position]
            time.sleep(1)
            filt.click()
        time.sleep(0.5)
        try:
            # Select videos with CC
            driver.implicitly_wait(10)
            subtitles = driver.find_elements_by_xpath('//*[@id="label"]/yt-formatted-string')
            matchword = 'Short (< 4 minutes)'
            find_sub = [i.text for i in subtitles]
            position = find_sub.index(matchword)
            subtitles = subtitles[position]
            time.sleep(1)
            subtitles.click()
        except:
            print("----> Error finding quality videos, trying again...")
            driver.refresh()
            driver.set_window_size(max_screen_width/0.75, max_screen_height/0.75)
            time.sleep(1)
            driver.set_window_size(max_screen_width, max_screen_height)
            # Select videos with CC
            driver.implicitly_wait(10)
            subtitles = driver.find_elements_by_xpath('//*[@id="label"]/yt-formatted-string')
            matchword = 'Short (< 4 minutes)'
            find_sub = [i.text for i in subtitles]
            position = find_sub.index(matchword)
            subtitles = subtitles[position]
            time.sleep(1)
            subtitles.click()


    def getVideos(self, search_me, driver, X):
        print("- Curating video list...")
        # Scroll down feed
        n=0
        while True:
            if n<5:
                driver.execute_script("window.scrollTo(0, 10000000)")
                time.sleep(1)
                n+=1
            else:
                break
        # Get video names and filter out irrelevant ones
        driver.implicitly_wait(10)
        video_titles = driver.find_elements_by_id("video-title")
        t_video_names = [i.get_property("title") for i in video_titles]
        list1 = search_me.lower().split()
        t_to_watch = [i for i in t_video_names if (sum(l in list1 for l in i.lower().split())/len(list1)) >= (X/10)]    
        # Get urls for relevant videos
        t_video_urls = []
        for i in t_to_watch:
            try:
                url = driver.find_element_by_xpath("""//*[contains(text(), '{}')]""".format(i))
                t_video_urls.append(url)
            except:
                t_to_watch.remove(i)
        t_video_urls = [i.get_property("href") for i in t_video_urls]
        print("- I've found,", len(t_video_urls), "videos to watch...")
        return t_video_names, t_to_watch, t_video_urls


    def watchVideos(self, driver, max_screen_width, t_video_urls):
        driver.set_window_position(-(max_screen_width*5),0)
        print("- Watching videos...")
        t_video_ids = []
        t_video_dates = []
        t_video_locations = []
        y=1
        for i in t_video_urls:
            try:
                driver.get(i)
                driver.implicitly_wait(10)
                title = driver.find_element_by_css_selector(".title.ytd-video-primary-info-renderer")
                t_video_ids.append(title.text)
                print("    "+str(y)+". Watching:", title.text)
                driver.implicitly_wait(10)
                date = driver.find_element_by_class_name("date")
                t_video_dates.append(date.text)
                # Get location
                try:
                    driver.implicitly_wait(10)
                    page = driver.find_element_by_xpath('//*[@id="img"]')
                    page.click()
                    #time.sleep(2)
                    driver.implicitly_wait(10)
                    about = driver.find_elements_by_tag_name("paper-tab")
                    matchword = 'ABOUT'
                    find_about = [i.text for i in about]
                    position = find_about.index(matchword)
                    about = about[position]
                    about.click()
                    #time.sleep(1)
                    driver.implicitly_wait(10)
                    search = driver.find_elements_by_tag_name("td")
                    results = [i.text for i in search]
                    location = results[results.index("Location:")+1]
                    t_video_locations.append(location)
                except:
                    pass
                y+=1
                time.sleep(1)
                download_subs("'{}'".format(i))
            except:
                print("    ----> Error with:", i, "moving onto the next video...")
                y+=1    
            continue
        print("- Finished watching videos :)")
        return t_video_ids, t_video_dates, t_video_locations


    def montyWatchingTime(self):
        t_video_corpus, t_video_entities = YoutubeCleaner()
        return t_video_corpus, t_video_entities


    def montyReadingTime(self, search_me, driver, X):
        # Now to search Google News
        query = search_me.replace(" ", "+")
        source = "&source=lnms&tbm=nws&sa=X&ved=0ahUKEwiAz5GF5dLiAhW0qHEKHZIjCxEQ_AUIEygE&cshid=1559753093567875&biw=1440&bih=798"
        driver.get("https://google.co.uk/search?q="+query+source)
        time.sleep(1)
        # find related searches
        try:
            related = driver.find_elements_by_id("brs")
            t_related_searches = [i.text for i in related]
            t_related_searches = [i.split("\n") for i in t_related_searches]
            t_related_searches = t_related_searches[0]
            t_related_searches = t_related_searches[1:]
        except:
            t_related_searches = []
        # Select News from google
        buzzword = "News"
        driver.implicitly_wait(10)
        news = driver.find_elements_by_class_name("q")
        for i in news:
            if buzzword in i.text:
                i.click()
                break
            else:
                pass
        # Get links for news articles
        n=0
        t_article_links = []
        t_news_articles = []
        t_news_dates = []
        while True:
            try:
                if n<5:
                    driver.implicitly_wait(10)
                    pages = [i.text for i in driver.find_elements_by_class_name("fl")]
                    if len(pages)==1:
                        break
                    elif len(pages)==0:
                        break
                    else:
                        for i in driver.find_elements_by_class_name("l"):
                            t_article_links.append(i.get_attribute("href"))
                            t_news_articles.append(i.text)
                        for i in driver.find_elements_by_class_name("slp"):
                            t_news_dates.append(i.text)
                        next_button = driver.find_element_by_id("pnnext")
                        next_button.click()
                        n+=1
                else:
                    break
            except:
                break
        # Filter out articles without search_me in name
        indices_to_remove = []
        n=0
        for i in t_article_links:
            cnt=0
            for j in search_me.split():
                if j in i.lower():
                    cnt+=1
                else:
                    pass
            if cnt/len(search_me.split()) >= (X/10):
                n+=1
            else:
                indices_to_remove.append(n)
                n+=1        
        for index in sorted(indices_to_remove, reverse=True):
            del t_article_links[index]
        print("- I've found", len(t_article_links), "news articles to read...")
        for index in sorted(indices_to_remove, reverse=True):
            del t_news_dates[index]   
        for index in sorted(indices_to_remove, reverse=True):
            del t_news_articles[index]
        # Create corpus
        t_news_corpus, t_news_entities = GoogleNewsCleaner(t_article_links, t_news_articles)
        # Get location
        t_news_locations = []
        driver.get("https://who.is/whois/google")
        for i in t_article_links:
            try:
                if "www" in i.split("//")[1].split("/")[0].split("."):
                    if "uk" in i.split("//")[1].split("/")[0].split("."):
                        source = i.split("//")[1].split("/")[0].split(".")[1]+"."+i.split("//")[1].split("/")[0].split(".")[2]+"."+i.split("//")[1].split("/")[0].split(".")[3]
                        search_this = "www."+source
                    else:
                        source = i.split("//")[1].split("/")[0].split(".")[1]+"."+i.split("//")[1].split("/")[0].split(".")[2]
                        search_this = "www."+source
                else:    
                    if "uk" in i.split("//")[1].split("/")[0].split("."):
                        source = i.split("//")[1].split("/")[0].split(".")[0]+"."+i.split("//")[1].split("/")[0].split(".")[1]+"."+i.split("//")[1].split("/")[0].split(".")[2]
                        search_this = "www."+source
                    else:
                        source = i.split("//")[1].split("/")[0].split(".")[0]+"."+i.split("//")[1].split("/")[0].split(".")[1]
                        search_this = "www."+source
                driver.implicitly_wait(10)
                search = driver.find_element_by_tag_name("input")
                search.click()
                search.send_keys(search_this)
                search.send_keys(Keys.RETURN)
                location = [i.text for i in driver.find_elements_by_class_name("row")]
                location = [i for i in location if "Country" in i]
                if location:
                    pass
                else:
                    location = location[0]
                    location = location.split("\n")
                    n=0
                    for i in location:
                        if "Registrant Country" in i:
                            m=n
                        elif "Country" in i:
                            n+=1
                            m=n
                        else:
                            n+=1
                    if ":" in location[m]:
                        t_news_locations.append(location[m].split(": ")[1])
                    else:
                        t_news_locations.append(location[m])
            except:
                t_news_locations.append("N/A")
        print("- News content added to corpus :)")
        return t_related_searches, t_article_links, t_news_articles, t_news_dates, t_news_entities, t_news_corpus, t_news_locations
        