import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    parse_qs,
    qualities,
    traverse_obj,
    url_or_none,
    urljoin,
)


class CETVPlayerIE(InfoExtractor):
    IE_NAME = 'cetv:player'
    IE_DESC = '中国教育电视台播放器'
    _VALID_URL = r'https?://app\.cetv\.cn/video/player/index\?(?P<id>[^#]+)'
    _EMBED_REGEX = [r'''(?x)
        <iframe[^>]+src=(["\'])
            (?P<url>https?://app\.cetv\.cn/video/player/index\?[^"'<>]+)
        \1
    ''']
    _TESTS = [{
        'url': 'https://app.cetv.cn/video/player/index?vid=312889&thumb=http%3A%2F%2Fimg.cetv.cn%2Fa%2F10001%2F202606%2F407d600a9d0b62ca67b8dc5039e6061c.jpg&sid=10001&next=&autoStart=1&type=&customid=10418',
        'info_dict': {
            'id': '312889',
            'ext': 'mp4',
            'title': '《教育新闻直播间》12:05全集20260602',
            'thumbnail': r're:^https?://.+\.jpg(?:\?.+)?$',
            'duration': 598,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.centv.cn/p/591374.html',
        'info_dict': {
            'id': '312889',
            'ext': 'mp4',
            'title': '《教育新闻直播间》12:05全集20260602',
            'thumbnail': r're:^https?://.+\.jpg(?:\?.+)?$',
            'duration': 598,
        },
        'add_ie': ['Generic'],
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        query = parse_qs(url)
        video_id = traverse_obj(query, ('vid', 0, {str}))
        if not video_id:
            raise ExtractorError('This CETV player URL does not contain a video id', expected=True)

        site_id = traverse_obj(query, ('sid', 0, {str})) or '10001'
        video_type = traverse_obj(query, ('type', 0, {str})) or 'video'
        thumbnail = url_or_none(traverse_obj(query, ('thumb', 0, {str})))

        data = self._download_json(
            'https://app.cetv.cn/video/player/video', video_id,
            query={
                'sid': site_id,
                'vid': video_id,
                'type': video_type,
            },
            headers={'Referer': url})

        if traverse_obj(data, ('status', {int})) not in (None, 0):
            raise ExtractorError('CETV player returned an error', expected=True)

        file_info = traverse_obj(data, ('file', {dict})) or {}
        quality = qualities(('sd', 'hd', 'ed'))
        formats, subtitles = [], {}
        seen_urls = set()

        for format_id in ('sd', 'hd', 'ed', 'url'):
            format_url = url_or_none(file_info.get(format_id))
            if not format_url or format_url in seen_urls:
                continue
            seen_urls.add(format_url)

            if determine_ext(format_url) == 'm3u8' or re.search(r'(?i)\.m3u8(?:$|[?#])', format_url):
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    format_url, video_id, 'mp4',
                    m3u8_id='hls' if format_id == 'url' else format_id, fatal=False)
                for fmt in fmts:
                    if format_id in ('sd', 'hd', 'ed'):
                        fmt.setdefault('quality', quality(format_id))
                self._merge_subtitles(subs, target=subtitles)
                formats.extend(fmts)
                continue

            formats.append({
                'url': format_url,
                'format_id': format_id,
                'quality': quality(format_id) if format_id in ('sd', 'hd', 'ed') else None,
            })

        if not formats:
            raise ExtractorError('No playable formats found in CETV player response', expected=True)

        thumbnail = thumbnail or urljoin(url, data.get('image'))

        return {
            'id': video_id,
            'title': data.get('title') or data.get('tags') or video_id,
            'thumbnail': thumbnail,
            'duration': int_or_none(data.get('time')),
            'formats': formats,
            'subtitles': subtitles,
        }
