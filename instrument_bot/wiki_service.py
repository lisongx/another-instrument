import json
import random
from collections import defaultdict
from xml.dom.minidom import parseString as parseDomString

import mwclient
import wptools
import requests

COMMONS_LINK = 'commons.wikimedia.org'

SPARQL_QUERY = """
    SELECT DISTINCT ?item ?image ?common ?itemLabel  (group_concat(?langLabel;separator=",") as ?langLabels)   WHERE {
        ?item wdt:P279+ wd:Q34379 .

         OPTIONAL  {
           ?item wdt:P18 ?image.
         }

        OPTIONAL  {
          ?item wdt:P373 ?common.
        }

     ?item wikibase:sitelinks ?sitelinks .

      OPTIONAL {
        ?item  wdt:P495  ?country.
        ?country wdt:P37  ?wikilang.
        ?wikilang wdt:P218 ?wikilangCode.
        ?item rdfs:label ?langLabel FILTER(LANG(?langLabel) = ?wikilangCode).
      }

      FILTER (
        bound(?common) || bound(?image) || (?sitelinks > 0)
     )

      ?item rdfs:label ?itemLabel FILTER(LANG(?itemLabel)  IN ('en', 'en-gb') ).
#      ?item schema:description ?itemDesc FILTER(LANG(?itemDesc)  IN ('en', 'en-gb') ).
    } GROUP BY ?item ?image ?common ?itemLabel
"""

WIKIDATA_SPARQL = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"

COMMONS_NAMESPACE_IMAGE = 6

commons = mwclient.Site(COMMONS_LINK)


def get_entity_data(wd_id):
    r = requests.get('https://www.wikidata.org/wiki/Special:EntityData/%s.json' % wd_id)
    data = r.json()
    return data['entities'].get(wd_id)


def shortern_url(url):
    r = requests.post(
        "https://meta.wikimedia.org/w/api.php",
        data = {
            'action':  'shortenurl',
            'url': url,
            'format': 'json'
        }
    )
    assert r.status_code == 200, "URL shortern failed!"
    data = r.json()
    print("Shorten url response", data)
    return data['shortenurl']['shorturl']


def get_images_from_commons_category(category_name):
    category = commons.categories[category_name]
    images =  list(category.members(namespace=COMMONS_NAMESPACE_IMAGE))
    # Get First one
    if len(images) > 0:
        image = images[0]
        page = wptools.page(image.name, wiki=COMMONS_LINK)
        page.get()
        page.get_imageinfo()
        return page.data['image'][0]


def get_all_items():
    r = requests.get(
        WIKIDATA_SPARQL,
        params={
            'query': SPARQL_QUERY,
            'format': 'json'
        }
    )
    assert r.status_code == 200
    items = r.json()['results']['bindings']
    for item in items:
        item['id'] = item['item']['value'].split('/')[-1]
    return items


def get_item_page_by_id(wd_id):
    page = wptools.page(wikibase=wd_id)
    page.get_wikidata()
    return page


def get_image_by_item(item):
    images = item.data.get('image', [])
    claims = item.data.get('claims', {})
    common_categories = claims.get('P373', [])
    if len(images) > 0:
        return images[0]
    # Try get commons gallery
    elif len(common_categories) > 0:
        common_category = common_categories[0]
        return get_images_from_commons_category(common_category)


def get_item_title(item):
    if item.get('itemLabel'):
        return item['itemLabel']['value']
    elif item.get('langLabels'):
        return item['itemLabel']['value'].split(',')[0]


def get_commons_author_name(dom_string):
    dom = parseDomString(dom_string)
    return dom.documentElement.firstChild.nodeValue


def get_image_description_text(image):
    metadata = image['metadata']
    if metadata['Copyrighted']['value'] == 'True':
        license_name = metadata['LicenseShortName']['value']
        try:
            artist = get_commons_author_name(image['metadata']['Artist']['value'])
        except KeyError:
            print("Could not find the artist name!", image['metadata'])
            return None
        return "Photo by %s, %s" % (artist, license_name)


def get_site_link_by_entity_data(data):
    sitelinks = data['sitelinks']
    if len(sitelinks) == 0:
        return

    if 'enwiki' in sitelinks:
        return sitelinks['enwiki']['url']
    return sitelinks.values()[0]['url']

def get_item_data(wd_item):
    title = get_item_title(wd_item)
    if not title:
        return
    wd_id = wd_item['id']
    item = get_item_page_by_id(wd_id)
    image = get_image_by_item(item)
    if not image:
        return

    entity_data = get_entity_data(wd_id)
    site_link = get_site_link_by_entity_data(entity_data)
    if not site_link:
        return

    data = dict(
        wd_id=wd_id,
        title=title.capitalize(),
        site_link=site_link,
        image_url=image['url'],
        image_description=get_image_description_text(image),
        image_source_url=image['descriptionurl']
    )
    return data
