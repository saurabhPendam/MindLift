"""
Custom template filters for YouTube URLs
File: chatbot/templatetags/youtube_filters.py
"""
import re
from django import template

register = template.Library()


@register.filter
def youtube_id(url):
    """
    Extract YouTube video ID from URL
    Usage: {{ video_url|youtube_id }}
    """
    if not url:
        return ''
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'youtube-nocookie\.com\/embed\/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return ''


@register.filter
def youtube_embed_url(url):
    """
    Convert any YouTube URL to embed format using youtube-nocookie.com
    Usage: {{ video_url|youtube_embed_url }}
    """
    video_id = youtube_id(url)
    if video_id:
        return f'https://www.youtube-nocookie.com/embed/{video_id}'
    return url


@register.filter
def is_youtube_url(url):
    """
    Check if URL is a YouTube URL
    Usage: {% if video_url|is_youtube_url %}...{% endif %}
    """
    if not url:
        return False
    
    youtube_domains = ['youtube.com', 'youtu.be', 'youtube-nocookie.com']
    return any(domain in url for domain in youtube_domains) 