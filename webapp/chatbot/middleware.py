"""
Custom middleware for handling YouTube embeds and CORS - FIXED FOR JITSI
File: chatbot/middleware.py
"""

class YouTubeEmbedMiddleware:
    """
    Middleware to add headers that allow YouTube embeds and Jitsi Meet
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
        ]
        
        for header in restrictive_headers:
            if header in response:
                del response[header]
        
        # Build comprehensive CSP for YouTube embeds AND Jitsi Meet
        csp_directives = {
            'default-src': "'self'",
            
            # Scripts: Allow inline, eval, and external scripts (REQUIRED FOR JITSI)
            'script-src': " ".join([
                "'self'",
                "'unsafe-inline'",
                "'unsafe-eval'",  # CRITICAL for Jitsi
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com",
                "https://www.youtube.com",
                "https://www.youtube-nocookie.com",
                "https://s.ytimg.com",
                "https://*.ytimg.com",
                "https://www.gstatic.com",
                "https://meet.jit.si",  # JITSI DOMAIN
                "https://*.jitsi.net",  # JITSI CDN
                "https://8x8.vc",       # JITSI ADDITIONAL
            ]),
            
            # Styles
            'style-src': " ".join([
                "'self'",
                "'unsafe-inline'",
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com",
                "https://fonts.googleapis.com",
                "https://meet.jit.si",
            ]),
            
            # Fonts
            'font-src': " ".join([
                "'self'",
                "https://cdnjs.cloudflare.com",
                "https://fonts.gstatic.com",
                "https://meet.jit.si",
                "data:",
            ]),
            
            # Images: Allow all sources
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
                "https://meet.jit.si",
                "https://*.jitsi.net",
            ]),
            
            # CRITICAL: Frame sources - Allow YouTube AND Jitsi
            'frame-src': " ".join([
                "'self'",
                "https://www.youtube.com",
                "https://www.youtube-nocookie.com",
                "https://*.youtube.com",
                "https://*.youtube-nocookie.com",
                "https://meet.jit.si",      # JITSI MAIN
                "https://*.meet.jit.si",    # JITSI SUBDOMAINS
                "https://8x8.vc",           # JITSI ALTERNATIVE
                "https://*.jitsi.net",      # JITSI CDN
            ]),
            
            # Connect sources: API calls and video streaming (CRITICAL FOR JITSI)
            'connect-src': " ".join([
                "'self'",
                "https://www.youtube.com",
                "https://www.youtube-nocookie.com",
                "https://*.googlevideo.com",
                "https://i.ytimg.com",
                "https://*.ytimg.com",
                "https://www.gstatic.com",
                "https://cdn.jsdelivr.net",
                "https://meet.jit.si",
                "https://*.meet.jit.si",
                "https://*.jitsi.net",
                "https://8x8.vc",
                "wss://meet.jit.si",        # WEBSOCKET FOR JITSI
                "wss://*.meet.jit.si",
                "wss://*.jitsi.net",
                "ws:",
                "wss:",
                "http://localhost:*",
                "https://localhost:*",
            ]),
            
            # Media sources: Video/Audio playback (REQUIRED FOR JITSI)
            'media-src': " ".join([
                "'self'",
                "https://www.youtube.com",
                "https://www.youtube-nocookie.com",
                "https://*.googlevideo.com",
                "https://meet.jit.si",
                "https://*.meet.jit.si",
                "https://*.jitsi.net",
                "blob:",
                "data:",
                "mediastream:",  # REQUIRED FOR WEBRTC
            ]),
            
            # Child/Worker sources
            'child-src': " ".join([
                "'self'",
                "https://www.youtube.com",
                "https://www.youtube-nocookie.com",
                "https://meet.jit.si",
                "blob:",
            ]),
            
            # Worker sources (REQUIRED FOR JITSI)
            'worker-src': " ".join([
                "'self'",
                "https://meet.jit.si",
                "blob:",
            ]),
            
            # Object sources
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
        
        # CRITICAL: Permissions Policy for camera and microphone (JITSI)
        response['Permissions-Policy'] = 'camera=*, microphone=*, display-capture=*'
        
        return response