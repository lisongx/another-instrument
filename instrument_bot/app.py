import os
import io
import requests
import random
import logging
from datetime import datetime

from wiki_service import get_all_items, get_item_data
from config import TWITTER_CONFIG

import tweepy
import redis
from retry import retry

ITEMS_KEY = 'items'

def get_tweet_client():
    auth = tweepy.OAuthHandler(
        TWITTER_CONFIG['api_key'],
        TWITTER_CONFIG['api_secret']
    )
    auth.set_access_token(TWITTER_CONFIG['access_token'], TWITTER_CONFIG['access_secret'])

    api = tweepy.API(auth)
    return api


@retry(tries=5, delay=10)
def get_random_data(items):
    wd_item = random.sample(items, 1)[0]
    ret = get_item_data(wd_item)
    if not ret:
        raise Exception("invalid item")
    return ret

def get_tweet_data(all_posted):
    items = get_all_items()
    print("Got Items, %s" % len(items))
    filterd_items = [item for item in items if item['id'] not in all_posted]
    print("After filter posted Items, %s" % len(filterd_items))
    return get_random_data(filterd_items)


def gen_status_from_data(data):
    if data['image_description']:
        return "%s (%s) %s" % (data['title'], data['image_description'], data['image_source_url'])

    return "%s %s" % (data['title'], data['image_source_url'])


class DataClient(object):
    def __init__(self):
        self.rds = redis.from_url(os.environ.get("REDISTOGO_URL"))
        self.key = ITEMS_KEY

    def get_all_posted_item_ids(self):
        return [item.decode('utf-8') for item in self.rds.smembers(self.key)]

    def add_posted_item_id(self, item_id):
        return self.rds.sadd(self.key, item_id)


def exit_for_cron_time_checking():
    hour = datetime.now().hour
    if hour not in [10, 19, 0]:
        return True


def main():
    if os.environ.get('PRODUCTION') and exit_for_cron_time_checking():
        print("exit because not the right time")
        return

    data_client = DataClient()
    all_posted = data_client.get_all_posted_item_ids()
    api = get_tweet_client()
    data = get_tweet_data(all_posted)
    image_url = data['image_url']
    _, filename = os.path.split(image_url)

    try:
        api.verify_credentials()
        print("Authentication OK")
        print(image_url)
        status_text = gen_status_from_data(data)
        print("Ready to send tweet", status_text)
        image_file = io.BytesIO(requests.get(image_url).content)
        media = api.media_upload(filename=filename, file=image_file)
        status = api.update_status(status=status_text, media_ids=[media.media_id])
        print("Sent tweet", status.entities['urls'])
        data_client.add_posted_item_id(data['wd_id'])
    except Exception as e:
        print("Send Error", e)


if __name__ == "__main__":
    logging.basicConfig()
    main()
