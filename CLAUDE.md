# News Digest

Automated news digest emails produced by scheduled remote Claude Code agents. Each agent researches news, writes a JSON data file, then renders and sends an HTML email via `render.py`.

## Architecture

```
Scheduled trigger (Anthropic cloud)
  → Agent researches news (WebFetch + WebSearch)
  → Writes /tmp/stories.json
  → Runs: python3 render.py --template <name> --data /tmp/stories.json --send
  → Email sent via Resend API
```

## Digests

| Digest | Template | Schedule | Sections |
|--------|----------|----------|----------|
| Iran Conflict Daily | `iran-daily` | Daily 12:00 UTC (8am ET) | Military, Diplomatic, Humanitarian, Economic |
| Global Weekly | `global-weekly` | Sundays 12:00 UTC (8am ET) | Americas, Europe, Asia-Pacific, Middle East & Africa, Economy & Markets, Science & Technology |
| NYC Weekly | `nyc-weekly` | Sundays 12:00 UTC (8am ET) | City Hall & Politics, Transit & Infrastructure, Housing & Real Estate, Public Safety, Culture/Food/Events, Business & Economy, Education |
| Agentic Engineering Monthly | `agentic-monthly` | 1st of month 13:00 UTC (9am ET) | Setups, Patterns, Releases |
| Indie SaaS Monthly | `indie-saas-monthly` | 1st of month 13:00 UTC (9am ET) | Factory Flows, Launches, Stacks |

## Remote Triggers (3-slot limit)

| Trigger | ID | Sends |
|---------|-----|-------|
| Daily Iran War Update | `trig_016FofHKZEw7RrU7Trh5CQdY` | Iran daily |
| Weekly Global + NYC | `trig_018ygtozXBKo5TANpFuZLSxG` | Global weekly + NYC weekly |
| Monthly Agentic + Indie SaaS | `trig_01VWaVE6Ab2tNTb6hUtCTKty` | Agentic monthly + Indie SaaS monthly |

## Key Files

- `render.py` — CLI that loads a template, renders JSON data into HTML, and optionally sends via Resend. Flags: `--template`, `--data`, `--send`, `--output`.
- `templates/*.html` — HTML email templates using Python `string.Template` (`$variable` substitution). All currently extend the same base structure.
- `examples/*.json` — Sample JSON data files showing the expected schema.

## JSON Data Schema

```json
{
  "title": "string",
  "date_range": "string",
  "subject": "string (used as email subject)",
  "summary": ["bullet strings"],
  "stories": [
    {
      "section": "string",
      "headline": "string",
      "bullets": ["strings"],
      "sources": [{"name": "string", "url": "string"}],
      "framing_watch": "optional string"
    }
  ],
  "this_week": ["optional, NYC only"],
  "what_to_watch": ["optional developing stories"],
  "sources_consulted": "string"
}
```

## Environment

- `RESEND_API_KEY` — Required for `--send`. Already configured in the Anthropic cloud default environment.
- `DIGEST_TO_EMAIL` — Recipient (default: `cotto3@icloud.com`)
- `DIGEST_FROM_EMAIL` — Sender (default: `digest@morningtide.news`)

## Remote Execution

Triggers are managed via `RemoteTrigger` API (or https://claude.ai/code/scheduled). The agents run in Anthropic's cloud with a git checkout of this repo. Allowed tools: `Bash`, `Write`, `WebSearch`, `WebFetch`.
