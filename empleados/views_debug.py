from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.http import JsonResponse
from .context_processors import periodo_global
from .utils import MONTH_NAMES

def is_presidencia(user):
    return user.is_authenticated and user.is_staff

@login_required(login_url="login")
@user_passes_test(is_presidencia)
def debug_context(request):
    """Vista temporal para debuggear el context processor"""
    context = periodo_global(request)
    
    debug_info = {
        'session_data': dict(request.session),
        'context_data': context,
        'month_names': MONTH_NAMES,
    }
    
    return JsonResponse(debug_info, indent=2)