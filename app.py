import tweepy
from config import TWITTER_CONFIG

auth = tweepy.OAuthHandler(
    TWITTER_CONFIG['api_key'],
    TWITTER_CONFIG['api_secret']
)
auth.set_access_token(TWITTER_CONFIG['access_token'], TWITTER_CONFIG['access_secret'])

api = tweepy.API(auth)

try:
    api.verify_credentials()
    print("Authentication OK")
except Exception as e:
    print(e)
    print("Error during authentication")
