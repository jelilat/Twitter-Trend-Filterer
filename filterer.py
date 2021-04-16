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
    tweet = tweet.replace("@filtertrend filter ", "")
    if tweet in all_trends:
        all_trends.remove(tweet)
    if "#" in tweet:
        tweet = tweet.replace("#", "%23")
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
    for x in clean_trends[0:25]:
        doc+= '-'
        doc+= '"'
        doc+=x
        doc+= '"'
        doc+="%20"
    url = 'https://twitter.com/search?q="{}"%20{}%20min_replies%3A2%20-filter%3Areplies&src=typed_query&f=live&lf=on'.format(collect_trend[1], doc)
    return url

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
    response = '@{} Hey buddy! Follow this format to get a link to your filtered trend (@filtertrend filter "trend_name")'.format(caller)
    api.update_status(response, tweet_id)

class StreamListener(tweepy.StreamListener):
    def on_status(self, status):
        tweet = status.text
        caller = status.user
        caller = caller.screen_name
        tweet_id = status.id_str
        if re.match('(@filtertrend filter "\w+\s\w+\")', tweet) or re.match('(@filtertrend filter "\w+\")', tweet):
            trends = extract_trends(BEARER_TOKEN)
            filter_trend = collect_trend(tweet, trends)
            clean_trends = clean_trend(filter_trend)
            link = url(clean_trends, filter_trend)
            shortened_url = shorten_url(link)
            respond(caller, shortened_url, tweet_id)
        else:
            negative_response(caller, tweet_id)  
        
    def on_error(self, status_code):
        if status_code != 200:
            return False

def main():
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
    stream.filter(track=["@filtertrend"])
               
if __name__ == "__main__":
    main()
