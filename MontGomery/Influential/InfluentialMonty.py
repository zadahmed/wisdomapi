# Class for finding out influential information on topics, such as latest breakthroughs, influential people and companies

# Imports
import time
import re
import time
from selenium.webdriver.common.keys import Keys
from langdetect import detect
from InfluentialCleaner import GoogleBlogsCleaner, MediumCleaner, ElsevierCleaner, ArXivCleaner


class InfluentialMonty():
    
    def goGoogleBlogs(self, search_me, driver, X):
        print("\n=========================================")
        print("MontGomery's Influential Tour...")
        print("=========================================\n")
        # Now to search Google News
        driver.get("https://google.com")
        time.sleep(1)
        driver.implicitly_wait(10)
        search = driver.find_element_by_class_name("gLFyf")
        search.click()
        search.send_keys(search_me)
        search.send_keys(Keys.RETURN)
        time.sleep(1)
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
        time.sleep(1)
        # Select News from google
        buzzword = "Tools"
        driver.implicitly_wait(10)
        news = driver.find_elements_by_class_name("hdtb-tl")
        for i in news:
            if buzzword in i.text:
                i.click()
                break
            else:
                pass
        time.sleep(1)
        # Select News from google
        buzzword = "All news"
        driver.implicitly_wait(10)
        news = driver.find_elements_by_class_name("mn-hd-txt")
        for i in news:
            if buzzword in i.text:
                i.click()
                break
            else:
                pass
        time.sleep(1)
        # Select News from google
        buzzword = "Blogs"
        driver.implicitly_wait(10)
        news = driver.find_elements_by_class_name("q")
        for i in news:
            if buzzword in i.text:
                i.click()
                break
            else:
                pass
        time.sleep(1)
        print("- Finding influential content...")
        # Get links for news articles
        n=0
        i_blogs_links = []
        i_blogs_articles = []
        i_blogs_dates = []
        while True:
            try:
                driver.implicitly_wait(10)
                if n<10:
                    pages = [i.text for i in driver.find_elements_by_class_name("fl")]
                    if len(pages)==1:
                        break
                    elif len(pages)==0:
                        break
                    else:
                        for i in driver.find_elements_by_class_name("l"):
                            i_blogs_links.append(i.get_attribute("href"))
                            i_blogs_articles.append(i.text)
                        for i in driver.find_elements_by_class_name("slp"):
                            i_blogs_dates.append(i.text)
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
        for i in i_blogs_links:
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
            del i_blogs_links[index]
        for index in sorted(indices_to_remove, reverse=True):
            del i_blogs_articles[index]   
        for index in sorted(indices_to_remove, reverse=True):
            del i_blogs_dates[index]
        print("- I've found", len(i_blogs_links), "blogs to read...")
        return i_blogs_links, i_blogs_articles, i_blogs_dates
    
    
    def extractGoogleBlogs(self, i_blogs_links, i_blogs_articles):
        i_blogs_corpus, i_blogs_entities = GoogleBlogsCleaner(i_blogs_links, i_blogs_articles)
        return i_blogs_corpus, i_blogs_entities


    def goMedium(self, search_me, driver):
        driver.get("https://medium.com/search?q")
        time.sleep(1)
        driver.implicitly_wait(10)
        search = driver.find_element_by_tag_name("input")
        search.click()
        search.send_keys(search_me)
        search.send_keys(Keys.RETURN)
        time.sleep(1)


    def getMedium(self, search_me, driver, X):
        n=0
        while True:
            if n<20:
                driver.execute_script("window.scrollTo(0, 10000000)")
                time.sleep(1)
                n+=1
            else:
                break
        time.sleep(1)
        # Get blog links
        driver.implicitly_wait(10)
        mediums = [i.text for i in driver.find_elements_by_tag_name("a")]
        i_medium_links = [i.get_attribute("href") for i in driver.find_elements_by_tag_name("a")]
        # Get read more links
        indices_to_remove1 = []
        n=0
        for i in mediums:
            if "Read more" in i:
                n+=1
            else:
                indices_to_remove1.append(n)
                n+=1
        for index in sorted(indices_to_remove1, reverse=True):
            del mediums[index]
            del i_medium_links[index]
        # Remove irrelevant links
        indices_to_remove2 = []
        n=0
        cnt = len(search_me.split())
        m=0
        abbrev = ""
        while m<cnt:
            first = search_me.split()[m][0]
            abbrev += first
            m+=1 
        for i in i_medium_links:
            if search_me in i.lower():
                n+=1              
            elif abbrev in i.lower():
                n+=1
            else:
                indices_to_remove2.append(n)
                n+=1      
        for index in sorted(indices_to_remove2, reverse=True):
            del i_medium_links[index]            
        print("- I've found", len(i_medium_links), "more blogs articles to read...")
        return i_medium_links


    def extractMedium(self, driver, i_medium_links, max_screen_width):
        driver.set_window_position(-(max_screen_width*5),0)
        i_medium_corpus, i_medium_entities, i_medium_authors, i_medium_dates = MediumCleaner(i_medium_links)
        return i_medium_corpus, i_medium_entities, i_medium_authors, i_medium_dates
    
    
    def blogsMerge(self, i_blogs_corpus, i_blogs_entities, i_blogs_links, i_medium_corpus, i_medium_links, i_medium_entities, i_medium_authors, i_medium_dates):
        for i in i_medium_corpus:
            i_blogs_corpus.append(i)
        for i in i_medium_entities:
            i_blogs_entities.append(i)
        for i in i_medium_links:
            i_blogs_links.append(i)
        i_blogs_authors = i_medium_authors
        i_blogs_dates = i_medium_dates
        return i_blogs_corpus, i_blogs_entities, i_blogs_links, i_blogs_authors, i_blogs_dates
        
        
    def goElsevier(self, search_me, driver):
        # Go to Elsevier
        insert_search = search_me.replace(" ", "%20")
        insert_search = '"'+insert_search+'"'
        insert_search = "search?qs="+insert_search+"&show=100&sortBy=relevance"
        #print("https://www.sciencedirect.com/"+insert_search)
        driver.get("https://www.sciencedirect.com/"+insert_search)
        time.sleep(2)
        #driver.implicitly_wait(10)
        # Search
        #search = driver.find_element_by_name("qs")
        #search = driver.find_element_by_css_selector(".SearchBox input")
        #search.click()
        #search.send_keys('"'+search_me+'"')
        #search.send_keys(Keys.RETURN)
        sign_in = [i.text for i in driver.find_elements_by_class_name("registration-header")]
        if 'Sign in to take advantage of the free personalised features' in sign_in:
            try:
                close = driver.find_element_by_xpath('/html/body/div[2]/div/div/div/button/span')
                close.click()
            except:
                close = driver.find_element_by_xpath('/html/body/div[3]/div/div/div/button/span')
                close.click()     
        else:
            pass
        check_box = [i for i in driver.find_elements_by_class_name("checkbox-label-value")]
        for i in check_box:
            if "Research articles" in i.text:
                i.click()
                break
            else:
                pass
        n=0
        while n<1:
            driver.execute_script("window.scrollTo(0, 10000000)")
            time.sleep(0.5)
            n+=1
        time.sleep(1)
        driver.implicitly_wait(10)
        display_100 = [i for i in driver.find_elements_by_tag_name("a")]
        for i in display_100:
            if "100" == i.text:
                i.click()
                break
            else:
                pass
        time.sleep(1)
        try:
            # Count pages
            base_url = driver.current_url
            driver.implicitly_wait(10)
            pages = driver.find_element_by_class_name("Pagination").text
            pages = pages.split()[-1]
            pages = pages.replace("next", "")
            pages = int(pages)
            # Get all titles, links and authors
            i_elsevier_titles = []
            i_elsevier_links = []
            i_elsevier_authors = []
            driver.implicitly_wait(10)
            for i in driver.find_elements_by_class_name("result-list-title-link"):
                i_elsevier_titles.append(i.text)
                i_elsevier_links.append(i.get_attribute("href")) 
            for i in driver.find_elements_by_class_name("Authors"):
                i_elsevier_authors.append(i.text)  
            n=1
            m=0
            print("- Finding research content...")
            if pages>10:
                pages = 2
            else:
                pass
            while n<pages:
                m=m+100
                url = base_url+"&offset="+str(m)
                driver.get(url)
                driver.implicitly_wait(10)
                for i in driver.find_elements_by_class_name("result-list-title-link"):
                    i_elsevier_titles.append(i.text)
                    i_elsevier_links.append(i.get_attribute("href"))
                for i in driver.find_elements_by_class_name("Authors"):
                    i_elsevier_authors.append(i.text)
                n+=1
            # Filter out irrelavent ones
            indices_to_remove = []
            n=0
            for i in i_elsevier_titles:
                if search_me.lower() not in i.lower():
                    indices_to_remove.append(n)
                    n+=1
                else:
                    n+=1
            for index in sorted(indices_to_remove, reverse=True):
                del i_elsevier_titles[index]
                del i_elsevier_links[index]
                del i_elsevier_authors[index]
        except:
            i_elsevier_titles = []
            i_elsevier_links = []
            i_elsevier_authors = []
        print("- I've found", len(i_elsevier_links), "research papers to read...")
        return i_elsevier_titles, i_elsevier_links, i_elsevier_authors
    

    def extractElsevier(self, i_elsevier_titles, i_elsevier_links, driver):
        i_elsevier_abstracts = ElsevierCleaner(i_elsevier_titles, i_elsevier_links, driver)
        return i_elsevier_abstracts
        

    def goArXiv(self, search_me, driver):
        # Go to arXiv
        insert_search = search_me.replace(" ", "+")
        insert_search = '"'+insert_search+'"'
        insert_search = "search/?query="+insert_search+"&searchtype=all&source=header"
        driver.get("https://arxiv.org/"+insert_search)
        time.sleep(2)
        # Search
        #driver.implicitly_wait(10)
        #search = driver.find_element_by_class_name("is-small")
        #search.click()
        #search.send_keys('"'+search_me+'"')
        #search.send_keys(Keys.ENTER)
        # Get all links and titles
        i_arxiv_links = []
        i_arxiv_titles = []
        n=0
        print("- Finding more research content...")
        while n<2:
            driver.implicitly_wait(10)
            for i in driver.find_elements_by_tag_name("a"):
                if "arXiv:" in i.text:
                    i_arxiv_links.append(i.get_attribute("href"))
                else:
                    pass
            for i in driver.find_elements_by_class_name("is-5"):
                i_arxiv_titles.append(i.text)

            try:
                next_button = driver.find_element_by_class_name("pagination-next")
                if 'Next' in next_button.text:
                    next_button.click()
                else:
                    break
            except:
                break   
            n+=1
        if i_arxiv_links:
            # Filter out irrelevant papers
            indices_to_remove = []
            n=0
            for i in i_arxiv_titles:
                if search_me.lower() not in i.lower():
                    indices_to_remove.append(n)
                    n+=1
                else:
                    n+=1
            for index in sorted(indices_to_remove, reverse=True):
                del i_arxiv_links[index]
                del i_arxiv_titles[index]
        print("- I've found", len(i_arxiv_links), "more research papers to read...")
        return i_arxiv_links, i_arxiv_titles
    
    
    def extractArxiv(self, i_arxiv_links, i_arxiv_titles):
        i_arxiv_abstracts, i_arxiv_authors = ArXivCleaner(i_arxiv_links, i_arxiv_titles)
        return i_arxiv_abstracts, i_arxiv_authors

    
    def researchMerge(self, i_elsevier_titles, i_elsevier_links, i_elsevier_authors, i_elsevier_abstracts, i_arxiv_links, i_arxiv_titles, i_arxiv_abstracts, i_arxiv_authors):
        # Merge titles, abstracts and authors and links
        i_research_titles = []
        i_research_links = []
        i_research_authors = []
        i_research_abstracts = []
        for i in i_elsevier_titles:
            i_research_titles.append(i)
        for i in i_arxiv_titles:
            i_research_titles.append(i)  
        for i in i_elsevier_links:
            i_research_links.append(i)
        for i in i_arxiv_links:
            i_research_links.append(i)
        for i in i_elsevier_authors:
            i_research_authors.append(i)
        for i in i_arxiv_authors:
            i_research_authors.append(i)    
        for i in i_elsevier_abstracts:
            i_research_abstracts.append(i)
        for i in i_arxiv_abstracts:
            i_research_abstracts.append(i)
        # Remove duplicated papers
        n=0
        indices_to_remove = []
        unique_papers = set()
        for i in i_research_titles:
            if i not in unique_papers:
                unique_papers.add(i)
            else:
                indices_to_remove.append(n)
            n+=1
        for index in sorted(indices_to_remove, reverse=True):
            del i_research_titles[index]
            del i_research_links[index]
            del i_research_authors[index] 
            del i_research_abstracts[index]
        return i_research_titles, i_research_links, i_research_authors, i_research_abstracts
        
