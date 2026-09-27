"""YouTube Video, Audio & Subtitles Download Engine
Adapted from YTSage (ytsage_downloader.py & ytsage_gui_format_table.py)
Provides multi-resolution video merging (MP4/WebM/MKV), audio extraction (MP3/M4A/WAV/FLAC),
subtitle exports (SRT/VTT), and metadata embedding.
"""
import os
import re
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yt_dlp

from app.engine.youtube_transcript import extract_video_id, format_seconds_to_timestamp

logger = logging.getLogger(__name__)

STANDARD_RESOLUTIONS = ["2160", "1440", "1080", "720", "480", "360"]
RESOLUTION_LABELS = {
    "2160": "4K Ultra HD (2160p)",
    "1440": "2K Quad HD (1440p)",
    "1080": "Full HD (1080p)",
    "720": "HD (720p)",
    "480": "Standard (480p)",
    "360": "Low (360p)",
}


def sanitize_filename(name: str) -> str:
    """Sanitizes filename for cross-platform filesystem and HTTP headers."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:120] or "youtube_media"


class YouTubeDownloadEngine:
    """Engine for extracting download formats and executing media downloads using yt-dlp."""

    @staticmethod
    def get_available_formats(url_or_id: str) -> Dict[str, Any]:
        """Extracts all downloadable video, audio, and subtitle options for a YouTube video."""
        video_id = extract_video_id(url_or_id)
        if not video_id:
            return {"success": False, "error": f"Invalid YouTube URL or ID: {url_or_id}"}

        video_url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)

            title = info.get("title", f"YouTube Video {video_id}")
            channel = info.get("uploader") or info.get("channel", "YouTube Creator")
            duration = int(info.get("duration") or 0)
            thumbnail = info.get("thumbnail") or f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            raw_formats = info.get("formats", [])
            raw_subtitles = info.get("subtitles", {})
            raw_auto_subs = info.get("automatic_captions", {})

            # 1. Filter and group video formats by resolution
            video_options = []
            seen_resolutions = set()

            # Separate video-only and progressive formats
            valid_videos = [
                f for f in raw_formats
                if f.get("vcodec") != "none" and (f.get("height") or f.get("resolution"))
            ]
            valid_videos.sort(key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)

            for f in valid_videos:
                height = f.get("height")
                if not height:
                    res_str = str(f.get("resolution", "0x0"))
                    try:
                        height = int(res_str.split("x")[-1])
                    except Exception:
                        continue

                height_str = str(height)
                if height_str in seen_resolutions:
                    continue
                seen_resolutions.add(height_str)

                # Approximate filesize
                filesize = f.get("filesize") or f.get("filesize_approx")
                formatted_size = f"{filesize / (1024 * 1024):.1f} MB" if filesize else "Unknown size"

                label = RESOLUTION_LABELS.get(height_str, f"{height_str}p Video")
                fps = f.get("fps") or 30

                video_options.append({
                    "resolution": height_str,
                    "label": label,
                    "height": height,
                    "format_id": f.get("format_id"),
                    "ext": "mp4",
                    "fps": fps,
                    "has_audio": bool(f.get("acodec") and f.get("acodec") != "none"),
                    "vcodec": f.get("vcodec", "h264"),
                    "filesize_bytes": filesize,
                    "filesize_label": formatted_size,
                })

            # Sort video options high to low
            video_options.sort(key=lambda x: x["height"], reverse=True)

            # 2. Pre-configured Audio Presets (YTSage standard)
            audio_presets = [
                {
                    "format": "mp3",
                    "bitrate": "320",
                    "label": "MP3 High Quality (320 kbps)",
                    "extension": "mp3",
                    "codec": "libmp3lame",
                    "description": "Standard high quality MP3 for music and podcasts"
                },
                {
                    "format": "mp3",
                    "bitrate": "192",
                    "label": "MP3 Balanced (192 kbps)",
                    "extension": "mp3",
                    "codec": "libmp3lame",
                    "description": "Balanced filesize and fidelity"
                },
                {
                    "format": "m4a",
                    "bitrate": "best",
                    "label": "M4A Original Audio Stream",
                    "extension": "m4a",
                    "codec": "aac",
                    "description": "Direct YouTube AAC audio stream (fastest download, zero transcoding)"
                },
                {
                    "format": "wav",
                    "bitrate": "lossless",
                    "label": "WAV Lossless Audio",
                    "extension": "wav",
                    "codec": "pcm_s16le",
                    "description": "Uncompressed audio for sound editing & production"
                },
                {
                    "format": "flac",
                    "bitrate": "lossless",
                    "label": "FLAC High-Res Audio",
                    "extension": "flac",
                    "codec": "flac",
                    "description": "Lossless compressed master audio"
                },
            ]

            # 3. Available Subtitles
            subtitles_list = []
            for lang, tracks in raw_subtitles.items():
                name = tracks[0].get("name", lang) if tracks else lang
                subtitles_list.append({
                    "language_code": lang,
                    "language_name": f"{name} (Manual)",
                    "is_auto": False,
                })

            for lang, tracks in raw_auto_subs.items():
                if any(s["language_code"] == lang for s in subtitles_list):
                    continue
                name = tracks[0].get("name", lang) if tracks else lang
                subtitles_list.append({
                    "language_code": lang,
                    "language_name": f"{name} (Auto-generated)",
                    "is_auto": True,
                })

            return {
                "success": True,
                "video_id": video_id,
                "video_url": video_url,
                "title": title,
                "channel": channel,
                "duration": duration,
                "duration_formatted": format_seconds_to_timestamp(duration),
                "thumbnail": thumbnail,
                "video_options": video_options,
                "audio_presets": audio_presets,
                "subtitles": subtitles_list[:25],
            }

        except Exception as e:
            logger.error(f"Error extracting formats for {video_id}: {e}")
            return {
                "success": False,
                "video_id": video_id,
                "video_url": video_url,
                "error": str(e),
            }

    @staticmethod
    def execute_media_download(
        url_or_id: str,
        media_type: str = "video",
        quality: str = "720",
        audio_format: str = "mp3",
        audio_bitrate: str = "192",
        format_id: Optional[str] = None,
        subtitle_lang: str = "en",
        subtitle_format: str = "srt",
        audio_normalization: bool = False,
        embed_metadata: bool = True,
        embed_thumbnail: bool = False,
    ) -> Tuple[str, str, str]:
        """Downloads requested media to a temporary file and returns (temp_file_path, filename, mime_type).

        Caller is responsible for removing temp_file_path after streaming.
        """
        video_id = extract_video_id(url_or_id)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL or ID: {url_or_id}")

        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Fetch title for human-readable filename
        info = YouTubeDownloadEngine.get_available_formats(video_id)
        raw_title = info.get("title", f"youtube_{video_id}")
        base_name = sanitize_filename(raw_title)

        temp_dir = tempfile.mkdtemp(prefix="pulseradar_dl_")

        ydl_opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "force_overwrites": True,
        }

        if media_type == "video":
            # Video Download (with best audio merge)
            target_ext = "mp4"
            out_template = os.path.join(temp_dir, f"{base_name}_{quality}p.%(ext)s")
            ydl_opts["outtmpl"] = out_template

            if format_id:
                # Merge specified format_id with best audio
                ydl_opts["format"] = f"{format_id}+bestaudio/best"
            elif quality and quality != "best":
                try:
                    q_int = int(quality)
                    ydl_opts["format"] = f"bestvideo[height<={q_int}]+bestaudio/best[height<={q_int}]/best"
                except Exception:
                    ydl_opts["format"] = "bestvideo+bestaudio/best"
            else:
                ydl_opts["format"] = "bestvideo+bestaudio/best"

            ydl_opts["merge_output_format"] = target_ext
            if embed_metadata:
                ydl_opts["add_metadata"] = True

            mime_type = "video/mp4"

        elif media_type == "audio":
            # Audio Extraction
            target_ext = audio_format.lower()
            out_template = os.path.join(temp_dir, f"{base_name}.%(ext)s")
            ydl_opts["outtmpl"] = out_template

            if target_ext == "m4a":
                # Direct stream copy without re-encoding (ultra-fast ~2s)
                ydl_opts["format"] = "ba[ext=m4a]/ba"
                mime_type = "audio/mp4"
            else:
                # Transcode to mp3 / wav / flac
                ydl_opts["format"] = "ba/b"
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": target_ext,
                    "preferredquality": audio_bitrate if audio_bitrate != "best" else "192",
                }]
                if audio_normalization:
                    ydl_opts["postprocessor_args"] = ["-af", "loudnorm=I=-16:LRA=11:TP=-1.5"]
                mime_type = "audio/mpeg" if target_ext == "mp3" else f"audio/{target_ext}"

        elif media_type == "subtitle":
            # Subtitle Extraction
            target_ext = subtitle_format.lower()
            out_template = os.path.join(temp_dir, f"{base_name}.%(ext)s")
            ydl_opts.update({
                "outtmpl": out_template,
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": [subtitle_lang],
                "postprocessors": [{
                    "key": "FFmpegSubtitlesConvertor",
                    "format": target_ext,
                }],
            })
            mime_type = "text/plain"
        else:
            raise ValueError(f"Unsupported media_type: {media_type}")

        # Execute yt-dlp download
        logger.info(f"Executing yt-dlp download for {video_id} (Type: {media_type}, Target: {out_template})")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Locate downloaded file in temp_dir
        downloaded_files = [
            os.path.join(temp_dir, f) for f in os.listdir(temp_dir)
            if not f.endswith(".part") and os.path.isfile(os.path.join(temp_dir, f))
        ]

        if not downloaded_files:
            raise RuntimeError(f"Download failed: no output file generated in {temp_dir}")

        # Pick the largest or matching file
        downloaded_files.sort(key=lambda p: os.path.getsize(p), reverse=True)
        final_file = downloaded_files[0]
        final_filename = os.path.basename(final_file)

        logger.info(f"Download complete: {final_file} ({os.path.getsize(final_file)} bytes)")
        return final_file, final_filename, mime_type
