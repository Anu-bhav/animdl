import functools

import regex

DAILYMOTION_VIDEO = regex.compile(r"/embed/video/([^&?/]+)")

def iter_urls(qualities):
    for name, data in qualities.items():
        for url in data:
            yield url.get('url')

def extract(session, url, **opts):
    match = DAILYMOTION_VIDEO.search(url)

    if not match:
        return []

    metadata_uri = "https://www.dailymotion.com/player/metadata/video/{}".format(match.group(1))

    metadata = session.get(metadata_uri).json()
    subtitles = functools.reduce(list.__add__, (data.get('urls') for language, data in metadata.get('subtitles', {}).get('data').items()), [])
    
    return list({
        'stream_url': content_uri, **({'subtitles': subtitles} if subtitles else {})
    } for content_uri in iter_urls(metadata.get('qualities')))