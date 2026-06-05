import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    qualities,
    try_get,
    unified_timestamp,
    url_or_none,
)


class CCTVIE(InfoExtractor):
    IE_DESC = '央视网'
    _VALID_URL = r'https?://(?:(?:[^/]+)\.(?:cntv|cctv)\.(?:com|cn)|(?:www\.)?ncpa-classic\.com)/(?:[^/]+/)*?(?P<id>[^/?#&]+?)(?:/index)?(?:\.s?html|[?#&]|$)'
    _TESTS = [{
        # fo.addVariable("videoCenterId","id")
        'url': 'http://sports.cntv.cn/2016/02/12/ARTIaBRxv4rTT1yWf1frW2wi160212.shtml',
        'md5': 'd61ec00a493e09da810bf406a078f691',
        'info_dict': {
            'id': '5ecdbeab623f4973b40ff25f18b174e8',
            'ext': 'mp4',
            'title': '[NBA]二少联手砍下46分 雷霆主场击败鹈鹕（快讯）',
            'description': 'md5:7e14a5328dc5eb3d1cd6afbbe0574e95',
            'duration': 98,
            'uploader': 'songjunjie',
            'timestamp': 1455279956,
            'upload_date': '20160212',
        },
    }, {
        # var guid = "id"
        'url': 'http://tv.cctv.com/2016/02/05/VIDEUS7apq3lKrHG9Dncm03B160205.shtml',
        'info_dict': {
            'id': 'efc5d49e5b3b4ab2b34f3a502b73d3ae',
            'ext': 'mp4',
            'title': '[赛车]“车王”舒马赫恢复情况成谜（快讯）',
            'description': '2月4日，蒙特泽莫罗透露了关于“车王”舒马赫恢复情况，但情况是否属实遭到了质疑。',
            'duration': 37,
            'uploader': 'shujun',
            'timestamp': 1454677291,
            'upload_date': '20160205',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # changePlayer('id')
        'url': 'http://english.cntv.cn/special/four_comprehensives/index.shtml',
        'info_dict': {
            'id': '4bb9bb4db7a6471ba85fdeda5af0381e',
            'ext': 'mp4',
            'title': 'NHnews008 ANNUAL POLITICAL SEASON',
            'description': 'Four Comprehensives',
            'duration': 60,
            'uploader': 'zhangyunlei',
            'timestamp': 1425385521,
            'upload_date': '20150303',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # loadvideo('id')
        'url': 'http://cctv.cntv.cn/lm/tvseries_russian/yilugesanghua/index.shtml',
        'info_dict': {
            'id': 'b15f009ff45c43968b9af583fc2e04b2',
            'ext': 'mp4',
            'title': 'Путь，усыпанный космеями Серия 1',
            'description': 'Путь, усыпанный космеями',
            'duration': 2645,
            'uploader': 'renxue',
            'timestamp': 1477479241,
            'upload_date': '20161026',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # var initMyAray = 'id'
        'url': 'http://www.ncpa-classic.com/2013/05/22/VIDE1369219508996867.shtml',
        'info_dict': {
            'id': 'a194cfa7f18c426b823d876668325946',
            'ext': 'mp4',
            'title': '小泽征尔音乐塾 音乐梦想无国界',
            'duration': 2173,
            'timestamp': 1369248264,
            'upload_date': '20130522',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # videoCenterId: "id"
        'url': 'http://news.cctv.com/2024/02/21/ARTIcU5tKIOIF2myEGCATkLo240221.shtml',
        'info_dict': {
            'id': '5c846c0518444308ba32c4159df3b3e0',
            'ext': 'mp4',
            'title': '《平“语”近人——习近平喜欢的典故》第三季 第5集：风物长宜放眼量',
            'uploader': 'yangjuan',
            'timestamp': 1708554940,
            'upload_date': '20240221',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # var ids = ["id"]
        'url': 'http://www.ncpa-classic.com/clt/more/416/index.shtml',
        'info_dict': {
            'id': 'a8606119a4884588a79d81c02abecc16',
            'ext': 'mp3',
            'title': '来自维也纳的新年贺礼',
            'description': 'md5:f13764ae8dd484e84dd4b39d5bcba2a7',
            'duration': 1578,
            'uploader': 'djy',
            'timestamp': 1482942419,
            'upload_date': '20161228',
        },
        'params': {
            'skip_download': True,
        },
        'expected_warnings': ['Failed to download m3u8 information'],
    }, {
        'url': 'http://ent.cntv.cn/2016/01/18/ARTIjprSSJH8DryTVr5Bx8Wb160118.shtml',
        'only_matching': True,
    }, {
        'url': 'http://tv.cntv.cn/video/C39296/e0210d949f113ddfb38d31f00a4e5c44',
        'only_matching': True,
    }, {
        'url': 'http://english.cntv.cn/2016/09/03/VIDEhnkB5y9AgHyIEVphCEz1160903.shtml',
        'only_matching': True,
    }, {
        'url': 'http://tv.cctv.com/2016/09/07/VIDE5C1FnlX5bUywlrjhxXOV160907.shtml',
        'only_matching': True,
    }, {
        'url': 'http://tv.cntv.cn/video/C39296/95cfac44cabd3ddc4a9438780a4e5c44',
        'only_matching': True,
    }]

    _CHAPTER_KEYS = ('lowChapters', 'chapters', 'chapters2', 'chapters3', 'chapters4')

    @staticmethod
    def _chapter_bitrate(fragment_url):
        bitrate = try_get(
            re.search(r'_h264(?P<tbr>\d+)', fragment_url or ''), lambda x: x.group('tbr'))
        return float_or_none(bitrate, scale=1000)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(
            [r'var\s+guid\s*=\s*["\']([\da-fA-F]+)',
             r'videoCenterId(?:["\']\s*,|:)\s*["\']([\da-fA-F]+)',
             r'changePlayer\s*\(\s*["\']([\da-fA-F]+)',
             r'load[Vv]ideo\s*\(\s*["\']([\da-fA-F]+)',
             r'var\s+initMyAray\s*=\s*["\']([\da-fA-F]+)',
             r'var\s+ids\s*=\s*\[["\']([\da-fA-F]+)'],
            webpage, 'video id')

        data = self._download_json(
            'http://vdn.apps.cntv.cn/api/getHttpVideoInfo.do', video_id,
            query={
                'pid': video_id,
                'url': url,
                'idl': 32,
                'idlr': 32,
                'modifyed': 'false',
            })

        title = data['title']

        formats = []

        chapter_qualities = qualities(self._CHAPTER_KEYS)

        video = data.get('video')
        chapter_streams = {}
        if isinstance(video, dict):
            for chapters_key in self._CHAPTER_KEYS:
                fragments = []
                for fragment in try_get(video, lambda x: x[chapters_key], list) or []:
                    fragment_url = url_or_none(fragment.get('url'))
                    if fragment_url:
                        fragments.append({
                            'url': fragment_url,
                            'duration': float_or_none(fragment.get('duration')),
                        })
                if fragments:
                    chapter_streams[chapters_key] = fragments
                    video_url = fragments[0]['url']
                    formats.append({
                        'url': video_url,
                        'format_id': f'http-{chapters_key}',
                        'quality': chapter_qualities(chapters_key),
                    })

        hls_urls = []
        manifest = data.get('manifest')
        if isinstance(manifest, dict):
            for hls_key in ('hls_enc_url', 'hls_h5e_url', 'hls_enc2_url'):
                hls_url = url_or_none(manifest.get(hls_key))
                if hls_url:
                    hls_urls.append(hls_url)
        hls_url = url_or_none(data.get('hls_url'))
        if hls_url:
            hls_urls.append(hls_url)

        chapter_format_info = {}
        hls_formats = []
        for hls_url in hls_urls:
            hls_url = re.sub(r'([?&])maxbr=\d+&?', r'\1', hls_url).rstrip('?&')
            hls_formats = self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', entry_protocol='m3u8_native',
                m3u8_id='hls', fatal=False)
            if hls_formats:
                break

        hls_variants = sorted({
            (fmt.get('tbr'), fmt.get('width'), fmt.get('height'))
            for fmt in hls_formats if fmt.get('tbr')
        })
        for chapters_key in sorted(chapter_streams, key=chapter_qualities):
            tbr = self._chapter_bitrate(chapter_streams[chapters_key][0]['url'])
            width = height = None
            if hls_variants:
                _, width, height = min(hls_variants, key=lambda x: abs((x[0] or 0) - (tbr or 0)))
            chapter_format_info[chapters_key] = {
                'tbr': tbr,
                'width': width,
                'height': height,
            }

        for fmt in formats:
            fmt.update(chapter_format_info.get(fmt['format_id'][len('http-'):], {}))

        if any(len(fragments) > 1 for fragments in chapter_streams.values()):
            for fmt in formats:
                chapters_key = fmt['format_id'][len('http-'):]
                fragments = chapter_streams.get(chapters_key)
                if not fragments:
                    continue
                fmt.update({
                    'ext': 'mp4',
                    'protocol': 'http_mp4_segments',
                    'fragments': fragments,
                })
            hls_formats = []

        if hls_formats:
            formats.extend(hls_formats)

        uploader = data.get('editer_name')
        description = self._html_search_meta(
            'description', webpage, default=None)
        timestamp = unified_timestamp(data.get('f_pgmtime'))
        duration = float_or_none(try_get(video, lambda x: x['totalLength']))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }
