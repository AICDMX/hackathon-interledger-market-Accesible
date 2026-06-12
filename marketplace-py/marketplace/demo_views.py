from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Sum

from audio.models import AudioSnippet
from jobs.models import Job, JobApplication, JobSubmission
from users.models import User

DEMO_PASSWORD = "accessovox"
SESSION_KEY = "demo_guide_authed"


def _check_auth(request):
    """Check demo password. Returns None if authed, or HttpResponse if not."""
    if request.session.get(SESSION_KEY):
        return None
    if request.method == "POST" and request.POST.get("password") == DEMO_PASSWORD:
        request.session[SESSION_KEY] = True
        return None
    if request.method == "POST":
        return _render_login(request, error=True)
    return _render_login(request)


def _get_stats():
    """Gather stats used across demo pages."""
    languages = set()
    for val in Job.objects.values_list("target_language", flat=True):
        if val:
            languages.add(val.strip())

    creator_languages = set()
    for val in User.objects.filter(role__in=["creator", "both"]).values_list("native_languages", flat=True):
        if val:
            for lang in val.split(","):
                lang = lang.strip()
                if lang and lang != "es":
                    creator_languages.add(lang)

    total_value = Job.objects.aggregate(total=Sum("budget"))["total"] or 0
    completed_value = Job.objects.filter(status="complete").aggregate(total=Sum("budget"))["total"] or 0

    return {
        "user_count": User.objects.count(),
        "funder_count": User.objects.filter(role="funder").count(),
        "creator_count": User.objects.filter(role__in=["creator", "both"]).count(),
        "job_count": Job.objects.count(),
        "active_job_count": Job.objects.filter(status__in=["recruiting", "selecting", "submitting"]).count(),
        "completed_job_count": Job.objects.filter(status="complete").count(),
        "app_count": JobApplication.objects.count(),
        "sub_count": JobSubmission.objects.count(),
        "job_language_count": len(languages),
        "creator_language_count": len(creator_languages),
        "audio_snippet_count": AudioSnippet.objects.count(),
        "total_value": int(total_value),
        "completed_value": int(completed_value),
    }


def demo_directory(request):
    """Master directory page — links to all demo sections."""
    auth_response = _check_auth(request)
    if auth_response:
        return auth_response
    context = _get_stats()
    context["page"] = "directory"
    return render(request, "demo/directory.html", context)


def demo_story(request):
    """Page 1: The problem, the solution, the impact."""
    auth_response = _check_auth(request)
    if auth_response:
        return auth_response
    context = _get_stats()
    context["page"] = "story"
    return render(request, "demo/story.html", context)


def demo_walkthrough(request):
    """Page 2: Interactive guided walkthrough."""
    auth_response = _check_auth(request)
    if auth_response:
        return auth_response

    context = _get_stats()
    context["page"] = "walkthrough"
    context["featured_reviewing"] = Job.objects.filter(status="reviewing").first()
    context["featured_submitting"] = Job.objects.filter(status="submitting").first()
    context["featured_complete"] = Job.objects.filter(status="complete").first()
    context["funders"] = User.objects.filter(role="funder")
    return render(request, "demo/walkthrough.html", context)


def demo_logins(request):
    """Page 3: All credentials and technical reference."""
    auth_response = _check_auth(request)
    if auth_response:
        return auth_response

    context = _get_stats()
    context["page"] = "logins"
    return render(request, "demo/logins.html", context)


def _render_login(request, error=False):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Native Language Market — Demo</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #f8f6f3;
            color: #1e293b;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .box {
            background: #fff;
            border: 1px solid #e7e5e4;
            border-radius: 16px;
            padding: 3rem;
            width: 100%;
            max-width: 400px;
            text-align: center;
            box-shadow: 0 4px 24px rgba(0,0,0,0.06);
        }
        .logo { font-size: 2rem; margin-bottom: 0.5rem; }
        h1 {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
            color: #1a365d;
        }
        .sub {
            color: #64748b;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }
        input[type="password"] {
            width: 100%;
            padding: 0.85rem 1rem;
            background: #f8f6f3;
            border: 1px solid #e7e5e4;
            border-radius: 10px;
            color: #1e293b;
            font-size: 1rem;
            text-align: center;
            letter-spacing: 0.1em;
            margin-bottom: 1rem;
        }
        input:focus { outline: 2px solid #c2410c; border-color: #c2410c; }
        button {
            width: 100%;
            padding: 0.85rem;
            background: #c2410c;
            color: #fff;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover { background: #9a3412; }
        .error { color: #dc2626; font-size: 0.85rem; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <div class="box">
        <div class="logo">&#127760;</div>
        <h1>Native Language Market</h1>
        <p class="sub">Enter password to view the demo showcase</p>
        """ + ('<p class="error">Incorrect password. Try again.</p>' if error else '') + """
        <form method="post">
            <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">
            <input type="password" name="password" placeholder="Password" autofocus>
            <button type="submit">View Demo</button>
        </form>
    </div>
</body>
</html>"""
    from django.middleware.csrf import get_token
    html = html.replace("{csrf}", get_token(request))
    return HttpResponse(html)
