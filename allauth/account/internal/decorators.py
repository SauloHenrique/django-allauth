from functools import wraps

from django.contrib.auth import decorators
from django.http import HttpResponseRedirect
from django.urls import reverse

from allauth.account import app_settings
from allauth.account.internal.stagekit import (
    get_pending_stage,
    redirect_to_pending_stage,
)
from allauth.account.stages import LoginStageController
from allauth.account.utils import get_login_redirect_url


def _dummy_login_not_required(view_func):
    return view_func


login_not_required = getattr(
    decorators, "login_not_required", _dummy_login_not_required
)


def login_stage_required(stage: str, redirect_urlname: str):
    def decorator(view_func):
        @login_not_required
        @wraps(view_func)
        def _wrapper_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                return HttpResponseRedirect(get_login_redirect_url(request))
            login_stage = LoginStageController.enter(request, stage)
            if not login_stage:
                return HttpResponseRedirect(reverse(redirect_urlname))
            request._login_stage = login_stage
            return view_func(request, *args, **kwargs)

        return _wrapper_view

    return decorator


def unauthenticated_only(function=None):
    def decorator(view_func):
        @login_not_required
        @wraps(view_func)
        def _wrapper_view(request, *args, **kwargs):
            if app_settings.AUTHENTICATED_LOGIN_REDIRECTS:
                if request.user.is_authenticated:
                    return HttpResponseRedirect(get_login_redirect_url(request))
                else:
                    stage = get_pending_stage(request)
                    if stage and stage.is_resumable(request):
                        return redirect_to_pending_stage(request, stage)
            return view_func(request, *args, **kwargs)

        return _wrapper_view

    if function:
        return decorator(function)
    return decorator