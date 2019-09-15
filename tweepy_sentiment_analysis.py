##########################################################################
#                                                                        #
# Please read the documentation for full details how to use this app     #
#                                                                        #
##########################################################################
from tweepy import API
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from textblob import TextBlob

import twitter_credentials
import numpy as np
import pandas as pd
import re
import matplotlib.pyplot as plt

#Twitter Client class
class TwitterClient():
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)

        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

    def get_user_timeline_tweets(self, num_tweets):
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
            tweets.append(tweet)
        return tweets

    def get_friend_list(self, num_friends):
        friend_list = []
        for friend in Cursor(self.twitter_client.friends, id=self.twitter_user).items(num_friends):
            friend_list.append(friend)
        return friend_list

    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_client.home_timeline, id=self.twitter_user).items(num_tweets):
                home_timeline_tweets.append(tweet)
        return home_timeline_tweets

#Twitter Authenticator class
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        #Authenticates from your credentials in twitter_credentials
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth

#Twitter Streamer class
class TwitterStreamer():
    #Handles the streaming and processing live tweets.

    def __init__(self):
        self.twitter_authenticator = TwitterAuthenticator()

    def stream_tweets(self, fetched_tweets_filename, hash_tag_list):
        #Handles Twitter auth and the connection to Twitter
        listener = TwitterListener(fetched_tweets_filename)
        auth = self.twitter_authenticator.authenticate_twitter_app()
        stream = Stream(auth, listener)
        stream.filter(track=hash_tag_list)

#Twitter Listener class
class TwitterListener(StreamListener):
    #This is a basic listener that just prints received tweets to stdout.

    def __init__(self, fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data):
        try:
            print(data)
            with open(self.fetched_tweets_filename, 'a') as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print("Error on_data %s" % str(e))
        return True


    def on_error(self, status):
        if status == 420:
            #Returning false on data method in case rate limit is reached.
            return False
        print(status)

class TweetAnalyser():
    #Functionality for analysing and catergorising content from tweets

    def clean_tweet(self, tweet):
        #Remove any special chars from string etc
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyse_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))

        #Tell you if the tweet is a positive or negative one
        if analysis.sentiment.polarity > 0:
            #Positive
            return 1
        elif analysis.sentiment.polarity == 0:
            #Neutral
            return 0
        else:
            #Negative
            return -1

    def tweets_to_data_frame(self, tweets):
        #Functionality provided by pandas
        #Loop through every single tweet in tweets where object equals .text
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['Tweets'])

        #Tweet ID
        df['ID'] = np.array([tweet.id for tweet in tweets])
        #Tweet length
        df['Length'] = np.array([len(tweet.text) for tweet in tweets])
        #Date created
        df['Date'] = np.array([tweet.created_at for tweet in tweets])
        #Where the tweet came from E.g. Android
        df['Source'] = np.array([tweet.source for tweet in tweets])
        #Number of likes
        df['Likes'] = np.array([tweet.favorite_count for tweet in tweets])
        #Number of retweets
        df['Retweets'] = np.array([tweet.retweet_count for tweet in tweets])

        return df

if __name__ == '__main__':

    twitter_client = TwitterClient()
    tweet_analyser = TweetAnalyser()
    api = twitter_client.get_twitter_client_api()

    #user_timeline function from twitter api - Specify your user and
    #how many tweets you would like to see e.g. screen_name="realDonaldTrump" count=20.
    tweets = api.user_timeline(screen_name="realDonaldTrump", count=20)

    #What types can be extracted from the tweet? Use the print line below.
    #print(dir(tweets[0]))

    df = tweet_analyser.tweets_to_data_frame(tweets)
    df['Sentiment'] = np.array([tweet_analyser.analyse_sentiment(tweet) for tweet in df['Tweets']])

    #Print the first 10 to console.
    print(df.head(10))

    #Get the number of likes for most liked tweet
    #print(np.max(df['Likes']))

    #Get the number of likes and retweets on the date and plot on a graph
    time_likes = pd.Series(data=df['Likes'].values, index=df['Date'])
    time_likes.plot(figsize=(16, 4), label="Likes", legend=True)
    time_retweets = pd.Series(data=df['Retweets'].values, index=df['Date'])
    time_retweets.plot(figsize=(16, 4), label="Retweets", legend=True)
    plt.show()
