import tweepy
import requests
import re
from os import environ
import time
import random
from datetime import datetime
from datetime import timedelta

APP_KEY = environ['CONSUMER_KEY']
APP_SECRET_KEY = environ['CONSUMER_SECRET']
BEARER_TOKEN = environ['BEARER_TOKEN']
oauth_token = environ['ACCESS_KEY']
oauth_secret = environ['ACCESS_SECRET']

since =  datetime.now() - timedelta(days=1)
since = since.isoformat() 
since = since[:-7] + "Z"

current = datetime.now()
current_time = current.strftime("%H:%M:%S")
current_time = current_time[:5]

def extract_trends(BEARER_TOKEN):
    url = 'https://api.twitter.com/1.1/trends/place.json?id=23424908'
    resp = requests.get(url, headers= {'Authorization': 'Bearer ' + BEARER_TOKEN
                                         })
    response = resp.json()
    trends = response[0]['trends']
    all_trends = []
    for trend in trends:
        all_trends.append(trend['name'])
    return all_trends
  
def clean_trend(collect_trend, trend):
    #collect_trend.remove(trend)
    clean_trends = []
    for trends in collect_trend:
        if " " in trends:
            trends = trends.replace(" ", "%20")
            clean_trends.append(trends)
        if "#" in trends:
            trends = trends.replace("#", "%23")
            clean_trends.append(trends)
        else: 
            clean_trends.append(trends)
    return clean_trends
  
def url(clean_trends, trend):
    collect_trend = trend
    if "#" in collect_trend:
        collect_trend = collect_trend.replace("#", "")
    if " " in trend:
        trend = trend.replace(" ", "%20")
    if "#" in trend:
        trend = trend.replace("#", "%23")
    doc = ""
    for x in clean_trends[0:25]:
        doc+= '-'
        doc+= '"'
        doc+=x
        doc+= '"'
        doc+="%20"
    url = 'https://twitter.com/search?q={}%20{}%20-from%3ARadioIsMyFriend%20-from%3Atruthbe_toldnow'.format(trend, doc)
    link = 'https://api.twitter.com/2/tweets/search/recent?query={}%20{}%20-from%3ARadioIsMyFriend%20-from%3Atruthbe_toldnow%20-is%3Aretweet%20-is:reply&start_time='.format(collect_trend, doc)
    return [link, url]
  
def detect_spammers(link):
    url = link[0] + since + '&tweet.fields=public_metrics&expansions=author_id&max_results=100'
    resp = requests.get(url, headers= {'Authorization': 'Bearer ' + BEARER_TOKEN
                                    })
    #print(resp.json())

    all_data = []
    data = resp.json()['data']
    includes = resp.json()['includes']['users']
    
    for d in data:
        all_data.append(d)
    
    while len(resp.json()['meta']) == 4:
        next_token = resp.json()['meta']['next_token']
        link = url + '&next_token={}'.format(next_token)

        resp = requests.get(link, headers= {'Authorization': 'Bearer ' + BEARER_TOKEN
                                    })
        include = resp.json()['includes']['users']
        for user in include:
            includes.append(user)
            daya = resp.json()['data']
        for d in daya:
            all_data.append(d)
    #print("issa goal")
      
    spam = []
    for tweet in all_data:
        if (tweet['text'].count("#") > 2) or (tweet['text'].count("|") > 1):
            spam.append(tweet)

    return [spam, all_data, includes]

def spammer_name(spam):
    spammers = []
    for spam_tweet in spam[0]:
        i_d = spam_tweet['id']
        for user in spam[2]:
            if i_d == user['id']:
                spammers.append(user['username'])
                break
    
    spammers = list(dict.fromkeys(spammers))
    return spammers

def update_link(spammers, link):
    doc = ""
    for handle in spammers[0:6]:
        spam_handle = "%20-from%3A" + handle
        doc += spam_handle
    updated_url = link[1] + doc + '&src=typed_query&f=live&lf=on'
    return updated_url

    
def get_highest_replies(spam):
    all_data = spam[1]
    r_id = [0, "", ""]
    for data in all_data:
        if data['public_metrics']['reply_count'] > r_id[0]:
            r_id[0] = data['public_metrics']['reply_count']
            r_id[1] = data['id']
            r_id[2] = data['text']
    return r_id

def star(r_id, spam):
    for user in spam[2]:
        if r_id[1] == user['id']:
            username = user['username']
            return username

def summarizer(r_id):

    body = r_id[2].encode('utf-8')
    resp = requests.post('https://api.smrzr.io/v1/summarize?num_sentences=1&algorithm=kmeans', data=body)
    print(resp.json())
    summary = resp.json()['summary']
    return summary  

def shorten_url(url):
    headers = {"Authorization": f"Bearer {'8793f1ef9f5b5a53bcba9b4c3fb224c212afbf9d'}"}
    groups_res = requests.get("https://api-ssl.bitly.com/v4/groups", headers=headers)
    groups_data = groups_res.json()['groups']
    guid = groups_data[0]['guid']
    shorten_res = requests.post("https://api-ssl.bitly.com/v4/shorten", 
                                json={"group_guid": guid, "long_url": url}, headers=headers)
    link = shorten_res.json().get("link")
    return link
               
auth = tweepy.OAuthHandler(APP_KEY, APP_SECRET_KEY)
auth.set_access_token(oauth_token, oauth_secret)
api = tweepy.API(auth)
               
def tweet_trend(url, summary, trend):
    if len(summary) > 190:
        summary = summary[0:190]
    response = '"{}" Read more about the {} trend here {}'.format(summary, trend, url)
    api.update_status(response)
    #print(response)
    
def tweet_why(username, r_id):
    tweet_url = "https://twitter.com/{}/status/{}".format(username, r_id[1])
    tweets = ['Wondering why {} is trending today? Here is why {}', 'Here is why {} is trending today {}', 'Why is {} trending today? Read this thread {}']
    choose = random.choice(tweets)
    tweet = choose.format(trend, tweet_url)
    api.update_status(tweet)
               
if current_time == "12:00":
    all_trends = extract_trends(BEARER_TOKEN)

    for trend in all_trends:
        print(trend)
        clean_trends = clean_trend(all_trends, trend)
        urls = url(clean_trends, trend)
        spammers_n_data = detect_spammers(urls)
        spammers = spammer_name(spammers_n_data)
        url_update = update_link(spammers, urls)
        short_url = shorten_url(url_update)
        replies = get_highest_replies(spammers_n_data)
        user_name = star(replies, spammers_n_data)
        summary = summarizer(replies)
        #print(summary)
        short_url = shorten_url(url_update)
        #print(short_url)
        tweet_trend(short_url, summary, trend)
        time.sleep(300)
        tweet_why(user_name, replies)
        time.sleep(600)   
