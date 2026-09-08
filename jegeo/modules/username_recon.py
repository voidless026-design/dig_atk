"""Public username footprint check — Sherlock/theHarvester-style, scoped down.

Every check here is one ordinary, unauthenticated HTTP GET to a platform's
public profile URL, deciding "found" / "not found" from the response's
status code (and, for a couple of sites that always return 200, a known
"no such user" marker in the page body). Nothing is scraped beyond that —
no private data, no friends/followers lists, no login.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget

from jegeo.core import http
from jegeo.modules.base import BaseModule

# Anti-bot / CDN challenge pages some sites return with HTTP 200 for *any*
# URL, real or not (Fastly "Client Challenge", Cloudflare "Just a moment",
# etc.). A 200 carrying one of these is not a real profile page, so it's
# reported as "unknown" rather than a false "found".
CHALLENGE_MARKERS = (
    "client challenge", "just a moment", "attention required",
    "checking your browser", "are you a human", "captcha",
)

# (platform name, profile URL template, check mode, "not found" marker)
#   mode "status"      -> HTTP 200 = found, HTTP 404 = not found, else unknown
#   mode "text_absent" -> HTTP 200 and marker missing from body = found;
#                         marker present = not found (site always returns 200)
PLATFORMS = [
    ("GitHub", "https://github.com/{u}", "status", None),
    ("GitLab", "https://gitlab.com/{u}", "status", None),
    ("Hacker News", "https://news.ycombinator.com/user?id={u}", "text_absent", "No such user"),
    ("Steam", "https://steamcommunity.com/id/{u}", "text_absent", "The specified profile could not be found"),
    ("YouTube", "https://www.youtube.com/@{u}", "status", None),
    ("Dev.to", "https://dev.to/{u}", "status", None),
    ("npm", "https://www.npmjs.com/~{u}", "status", None),
    ("PyPI", "https://pypi.org/user/{u}/", "status", None),
    ("Docker Hub", "https://hub.docker.com/v2/users/{u}/", "status", None),
    ("Keybase", "https://keybase.io/{u}", "status", None),
]


def check_platform(name: str, template: str, mode: str, marker: str | None, username: str):
    url = template.format(u=username)
    status, body = http.probe(url)
    if status is None:
        return name, url, "unknown", "request failed"
    challenged = any(m in body.lower() for m in CHALLENGE_MARKERS)
    if mode == "status":
        if status == 200:
            if challenged:
                return name, url, "unknown", "blocked by an anti-bot challenge page"
            return name, url, "found", None
        if status == 404:
            return name, url, "not_found", None
        return name, url, "unknown", f"HTTP {status}"
    if mode == "text_absent":
        if status != 200:
            return name, url, "unknown", f"HTTP {status}"
        if challenged:
            return name, url, "unknown", "blocked by an anti-bot challenge page"
        if marker and marker.lower() in body.lower():
            return name, url, "not_found", None
        return name, url, "found", None
    return name, url, "unknown", "bad platform config"


class UsernameReconModule(BaseModule):
    display_name = "Username Recon"
    glyph = "⚉"
    tagline = "Public profile footprint across major platforms"
    notice = "Ordinary, unauthenticated HTTP checks against public profile pages — for your own footprint or an authorized OSINT assessment only."

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        form = QFormLayout(wrapper)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("username to check")
        form.addRow("USERNAME", self.username_input)
        return wrapper

    def make_task(self):
        username = self.username_input.text().strip()
        if not username:
            raise ValueError("enter a username")

        def task(emit, is_cancelled):
            emit(f"checking {len(PLATFORMS)} platforms for '{username}'...", "meta")
            found = []
            with ThreadPoolExecutor(max_workers=len(PLATFORMS)) as pool:
                futures = {
                    pool.submit(check_platform, name, tmpl, mode, marker, username): name
                    for name, tmpl, mode, marker in PLATFORMS
                }
                for fut in as_completed(futures):
                    if is_cancelled():
                        for f in futures:
                            f.cancel()
                        emit("scan aborted", "warn")
                        return
                    name, url, verdict, detail = fut.result()
                    if verdict == "found":
                        emit(f"  [FOUND]      {name:<12} {url}", "success")
                        found.append(name)
                    elif verdict == "not_found":
                        emit(f"  [not found]  {name:<12}", "meta")
                    else:
                        emit(f"  [unknown]    {name:<12} ({detail})", "warn")

            emit(f"profile found on {len(found)}/{len(PLATFORMS)} platform(s)", "cyan")
            if found:
                emit(f"present on: {', '.join(found)}", "info")

        return task
