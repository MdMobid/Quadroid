import requests
import json
from Main.speak_text import speak_text
from Main.quadpath import quadpath

# Imports From The Databases
congif_path = quadpath('Databases', 'config.json')
with open(congif_path, "r") as f:
    data = json.load(f)

def newsfunc(topic_word):
    
    # INITIALIZING YOUR API KEY HERE FROM DATABASES
    api_keys = data["api_keys"]
    api_key = api_keys["NEWS_API_KEY"]

    # No.of News You want to listen in One go:
    news_counter=3

    #Country Selection:
    country="in"

    def get_news(topic):
        # Make a request to the news API and retrieve articles related to the topic
        url=f'https://newsapi.org/v2/top-headlines?country={country}&category={topic}&sortBy=popularity&apiKey={api_key}'
        #print(url)
        response = requests.get(url)
        articles = response.json()['articles']
        return articles
                    
    def extract_information(article):
        # Extract information from the article
        title = article['title']
        if 'description' in article:
            description = article['description']
            return title, description
        else:
            return None, None

                    
    def present_news(articles):
        # Create a string to store the news articles
        news_str = ''
        counter = 1
        for article in articles:
            title, description = extract_information(article)
            if title is None:
                continue
            if description is None:
                continue
            news_str += f'{counter}. {title}\n'
            news_str += f'{description}\n\n'
            counter += 1
            if counter == news_counter+1:
                break
        return news_str
    
    
    topic = topic_word
    articles = get_news(topic)
    news_str = present_news(articles)
    print()
    print(news_str)
    speak_text(news_str)