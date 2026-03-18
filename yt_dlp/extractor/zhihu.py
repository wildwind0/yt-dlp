from .common import InfoExtractor
from ..utils import float_or_none, format_field, int_or_none, strip_or_none, url_or_none
from ..utils.traversal import traverse_obj


class ZhihuBaseIE(InfoExtractor):
    def _extract_video_formats(self, video):
        formats = []
        for format_id, q in (video.get('playlist') or {}).items():
            play_url = url_or_none(q.get('url') or q.get('play_url'))
            if not play_url:
                continue
            formats.append({
                'asr': int_or_none(q.get('sample_rate')),
                'audio_channels': int_or_none(q.get('channels')),
                'filesize': int_or_none(q.get('size')),
                'format_id': format_id,
                'fps': int_or_none(q.get('fps')),
                'height': int_or_none(q.get('height')),
                'tbr': float_or_none(q.get('bitrate')),
                'url': play_url,
                'width': int_or_none(q.get('width')),
            })
        return formats

    def _extract_author_info(self, author):
        url_token = author.get('url_token')
        return {
            'uploader': author.get('name'),
            'uploader_id': author.get('id'),
            'uploader_url': format_field(url_token, None, 'https://www.zhihu.com/people/%s'),
        }


class ZhihuIE(ZhihuBaseIE):
    _VALID_URL = r'https?://(?:www\.)?zhihu\.com/zvideo/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.zhihu.com/zvideo/1342930761977176064',
        'md5': 'c8d4c9cd72dd58e6f9bc9c2c84266464',
        'info_dict': {
            'id': '1342930761977176064',
            'ext': 'mp4',
            'title': '写春联也太难了吧！',
            'thumbnail': r're:^https?://.*\.jpg',
            'uploader': '桥半舫',
            'timestamp': 1612959715,
            'upload_date': '20210210',
            'uploader_id': '244ecb13b0fd7daf92235288c8ca3365',
            'duration': 146.333,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        zvideo = self._download_json(
            'https://www.zhihu.com/api/v4/zvideos/' + video_id, video_id)
        title = zvideo['title']
        video = zvideo.get('video') or {}

        author = zvideo.get('author') or {}

        return {
            'id': video_id,
            'title': title,
            'formats': self._extract_video_formats(video),
            'thumbnail': video.get('thumbnail') or zvideo.get('image_url'),
            'timestamp': int_or_none(zvideo.get('published_at')),
            'duration': float_or_none(video.get('duration')),
            'view_count': int_or_none(zvideo.get('play_count')),
            'like_count': int_or_none(zvideo.get('liked_count')),
            'comment_count': int_or_none(zvideo.get('comment_count')),
            **self._extract_author_info(author),
        }


class ZhihuPinIE(ZhihuBaseIE):
    _VALID_URL = r'https?://(?:www\.)?zhihu\.com/pin/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.zhihu.com/pin/1997931711028299234?native=1&page=video_pin&scene=share&share_code=uCNbzG9TnfYJ&utm_psn=2016935021219435993',
        'info_dict': {
            'id': '1997931711028299234',
            'ext': 'mp4',
            'title': '环氧树脂能封存物质的形态，却封存不住时间的流逝。 它把世界变成了一件巨大的标本，供我们安全地观赏。',
            'description': '环氧树脂能封存物质的形态，却封存不住时间的流逝。 它把世界变成了一件巨大的标本，供我们安全地观赏。',
            'thumbnail': r're:^https?://.*\.(?:jpe?g|png)(?:\?.+)?$',
            'uploader': 'Chloe克洛一',
            'timestamp': 1769124055,
            'upload_date': '20260122',
            'uploader_id': '37a26ccb900addf99aa7fc96458b0e64',
            'uploader_url': 'https://www.zhihu.com/people/chloe-37-70-3',
            'duration': 141,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        pin_id = self._match_id(url)
        pin = self._download_json(
            'https://www.zhihu.com/api/v4/pins/' + pin_id, pin_id)

        video = traverse_obj(pin, ('content', lambda _, v: v.get('type') == 'video', any), expected_type=dict) or {}
        if not video:
            self.raise_no_formats('No video found in pin', expected=True)
        video_info = video.get('video_info') or video
        description = traverse_obj(
            pin, ('content', lambda _, v: v.get('type') == 'text', ('content', 'own_text'), any),
            expected_type=strip_or_none)
        title = strip_or_none(pin.get('excerpt_title')) or description or pin_id
        author = pin.get('author') or {}

        return {
            'id': pin_id,
            'title': title,
            'description': description,
            'formats': self._extract_video_formats(video_info),
            'thumbnail': traverse_obj(video, ('thumbnail', {url_or_none}), ('video_info', 'thumbnail', {url_or_none}), any),
            'timestamp': int_or_none(pin.get('created')),
            'duration': float_or_none(video_info.get('duration')),
            'view_count': int_or_none(pin.get('page_view_count') or video_info.get('play_count')),
            'like_count': int_or_none(pin.get('like_count')),
            'comment_count': int_or_none(pin.get('comment_count')),
            **self._extract_author_info(author),
        }
