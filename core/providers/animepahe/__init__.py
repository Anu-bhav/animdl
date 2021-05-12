"""
AnimePahe is supposed to provide us with superior qualities. :P
"""

import re

import requests

API_URL = "https://animepahe.com/api"
SITE_URL = "https://animepahe.com/"

KWIK_RE = re.compile(r"Plyr\|querySelector\|document\|([^\\']+)")

# https://animepahe.com/play/239f0d07-3a6d-616e-ed8c-f2f1a9489463/d288b66b298f54f727d2741cd512ce2becb07d91686de759658a08fa3a0e40f0

# https://animepahe.com/api?m=release&id=4&l=30&sort=episode_desc&page=33

ID_RE = re.compile(r"/api\?m=release&id=([^&]+)")

def get_session_page(session, page, release_id):
    
    with session.get(API_URL, params={'m': 'release', 'id': release_id, 'sort': 'episode_desc', 'page': page}) as response:
        return response.json()

def get_m3u8_from_kwik(session, kwik_url):
    
    with session.get(kwik_url, headers={'referer': SITE_URL}) as kwik_page:
        match = KWIK_RE.search(kwik_page.text).group(1)
        
    return "{10}://{9}-{8}-{7}.{6}.{5}/{4}/{3}/{2}/{1}.{0}".format(*match.split('|'))

def get_stream_url(session, release_id, stream_session):
    
    with session.get(API_URL, params={'m': 'links', 'id': release_id, 'session': stream_session, 'p': 'kwik'}) as stream_url_data:
        content = stream_url_data.json().get('data', [])
        
    for d in content:
        for quality, data in d.items():
            yield {'quality': quality, 'headers': {'referer': data.get('kwik')}, 'stream_url': get_m3u8_from_kwik(session, data.get('kwik'))}
    

def get_stream_urls_from_data(session, release_id, data, check):
    for content in reversed(data):
        if check(content.get('episode', 0)):
            yield [*get_stream_url(session, release_id, content.get('session'))]  

def predict_pages(total, check):
    """
    A calculative call to minimize API calls :P.
    """
    for x in range(1, total + 1):
        if check(x):
            yield (total - x) // 30 + 1
        

def fetcher(session: requests.Session, url, check):
    with session.get(url) as anime_page:
        release_id = ID_RE.search(anime_page.text).group(1)
    
    fpd = get_session_page(session, '1', release_id)

    if fpd.get('last_page') == 1:
        yield from get_stream_urls_from_data(session, release_id, fpd.get('data'), check)
        return

    for pages in predict_pages(fpd.get('total'), check):
        yield from get_stream_urls_from_data(session, release_id, get_session_page(session, str(pages), release_id).get('data'), check)