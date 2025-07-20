"""
OpenFing extractor for yt-dlp

This extractor handles OpenFing course lesson pages which can contain:
1. Direct MP4 video links
2. YouTube embedded videos
"""

import re
from urllib.parse import urljoin, urlparse

from shared.logging.logger import get_logger
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.extractor.youtube import YoutubeIE
from yt_dlp.utils import ExtractorError

logger = get_logger(__name__)


class OpenFingIE(InfoExtractor):
    """
    Custom extractor for OpenFing lesson pages.

    Supports:
    - Direct MP4 video links
    - YouTube embedded videos
    - Domain redirects (open.fing.edu.uy → openfing.pages.fing.edu.uy)
    - Multiple HTML structures and formats
    """

    IE_NAME = "openfing"
    IE_DESC = "OpenFing course lessons"

    _VALID_URL = r"https?://(?:open\.fing\.edu\.uy|openfing\.pages\.fing\.edu\.uy)/courses/(?P<course>[^/]+)/(?P<lesson>\d+)/?"

    _TESTS = [
        {
            "url": "https://open.fing.edu.uy/courses/cdivv-2022/19/",
            "info_dict": {
                "id": "cdivv-2022_19",
                "title": "Unión e intersección de abiertos. Conjuntos cerrados",
                "course": "cdivv-2022",
                "lesson_number": 19,
                "ext": "mp4",
            },
            "note": "Direct MP4 video",
        },
        {
            "url": "https://open.fing.edu.uy/courses/cdivv-2022/20/",
            "info_dict": {
                "id": "cdivv-2022_20",
                "title": "Puntos de acumulación",
                "course": "cdivv-2022",
                "lesson_number": 20,
            },
            "note": "YouTube embedded video",
        },
        {
            "url": "https://openfing.pages.fing.edu.uy/courses/ac/23/",
            "info_dict": {
                "id": "ac_23",
                "course": "ac",
                "lesson_number": 23,
            },
            "note": "Direct access to pages subdomain",
        },
    ]

    def _real_extract(self, url):
        """Extract video information from OpenFing lesson page."""
        mobj = self._match_valid_url(url)
        course_code = mobj.group("course")
        lesson_number = int(mobj.group("lesson"))
        video_id = f"{course_code}_{lesson_number}"

        logger.debug(f"Extracting OpenFing lesson: {course_code} #{lesson_number}")

        try:
            webpage = self._download_webpage(url, video_id)
        except Exception as e:
            logger.error(f"Failed to download webpage {url}: {e}")
            raise ExtractorError(f"Could not download OpenFing lesson page: {url}")

        # Handle redirects first
        redirect_url = self._extract_redirect(webpage)
        if redirect_url:
            logger.debug(f"Following redirect: {url} → {redirect_url}")
            return self._extract_from_redirect(
                redirect_url,
                video_id,
                course_code,
                lesson_number,
            )

        metadata = self._extract_metadata(
            webpage,
            video_id,
            course_code,
            lesson_number,
            url,
        )

        # Try direct video first (faster)
        direct_video_url = self._extract_direct_video(webpage, url)
        if direct_video_url:
            logger.debug(f"Found direct video: {direct_video_url}")
            return self._build_direct_video_info(direct_video_url, metadata)

        # Try to find YouTube embed
        youtube_url = self._extract_youtube_embed(webpage)
        if youtube_url:
            logger.debug(f"Found YouTube embed: {youtube_url}")
            return self._build_youtube_info(youtube_url, metadata)

        logger.warning(f"No video content found in {url}")
        raise ExtractorError(
            f"No video content found in OpenFing lesson: {course_code} lesson {lesson_number}",
            expected=True,
        )

    def _extract_metadata(
        self,
        webpage,
        video_id,
        course_code,
        lesson_number,
        webpage_url,
    ):
        """Extract common metadata from webpage."""
        title = self._extract_title(webpage, video_id)

        return {
            "id": video_id,
            "title": title,
            "course": course_code,
            "lesson_number": lesson_number,
            "webpage_url": webpage_url,
            "extractor": "openfing",
        }

    def _extract_title(self, webpage, video_id):
        title_patterns = [
            # Most specific first
            r"<h2\s+class=[\"\']video__title[\"\'][^>]*>([^<]+)</h2>",
            r"<h2[^>]*class=[\"\'][^\"\']*video__title[^\"\']*[\"\'][^>]*>([^<]+)</h2>",
            r"<h1[^>]*class=[\"\'][^\"\']*title[^\"\']*[\"\'][^>]*>([^<]+)</h1>",
            # General patterns
            r"<title>([^<]+?)\s*-\s*OpenFing</title>",
            r"<title>([^<]+?)\s*-\s*[^<]*</title>",
            r"<title>([^<]+?)</title>",
            # Fallback to any heading
            r"<h[1-3][^>]*>([^<]+)</h[1-3]>",
        ]

        for pattern in title_patterns:
            title = self._search_regex(
                pattern,
                webpage,
                "title",
                default=None,
                flags=re.IGNORECASE,
            )
            if title:
                title = re.sub(r"\s+", " ", title.strip())
                if title and title != "OpenFing":
                    logger.debug(f"Extracted title: {title}")
                    return title

        logger.warning(f"Could not extract title, using fallback for {video_id}")
        return f"OpenFing Lesson {video_id}"

    def _extract_direct_video(self, webpage, base_url):
        """Extract direct video URL with better URL resolution."""
        video_patterns = [
            # Most specific patterns first
            r"<source[^>]+src=[\"\']([^\"\']+\.mp4)[\"\'][^>]*>",
            r"<video[^>]+src=[\"\']([^\"\']+\.mp4)[\"\'][^>]*>",
            # Unquoted attributes (common in some HTML)
            r"<source[^>]+src=([^\s>]+\.mp4)(?:\s|>)",
            r"<video[^>]+src=([^\s>]+\.mp4)(?:\s|>)",
            # OpenFing specific paths
            r"src=[\"\']([^\"\']*open\.fing\.edu\.uy/media/[^\"\']+\.mp4)[\"\']",
            r"src=[\"\']([^\"\']*openfing[^\"\']+\.mp4)[\"\']",
        ]

        for pattern in video_patterns:
            video_url = self._search_regex(
                pattern,
                webpage,
                "direct video URL",
                default=None,
            )
            if video_url:
                video_url = urljoin(base_url, video_url)
                if self._is_valid_video_url(video_url):
                    return video_url

        return None

    def _extract_youtube_embed(self, webpage):
        """Extract YouTube embed URL"""
        youtube_patterns = [
            # Standard iframe embeds
            r"<iframe[^>]+src=[\"\']https://www\.youtube\.com/embed/([a-zA-Z0-9_-]+)[^\"\']*[\"\']",
            r"<iframe[^>]+src=[\"\']https://www\.youtube-nocookie\.com/embed/([a-zA-Z0-9_-]+)[^\"\']*[\"\']",
            # Unquoted src
            r"src=https://www\.youtube\.com/embed/([a-zA-Z0-9_-]+)(?:\s|>|&)",
            # Links and other references
            r"href=[\"\']https://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)[^\"\']*[\"\']",
            r"data-youtube-id=[\"\']([a-zA-Z0-9_-]+)[\"\']",
        ]

        for pattern in youtube_patterns:
            video_id = self._search_regex(
                pattern,
                webpage,
                "youtube video id",
                default=None,
            )
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"

        return None

    def _extract_redirect(self, webpage):
        """Extract redirect URL"""
        redirect_patterns = [
            # OpenFing specific redirects
            r"<a href=[\"\']?(//openfing\.pages\.fing\.edu\.uy/[^\"\'>\s]+)[\"\']?[^>]*>Found</a>",
            r"href=[\"\']?(//openfing\.pages\.fing\.edu\.uy/[^\"\'>\s]+)[\"\']?",
            # General redirects
            r"<meta[^>]+http-equiv=[\"\']refresh[\"\'][^>]+url=([^\"\'>\s]+)",
            r"window\.location\.href\s*=\s*[\"\']([^\"\']+)[\"\']",
        ]

        for pattern in redirect_patterns:
            redirect_url = self._search_regex(
                pattern,
                webpage,
                "redirect URL",
                default=None,
            )
            if redirect_url:
                if redirect_url.startswith("//"):
                    redirect_url = "https:" + redirect_url
                elif redirect_url.startswith("/"):
                    redirect_url = "https://open.fing.edu.uy" + redirect_url
                return redirect_url

        return None

    def _build_direct_video_info(self, video_url, metadata):
        """Build info dict for direct video files."""
        info = metadata.copy()
        info.update(
            {
                "url": video_url,
                "ext": "mp4",
                "protocol": "https",
                "format_id": "direct",
                "format": f"MP4 - {metadata['title']}",
            },
        )
        return info

    def _build_youtube_info(self, youtube_url, metadata):
        """Build info dict for YouTube embedded videos."""
        youtube_info = self.url_result(
            youtube_url,
            ie=YoutubeIE.ie_key(),
            video_id=None,
            video_title=metadata["title"],
        )

        youtube_info.update(
            {
                "openfing_id": metadata["id"],
                "openfing_title": metadata["title"],
                "course": metadata["course"],
                "lesson_number": metadata["lesson_number"],
                "webpage_url": metadata["webpage_url"],
                "extractor": "openfing",
            },
        )

        return youtube_info

    def _extract_from_redirect(
        self,
        redirect_url,
        video_id,
        course_code,
        lesson_number,
    ):
        """Extract video info from redirected URL."""
        try:
            webpage = self._download_webpage(redirect_url, video_id)
            metadata = self._extract_metadata(
                webpage,
                video_id,
                course_code,
                lesson_number,
                redirect_url,
            )

            direct_video_url = self._extract_direct_video(webpage, redirect_url)
            if direct_video_url:
                return self._build_direct_video_info(direct_video_url, metadata)

            youtube_url = self._extract_youtube_embed(webpage)
            if youtube_url:
                return self._build_youtube_info(youtube_url, metadata)

            raise ExtractorError(
                f"No video content found in redirected page: {redirect_url}",
                expected=True,
            )

        except Exception as e:
            logger.error(f"Failed to extract from redirect {redirect_url}: {e}")
            raise ExtractorError(f"Failed to process redirected page: {redirect_url}")

    def _is_valid_video_url(self, url):
        """Basic validation for video URLs."""
        if not url:
            return False

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        if url.lower().endswith((".mp4", ".webm", ".mkv", ".avi")):
            return True

        video_domains = ["open.fing.edu.uy", "openfing.pages.fing.edu.uy"]
        if any(domain in parsed.netloc for domain in video_domains):
            return True

        return False


# Plugin entry point for yt-dlp
def get_extractor_class():
    return OpenFingIE
