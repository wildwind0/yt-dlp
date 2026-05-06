import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    float_or_none,
    int_or_none,
    str_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class XueqiuIE(InfoExtractor):
    IE_DESC = '雪球'
    _VALID_URL = r'https?://(?:www\.)?xueqiu\.com/vod/(?P<id>\d+)(?:/(?P<status_id>\d+))?'
    _VOD_APP_ID = '1500005172'
    _TESTS = [{
        'url': 'https://xueqiu.com/vod/5145403724059960017/385121598',
        'info_dict': {
            'id': '5145403724059960017',
            'display_id': '385121598',
            'ext': 'mp4',
            'title': '视频 | 快速看懂珀莱雅2025年财报',
            'description': 'md5:2ad1d25d07e01f238aae3b31962e990c',
            'uploader': '珀莱雅',
            'uploader_id': '6973638177',
            'uploader_url': 'https://xueqiu.com/6973638177',
            'duration': 319.36,
            'timestamp': 1776836085,
            'upload_date': '20260422',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _extract_formats(self, video_data, referer):
        formats = []
        for video in traverse_obj(video_data, ('videoInfo', ('sourceVideo', ('transcodeList', ...)), {dict})):
            video_url = url_or_none(video.get('url'))
            if not video_url:
                continue
            formats.append({
                **traverse_obj(video, {
                    'url': 'url',
                    'format_id': ('definition', {lambda x: f'http-{x or "0"}'}),
                    'format_note': ('templateName', {str}),
                    'width': ('width', {int_or_none}),
                    'height': ('height', {int_or_none}),
                    'filesize': (('totalSize', 'size'), {int_or_none}),
                    'tbr': ('bitrate', {float_or_none(scale=1000)}),
                    'vcodec': ('videoStreamList', 0, 'codec'),
                    'acodec': ('audioStreamList', 0, 'codec'),
                    'fps': ('videoStreamList', 0, 'fps', {float_or_none}),
                }, get_all=False),
                'http_headers': {'Referer': referer},
            })
        return formats

    def _real_extract(self, url):
        file_id, status_id = self._match_valid_url(url).group('id', 'status_id')
        webpage = self._download_webpage(
            url, file_id, fatal=False, headers={
                'Referer': 'https://xueqiu.com/',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            })

        status_data = self._search_json(
            r'window\.SNOWMAN_STATUS\s*=', webpage, 'status data', file_id,
            default={}) if webpage else {}

        video_data = self._download_json(
            f'https://playvideo.qcloud.com/getplayinfo/v2/{self._VOD_APP_ID}/{file_id}',
            file_id, headers={'Referer': url})
        if video_data.get('code'):
            raise ExtractorError(
                f'腾讯云返回错误: {video_data.get("message") or video_data["code"]}')

        title = self._search_regex(
            r'<h1[^>]+class=["\']article__bd__title["\'][^>]*>([^<]+)',
            webpage, 'title', default=None) if webpage else None
        if title:
            title = re.sub(r'\s+', ' ', title).strip()

        return {
            'id': file_id,
            'display_id': status_id,
            'formats': self._extract_formats(video_data, url),
            **traverse_obj(video_data, {
                'title': ('videoInfo', 'basicInfo', 'name', {str}),
                'description': ('videoInfo', 'basicInfo', 'description', {str}),
                'duration': ('videoInfo', 'sourceVideo', ('floatDuration', 'duration'), {float_or_none}),
            }, get_all=False),
            **traverse_obj(status_data, {
                'title': ('title', {str}),
                'description': ('description', {clean_html}),
                'timestamp': ('created_at', {int_or_none(scale=1000)}),
                'uploader': ('user', 'screen_name', {str}),
                'uploader_id': ('user', ('id', 'user_id'), {str_or_none}, any),
                'uploader_url': ('user', 'profile', {urljoin('https://xueqiu.com')}),
            }, get_all=False),
            'title': title or traverse_obj(status_data, ('title', {str}), get_all=False)
            or traverse_obj(video_data, ('videoInfo', 'basicInfo', 'name', {str}), get_all=False),
        }
