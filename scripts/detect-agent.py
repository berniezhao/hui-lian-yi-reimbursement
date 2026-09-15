#!/usr/bin/env python3
"""Detect the host agent name for the reimbursement signature line.

Never trust the model's self-report: several agents' environment variables can
coexist in one session (e.g. a Codex plugin installed inside Claude Code).
Only the host-process markers below are authoritative, checked most-specific
first. Prints a display name, or `AI助手` when nothing matches.
"""
import os
import sys

# (display name, [env vars that only the host process sets])
HOSTS = [
    # WorkBuddy must be checked first: it co-injects other agents' session
    # vars (e.g. CLAUDE_SESSION_ID) but these two are host-exclusive.
    ("WorkBuddy", ["CLIENT_INFO_IDE_TYPE", "WORKBUDDY_APP_VERSION"]),
    ("Claude Code", ["CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"]),
    ("Codex", ["CODEX_SANDBOX", "CODEX_HOME", "CODEX_CLI_VERSION"]),
    ("Cursor", ["CURSOR_AGENT", "CURSOR_TRACE_ID"]),
    ("GitHub Copilot", ["COPILOT_AGENT_ID", "GITHUB_COPILOT_CLI"]),
    ("Gemini CLI", ["GEMINI_CLI", "GEMINI_SANDBOX"]),
]

FALLBACK = "AI助手"


def detect() -> str:
    for name, keys in HOSTS:
        if any(os.environ.get(k) for k in keys):
            return name

    # Generic marker some harnesses set, e.g. `claude-code_2-1-270_agent`.
    raw = os.environ.get("AI_AGENT", "").strip()
    if raw:
        slug = raw.split("_")[0].lower()
        for name, _ in HOSTS:
            if slug == name.lower().replace(" ", "-"):
                return name
        return raw.split("_")[0]

    return FALLBACK


if __name__ == "__main__":
    print(detect())
    sys.exit(0)
