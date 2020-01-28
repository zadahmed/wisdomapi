# Factual Monty file including FactualMonty class

# Imports
import requests
import os
import time
import re
import time
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from FactualCleaner import wikiCleaner


class FactualMonty():
    
    def goWikipediaWhat(self, search_me, driver):
        print("\n==========================================")
        print("MontGomery's Fact Finding Tour...")
        print("==========================================\n")
        print("- Finding a trustworthy source...")
        driver.get("https://www.wikipedia.org")
        driver.implicitly_wait(10)
        search = driver.find_element_by_id("searchInput")
        search.click()
        search.send_keys(search_me)
        search.send_keys(Keys.RETURN)


    def getWikipediaWhat(self, driver):
        f_wiki_url = requests.get(driver.current_url)
        raw_data = f_wiki_url.text
        f_wiki_soup = BeautifulSoup(raw_data, 'html.parser')
        return f_wiki_soup
    
    
    def goWikipediaWhen(self, search_me, driver):
        driver.get("https://www.wikipedia.org")
        driver.implicitly_wait(10)
        driver.find_element_by_class_name("pure-button").click()
        search = driver.find_element_by_name("search")
        search_key = "history of "+search_me
        search.send_keys(search_key)
        search.send_keys(Keys.RETURN)
        
    
    def getWikipediaWhen(self, driver, search_me):
        history_links = []
        f_history_type = ""
        search_key = "history of "+search_me
        print("- Finding significant events in history...")
        for i in driver.find_elements_by_tag_name("a"):
            n=0
            for j in search_key.split(" "):
                if j in i.text.lower():
                    n+=1
            if n==len(search_key.split()):
                if "redlink" in i.get_attribute("href"):
                    pass
                else:
                    history_links.append(i.get_attribute("href"))
        if history_links:
            driver.get(history_links[0])
            time.sleep(2)
            history_link = driver.current_url
            f_history_url = requests.get(history_link)  
            raw_data = f_history_url.text
            f_history_soup = BeautifulSoup(raw_data, 'html.parser')
            if "history" in history_link.lower():
                f_history_type += "history of"
            elif "timeline" in history_link.lower():
                f_history_type += "timeline of"
        else:
            f_history_soup = ["NO DATA"]
            f_history_type = " "
        return f_history_soup, f_history_type
    
    
    def wikiSummary(self, f_wiki_soup, f_history_soup, f_history_type, search_me):
        f_what_summary, f_old_history_summary_sorted, f_history_summary_sorted = wikiCleaner(f_wiki_soup, f_history_soup, f_history_type, search_me)
        return f_what_summary, f_old_history_summary_sorted, f_history_summary_sorted
        