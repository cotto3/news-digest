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
            current_section = section
            html += f'<h2 style="font-size:18px;border-bottom:1px solid #ddd;padding-bottom:4px">{section}</h2>\n'

        html += f'<h3 style="font-size:15px;margin-bottom:4px">{story["headline"]}</h3>\n'
        html += '<ul style="margin-top:4px">\n'
        for point in story.get("bullets", []):
            html += f"<li>{point}</li>\n"
        html += "</ul>\n"

        sources = story.get("sources", [])
        if sources:
            links = " | ".join(
                f'<a href="{s["url"]}">{s["name"]}</a>' for s in sources
            )
            html += f'<p style="font-size:13px;color:#666">Sources: {links}</p>\n'

        framing = story.get("framing_watch")
        if framing:
            html += f'<div style="background:#fffde7;padding:8px;margin:8px 0;font-size:13px"><strong>Framing Watch:</strong> {framing}</div>\n'

    return html


def render_summary(summary: list[str]) -> str:
    html = '<ul style="margin-top:4px">\n'
    for point in summary:
        html += f"<li>{point}</li>\n"
    html += "</ul>\n"
    return html


def render_extra_sections(data: dict) -> str:
    html = ""
    for key in ("this_week", "what_to_watch"):
        section = data.get(key)
        if not section:
            continue
        title = "This Week in NYC" if key == "this_week" else "What to Watch"
        html += f'<h2 style="font-size:18px;border-bottom:1px solid #ddd;padding-bottom:4px">{title}</h2>\n'
        html += '<ul style="margin-top:4px">\n'
        for item in section:
            html += f"<li>{item}</li>\n"
        html += "</ul>\n"
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
        sources_consulted=data.get("sources_consulted", ""),
    )


def send_email(html: str, subject: str):
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("ERROR: RESEND_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    to_email = os.environ.get("DIGEST_TO_EMAIL", "cotto3@icloud.com")
    from_email = os.environ.get("DIGEST_FROM_EMAIL", "notifications@pageauditors.com")

    payload = json.dumps({
        "from": from_email,
        "to": to_email,
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
