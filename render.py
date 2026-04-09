#!/usr/bin/env python3
"""Render a news digest from JSON data + HTML template, then send via Resend."""

import argparse
import json
import os
import subprocess
import sys
from datetime import date
from string import Template


def load_template(template_name: str) -> str:
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    path = os.path.join(template_dir, f"{template_name}.html")
    with open(path) as f:
        return f.read()


def render_stories(stories: list[dict]) -> str:
    html = ""
    current_section = None
    for story in stories:
        section = story.get("section", "")
        if section != current_section:
            if current_section is not None:
                html += '<div style="height:8px"></div>\n'
            current_section = section
            html += (
                f'<h2 style="margin:28px 0 16px;padding:0 0 0 12px;font-size:13px;'
                f'text-transform:uppercase;letter-spacing:0.8px;color:#888;'
                f'font-weight:600;border-left:3px solid #1a1a1a">{section}</h2>\n'
            )

        html += (
            f'<div style="margin:0 0 20px;padding:16px 16px 12px;'
            f'border:1px solid #eee;border-radius:6px">\n'
        )
        html += (
            f'<h3 style="margin:0 0 10px;font-size:16px;font-weight:600;'
            f'line-height:1.3;color:#1a1a1a">{story["headline"]}</h3>\n'
        )
        html += '<ul style="margin:0 0 10px;padding-left:20px;color:#333">\n'
        for point in story.get("bullets", []):
            html += f'<li style="margin-bottom:4px;font-size:14px">{point}</li>\n'
        html += "</ul>\n"

        framing = story.get("framing_watch")
        if framing:
            html += (
                f'<div style="background:#fef9e7;padding:10px 12px;margin:0 0 10px;'
                f'font-size:13px;border-radius:4px;border-left:3px solid #f0c040;'
                f'color:#5a4e1a;line-height:1.4">'
                f'<strong>Framing Watch:</strong> {framing}</div>\n'
            )

        html += "</div>\n"

    return html


def render_sources_consulted(sources) -> str:
    """Render sources_consulted as dot-separated linked HTML.

    Accepts either a list of {"name", "url"} dicts (current schema) or a
    plain string (legacy schema — returned as-is so digests in flight during
    the schema migration keep rendering).
    """
    if isinstance(sources, str):
        return sources
    if not sources:
        return ""
    return " &middot; ".join(
        f'<a href="{s["url"]}" style="color:#666;text-decoration:none;'
        f'border-bottom:1px solid #ddd">{s["name"]}</a>'
        for s in sources
    )


def render_summary(summary: list[str]) -> str:
    html = '<ul style="margin:0;padding-left:20px;color:#333">\n'
    for point in summary:
        html += (
            f'<li style="margin-bottom:6px;font-size:14px;'
            f'line-height:1.5">{point}</li>\n'
        )
    html += "</ul>\n"
    return html


def render_extra_sections(data: dict) -> str:
    html = ""
    for key in ("this_week", "what_to_watch"):
        section = data.get(key)
        if not section:
            continue
        title = "This Week in NYC" if key == "this_week" else "What to Watch"
        html += (
            f'<div style="margin:0;padding:16px 28px 20px;'
            f'background:#f8f9fa;border-top:1px solid #e8e8e8">\n'
            f'<p style="margin:0 0 10px;font-size:13px;text-transform:uppercase;'
            f'letter-spacing:0.8px;color:#888;font-weight:600">{title}</p>\n'
            f'<ul style="margin:0;padding-left:20px;color:#333">\n'
        )
        for item in section:
            html += (
                f'<li style="margin-bottom:6px;font-size:14px;'
                f'line-height:1.5">{item}</li>\n'
            )
        html += "</ul>\n</div>\n"
    return html


def render(template_name: str, data: dict) -> str:
    template_str = load_template(template_name)
    t = Template(template_str)
    return t.safe_substitute(
        title=data.get("title", "News Digest"),
        date_range=data.get("date_range", str(date.today())),
        summary=render_summary(data.get("summary", [])),
        stories=render_stories(data.get("stories", [])),
        extra_sections=render_extra_sections(data),
        sources_consulted=render_sources_consulted(data.get("sources_consulted", "")),
    )


def send_email(html: str, subject: str):
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("ERROR: RESEND_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    to_email = os.environ.get("DIGEST_TO_EMAIL", "cotto3@icloud.com")
    to_list = [e.strip() for e in to_email.split(",")]
    from_email = os.environ.get("DIGEST_FROM_EMAIL", "digest@morningtide.news")

    payload = json.dumps({
        "from": from_email,
        "to": to_list,
        "subject": subject,
        "html": html,
    })

    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST", "https://api.resend.com/emails",
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json",
            "-d", payload,
        ],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Render and send a news digest email")
    parser.add_argument("--template", required=True, help="Template name (e.g., global-weekly)")
    parser.add_argument("--data", required=True, help="Path to JSON data file")
    parser.add_argument("--send", action="store_true", help="Send the email via Resend")
    parser.add_argument("--output", help="Write rendered HTML to this file (for preview)")
    args = parser.parse_args()

    with open(args.data) as f:
        data = json.load(f)

    html = render(args.template, data)

    if args.output:
        with open(args.output, "w") as f:
            f.write(html)
        print(f"Written to {args.output}")

    if args.send:
        subject = data.get("subject", f"News Digest — {date.today()}")
        send_email(html, subject)

    if not args.output and not args.send:
        print(html)


if __name__ == "__main__":
    main()
