"""
Custom middleware for handling YouTube embeds and CORS
File: chatbot/middleware.py
"""

class YouTubeEmbedMiddleware:
    """
    Middleware to add headers that allow YouTube embeds
    This must be the last middleware in the MIDDLEWARE list
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Remove X-Frame-Options to allow iframes
        if 'X-Frame-Options' in response:
            del response['X-Frame-Options']
        
        # Add permissive Content Security Policy for YouTube
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://meet.jit.si "
            "https://www.youtube.com https://s.ytimg.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "img-src 'self' data: https: http: blob:; "
            "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com "
            "https://meet.jit.si https://*.jitsi.net; "
            "connect-src 'self' https://www.youtube.com https://meet.jit.si ws: wss: http://localhost:*; "
            "media-src 'self' https://www.youtube.com blob:; "
            "child-src 'self' https://www.youtube.com https://www.youtube-nocookie.com;"
        )
        response['Content-Security-Policy'] = csp
        
        # Allow all origins for development
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response