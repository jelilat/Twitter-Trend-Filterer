import tweepy
import requests
import re
from os import environ

APP_KEY = environ['CONSUMER_KEY']
APP_SECRET_KEY = environ['CONSUMER_SECRET']
BEARER_TOKEN = environ['BEARER_TOKEN']
oauth_token = environ['ACCESS_KEY']
oauth_secret = environ['ACCESS_SECRET']

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

def collect_trend(tweet, all_trends):
    tweet = tweet.lower()
    print(tweet)
    tweet = tweet.replace("@filtertrend filter ", "")
    print(tweet)
    if '"' in tweet:
        tweet = tweet.replace('"', '')
    hash_tweet = "#" + tweet
    
    for trend in all_trends:
        if (tweet.lower() == trend.lower()) or (hash_tweet.lower() == trend.lower()):
            all_trends.remove(trend)
            
    if "," in tweet:
        tweet = tweet.replace(",", "%2C")
        split_tweet = tweet.split(",")
        
        for twit in split_tweet:
            hash_split = "#" + twit
            if (twit in all_trends) or (twit.lower() in all_trends):
                all_trends.remove(twit)
            if hash_split in all_trends:
                all_trends.remove(hash_split)
            if "#" in twit:
                tweet = twit.replace("#", "%23")
    else:
        if (tweet in all_trends) or (tweet.lower() in all_trends):
            all_trends.remove(tweet)
        if hash_tweet in all_trends:
            all_trends.remove(hash_tweet)
        if "#" in tweet:
            tweet = tweet.replace("#", "%23")
    if ' ' in tweet:
        tweet = tweet.replace(' ', '%20')
    
    return [all_trends, tweet]

def clean_trend(collect_trend):
    collect_trend = collect_trend[0]
    clean_trends = []
    for trends in collect_trend:
        if " " in trends:
            trends = trends.replace(" ", "%20")
            clean_trends.append(trends)
        elif "#" in trends:
            trends = trends.replace("#", "%23")
            clean_trends.append(trends)
        else: 
            clean_trends.append(trends)
    return clean_trends

def url(clean_trends, collect_trend):
    doc = ""
    for x in clean_trends[0:21]:
        doc+= '-'
        doc+= '"'
        doc+=x
        doc+= '"'
        doc+="%20"
    url = 'https://twitter.com/search?q={}%20{}%20-from%3ARadioIsMyFriend%20-from%3Atruthbe_toldnow'.format(collect_trend[1], doc)
    link = 'https://api.twitter.com/2/tweets/search/recent?query={}%20{}%20-from%3ARadioIsMyFriend%20-from%3Atruthbe_toldnow%20-is%3Aretweet'.format(collect_trend[1], doc)
    return [url, link]

def detect_spammers(link):
    url = link[1] + '&expansions=author_id&max_results=100'
    resp = requests.get(url, headers= {'Authorization': 'Bearer ' + BEARER_TOKEN
                                     })
    tweets = resp.json()['data']
    spam = []
    for tweet in tweets:
        if (tweet['text'].count("#") > 2) or (tweet['text'].count("|") > 1):
            spam.append(tweet)
        
    return spam

def spammer_name(spam):
    spammers = []
    for spam_tweet in spam:
        i_d = spam_tweet['author_id']
        url = 'https://api.twitter.com/1.1/users/lookup.json?user_id={}'.format(i_d)
        response = requests.get(url, headers= {'Authorization': 'Bearer ' + BEARER_TOKEN
                                         })
        spammer = response.json()[0]['screen_name']
        spammers.append(spammer)
    
    spammers = list(dict.fromkeys(spammers))
    return spammers

def update_link(spammers, link):
    doc = ""
    for handle in spammers[0:6]:
        spam_handle = "%20-from%3A" + handle
        doc += spam_handle
    updated_url = link[0] + doc + '&src=typed_query&f=live&lf=on'
    return updated_url

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

def respond(caller, url, tweet_id):
    response = "@{} Hey buddy! Here's the link to your filtered trend {}".format(caller, url)
    api.update_status(response, tweet_id)
               
def negative_response(caller, tweet_id):
    response = '@{} Hey {}! Follow this format to get a link to your filtered trend (@filtertrend filter "trend_name")'.format(caller, caller)
    api.update_status(response, tweet_id)

def thanks(caller, tweet_id):
    response = '@{} Thanks for mentioning @filtertrend'.format(caller)
    api.update_status(response, tweet_id)

class StreamListener(tweepy.StreamListener):
    def on_status(self, status):
        tweet = status.text
        caller = status.user
        caller = caller.screen_name
        tweet_id = status.id_str
        if "#" in tweet:
            twit = tweet.replace("#", "")
        else:
            twit = tweet
        if caller != "filtertrend":
            if re.match('(@filtertrend filter ("?#?\w+,?\s?"?)+)', twit, re.IGNORECASE):
                trends = extract_trends(BEARER_TOKEN)
                filter_trend = collect_trend(tweet, trends)
                clean_trends = clean_trend(filter_trend)
                link = url(clean_trends, filter_trend)
                spam = detect_spammers(link)
                spammers = spammer_name(spam)
                link_update = update_link(spammers, link)
                shortened_url = shorten_url(link_update)
                respond(caller, shortened_url, tweet_id)
            #elif re.match('(.+ @filtertrend .+)', twit) or re.match('(.+ @filtertrend)', twit):
                #thanks(caller, tweet_id)
            #else:
                #negative_response(caller, tweet_id)  
        
    def on_error(self, status_code):
        if status_code != 200:
            return False

def main():
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
    stream.filter(track=["@filtertrend"])
               
if __name__ == "__main__":
    main()
