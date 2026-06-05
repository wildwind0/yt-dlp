import time

from .dash import DashSegmentsFD
from ..postprocessor.ffmpeg import FFmpegConcatPP


class Mp4SegmentsFD(DashSegmentsFD):
    FD_NAME = 'mp4segments'

    def _append_fragment(self, ctx, frag_content):
        if not frag_content:
            return
        ctx.setdefault('fragment_files', []).append(ctx['fragment_filename_sanitized'])
        if self._FragmentFD__do_ytdl_file(ctx):
            self._write_ytdl_file(ctx)
        del ctx['fragment_filename_sanitized']

    def _finish_frag_download(self, ctx, info_dict):
        elapsed = time.time() - ctx.get('started', time.time())
        ctx['dest_stream'].close()
        self.try_remove(ctx['tmpfilename'])
        if self._FragmentFD__do_ytdl_file(ctx):
            self.try_remove(self.ytdl_filename(ctx['filename']))

        fragment_files = ctx.get('fragment_files') or []
        if not fragment_files:
            self.report_error('The downloaded file is empty')
            return False

        concat_pp = FFmpegConcatPP(self.ydl)
        if not concat_pp.available:
            self.report_error('ffmpeg is required to concatenate CCTV MP4 segments')
            return False

        files_to_delete = concat_pp.concat_files(fragment_files, ctx['filename'])
        if files_to_delete and not self.params.get('keep_fragments', False):
            self.ydl._delete_downloaded_files(*files_to_delete)

        downloaded_bytes = self.filesize_or_none(ctx['filename'])
        if not downloaded_bytes:
            self.report_error('The downloaded file is empty')
            return False

        self._hook_progress({
            'downloaded_bytes': downloaded_bytes,
            'total_bytes': downloaded_bytes,
            'filename': ctx['filename'],
            'status': 'finished',
            'elapsed': elapsed,
            'ctx_id': ctx.get('ctx_id'),
            'max_progress': ctx.get('max_progress'),
            'progress_idx': ctx.get('progress_idx'),
        }, info_dict)
        return True
