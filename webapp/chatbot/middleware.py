"""
Custom middleware for handling YouTube embeds and CORS - COMPLETE FIXED
File: chatbot/middleware.py
"""

class YouTubeEmbedMiddleware:
    """
    Middleware to add headers that allow YouTube embeds
    MUST be the LAST middleware in settings.MIDDLEWARE
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # CRITICAL: Remove ALL restrictive headers
        restrictive_headers = [
            'X-Frame-Options',
            'Content-Security-Policy',
            'Content-Security-Policy-Report-Only',
            'X-Content-Type-Options'
        ]
        
        for header in restrictive_headers:
            if header in response:
                del response[header]
        
        # Build comprehensive CSP for YouTube embeds
        csp_directives = {
            'default-src': "'self'",
            
            # Scripts: Allow inline, eval, and external scripts
            'script-src': " ".join([
                "'self'",
                "'unsafe-inline'",
                "'unsafe-eval'",
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com",
                "https://www.youtube.com",
                "https://www.youtube-nocookie.com",
                "https://s.ytimg.com",
                "https://*.ytimg.com",
                "https://www.gstatic.com",
            ]),
            
            # Styles
            'style-src': " ".join([
                "'self'",
                "'unsafe-inline'",
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com",
                "https://fonts.googleapis.com",
            ]),
            
            # Fonts
            'font-src': " ".join([
                "'self'",
                "https://cdnjs.cloudflare.com",
                "https://fonts.gstatic.com",
                "data:",
            ]),
            
            # Images: Allow all sources for YouTube thumbnails
            'img-src': " ".join([
                "'self'",
                "data:",
                "https:",
                "http:",
                "blob:",
                "https://*.ytimg.com",
                "https://i.ytimg.com",
                "https://www.youtube.com",
                "https://www.youtube-nocookie.com",
            ]),
            
            # CRITICAL: Frame sources - Allow YouTube embeds
            'frame-src': " ".join([
                "'self'",
                "https://www.youtube.com",
                "https://www.youtube-nocookie.com",
                "https://*.youtube.com",
                "https://*.youtube-nocookie.com",
            ]),
            
            # Connect sources: API calls and video streaming
            'connect-src': " ".join([
                "'self'",
                "https://www.youtube.com",
                "https://www.youtube-nocookie.com",
                "https://*.googlevideo.com",
                "https://i.ytimg.com",
                "https://*.ytimg.com",
                "https://www.gstatic.com",
                "https://cdn.jsdelivr.net",  # Allow Bootstrap CDN
                "ws:",
                "wss:",
                "http://localhost:*",
            ]),
            
            # Media sources: Video playback
            'media-src': " ".join([
                "'self'",
                "https://www.youtube.com",
                "https://www.youtube-nocookie.com",
                "https://*.googlevideo.com",
                "blob:",
                "data:",
            ]),
            
            # Child/Worker sources
            'child-src': " ".join([
                "'self'",
                "https://www.youtube.com",
                "https://www.youtube-nocookie.com",
                "blob:",
            ]),
            
            # Worker sources
            'worker-src': " ".join([
                "'self'",
                "blob:",
            ]),
            
            # Object sources (block plugins)
            'object-src': "'none'",
            
            # Base URI
            'base-uri': "'self'",
            
            # Form actions
            'form-action': "'self'",
            
            # Frame ancestors (allow embedding)
            'frame-ancestors': "'self'",
        }
        
        # Build CSP string
        csp = "; ".join([f"{key} {value}" for key, value in csp_directives.items()])
        response['Content-Security-Policy'] = csp
        
        # CORS headers for development
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response['Access-Control-Allow-Credentials'] = 'true'
        
        # Additional security headers (non-restrictive)
        response['X-Content-Type-Options'] = 'nosniff'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response