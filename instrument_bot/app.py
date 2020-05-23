import os
import requests
import random
import io
from config import TWITTER_CONFIG

from wiki_service import get_all_items, get_item_data

import tweepy


def get_tweet_client():
    auth = tweepy.OAuthHandler(
        TWITTER_CONFIG['api_key'],
        TWITTER_CONFIG['api_secret']
    )
    auth.set_access_token(TWITTER_CONFIG['access_token'], TWITTER_CONFIG['access_secret'])

    api = tweepy.API(auth)
    return api


def get_random_data(items):
    wd_item = random.sample(items, 1)[0]
    return get_item_data(wd_item)


def get_tweet_data():
    items = get_all_items()
    return get_random_data(items)


def gen_status_from_data(data):
    if data['image_description']:
        return "%s (%s) %s" % (data['title'], data['image_description'], data['image_source_url'])

    return "%s %s" % (data['title'], data['image_source_url'])


if __name__ == "__main__":
    api = get_tweet_client()
    data = get_tweet_data()
    image_url = data['image_url']
    _, filename = os.path.split(image_url)

    try:
        api.verify_credentials()
        print("Authentication OK")
        print(image_url)
        image_file = io.BytesIO(requests.get(image_url).content)
        media = api.media_upload(filename=filename, file=image_file)
        status = gen_status_from_data(data)
        api.update_status(status=status, media_ids=[media.media_id])
        import ipdb;
        ipdb.set_trace()
    except Exception as e:
        print(e)
        print("Error during authentication")


