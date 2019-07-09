import sqlite3
import time
from textblob import TextBlob
from unidecode import unidecode
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
import json


conct = sqlite3.connect('twitter2.db')
cur = conct.cursor()


def table():
    try:
        cur.execute("CREATE TABLE IF NOT EXISTS tweet(UnixTime REAL, Tweets TEXT, Sentiment_Score REAL)")
        
        conct.commit()
    except Exception as ex:
        print(str(ex))
table()

#consumer key, consumer secret, access token, access secret.

conKey=""
conSecret=""
accToken=""
accSecret=""

class listener(StreamListener):

    def on_data(self, data): 
        try:
            data = json.loads(data) 
            Tweet = unidecode(data['text'])
            timeInMs = data['timestamp_ms'] 
            analysis = TextBlob(Tweet)
            
            sentiment  = analysis.sentiment.polarity
            print(timeInMs, Tweet, sentiment)
            cur.execute("INSERT INTO tweet (UnixTime, Tweets, Sentiment_Score) VALUES (?, ?, ?)",
            (timeInMs, Tweet, sentiment))
            conct.commit()

        except KeyError as er:
            print(str(er))
        return(True)

    def on_error(self, error):
        print(error)


while True:

    try:
        oauth = OAuthHandler(conKey, conSecret)
        oauth.set_access_token(accToken, accSecret)
        stream = Stream(oauth, listener())
        stream.filter(track=["a","e","i","o","u"])
    except Exception as ex:
        print(str(ex))
        time.sleep(5)
