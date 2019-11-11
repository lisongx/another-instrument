import wptools
import requests
import pywikibot

_SPARQL_QUERY = "SELECT ?id  WHERE {?id wdt:P279+ wd:Q34379 .}"
_WIKIDATA_SPARQL = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"


def get_all_item_ids():
    r = requests.get(
        _WIKIDATA_SPARQL,
        params={
            'query': _SPARQL_QUERY,
            'format': 'json'
        }
    )
    assert r.status_code == 200
    items = r.json()['results']['bindings']
    ids = [item['id']['value'].split('/')[-1] for item in items]
    return ids


def get_item_page_by_id(wd_id):
    site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()
    return pywikibot.ItemPage(repo, wd_id)


def get_tweet_data_by_id(wd_id):
    item = get_item_page_by_id(wd_id)
    item_dict = item.get()
    print(item_dict)


get_tweet_data_by_id('Q3538954')
