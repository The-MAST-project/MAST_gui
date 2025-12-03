"""
Context processor to make user capabilities available in templates.
"""

def user_capabilities(request):
    """Add user capabilities to template context"""
    capabilities = []
    if request.user.is_authenticated:
        capabilities = request.user.get_capabilities()
    
    return {
        'user_capabilities': capabilities,
    }
