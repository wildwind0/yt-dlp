from .common import InfoExtractor
from ..utils import (
    clean_html,
    clean_podcast_url,
    int_or_none,
    parse_iso8601,
    str_or_none,
)
from ..utils.traversal import traverse_obj


class ApplePodcastsIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://podcasts\.apple\.com/
        (?:(?P<country>[^/?#]+)/)?podcast
        (?:/(?!id\d+(?:[/?#]|$))[^/?#]+)*(?:/id(?P<collection_id>\d+))?
        [^#]*?[?&]i=(?P<id>\d+)'''
    _TESTS = [{
        'url': 'https://podcasts.apple.com/us/podcast/urbana-podcast-724-by-david-penn/id1531349107?i=1000748574256',
        'md5': 'f8a6f92735d0cfbd5e6a7294151e28d8',
        'info_dict': {
            'id': '1000748574256',
            'ext': 'm4a',
            'title': 'URBANA PODCAST 724 BY DAVID PENN',
            'episode': 'URBANA PODCAST 724 BY DAVID PENN',
            'description': 'md5:fec77bacba32db8c9b3dda5486ed085f',
            'upload_date': '20260206',
            'timestamp': 1770400801,
            'duration': 3602,
            'series': 'Urbana Radio Show',
            'thumbnail': 're:.+[.](png|jpe?g|webp)',
        },
    }, {
        'url': 'https://podcasts.apple.com/us/podcast/207-whitney-webb-returns/id1135137367?i=1000482637777',
        'md5': 'baf8a6b8b8aa6062dbb4639ed73d0052',
        'info_dict': {
            'id': '1000482637777',
            'ext': 'mp3',
            'title': '207 - Whitney Webb Returns',
            'episode': '207 - Whitney Webb Returns',
            'episode_number': 207,
            'description': 'md5:75ef4316031df7b41ced4e7b987f79c6',
            'upload_date': '20200705',
            'timestamp': 1593932400,
            'duration': 5369,
            'series': 'The Tim Dillon Show',
            'thumbnail': 're:.+[.](png|jpe?g|webp)',
        },
    }, {
        'url': 'https://podcasts.apple.com/podcast/207-whitney-webb-returns/id1135137367?i=1000482637777',
        'only_matching': True,
    }, {
        'url': 'https://podcasts.apple.com/podcast/207-whitney-webb-returns?i=1000482637777',
        'only_matching': True,
    }, {
        'url': 'https://podcasts.apple.com/podcast/id1135137367?i=1000482637777',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        match = self._match_valid_url(url)
        episode_id, collection_id = match.group('id', 'collection_id')

        # The Podcasts web frontend is occasionally unavailable (and may return
        # HTTP 500), whereas the iTunes lookup API exposes the publisher's RSS
        # enclosure URL directly. Prefer it so that downloads do not depend on
        # Apple rendering the episode page.
        if collection_id:
            lookup = self._download_json(
                'https://itunes.apple.com/lookup', episode_id, 'Downloading podcast metadata',
                fatal=False, query={
                    'id': collection_id,
                    'entity': 'podcastEpisode',
                    'country': match.group('country') or 'us',
                    'limit': 200,
                }) or {}
            episode = traverse_obj(lookup, (
                'results', lambda _, v: str_or_none(v.get('trackId')) == episode_id, {dict}, any))
            episode_url = traverse_obj(episode, ('episodeUrl', {clean_podcast_url}))
            if episode_url:
                return {
                    'id': episode_id,
                    **traverse_obj(episode, {
                        'title': ('trackName', {str}),
                        'description': ('description', {str}),
                        'timestamp': ('releaseDate', {parse_iso8601}),
                        'duration': ('trackTimeMillis', {int_or_none(scale=1000)}),
                        'episode': ('trackName', {str}),
                        'series': ('collectionName', {str}),
                        'thumbnail': ('artworkUrl600', {str}),
                    }),
                    'url': episode_url,
                    'vcodec': 'none',
                }

        webpage = self._download_webpage(url, episode_id)
        server_data = self._search_json(
            r'<script [^>]*\bid=["\']serialized-server-data["\'][^>]*>', webpage,
            'server data', episode_id)['data'][0]['data']
        model_data = traverse_obj(server_data, (
            'headerButtonItems', lambda _, v: v['$kind'] == 'share' and v['modelType'] == 'EpisodeLockup',
            'model', {dict}, any))

        return {
            'id': episode_id,
            **traverse_obj(model_data, {
                'title': ('title', {str}),
                'description': ('summary', {clean_html}),
                'url': ('playAction', 'episodeOffer', 'streamUrl', {clean_podcast_url}),
                'timestamp': ('releaseDate', {parse_iso8601}),
                'duration': ('duration', {int_or_none}),
                'episode': ('title', {str}),
                'episode_number': ('episodeNumber', {int_or_none}),
                'series': ('showTitle', {str}),
            }),
            'thumbnail': self._og_search_thumbnail(webpage),
            'vcodec': 'none',
        }
