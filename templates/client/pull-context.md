---
name: pull-context
description: Brings everything new about this client into context/ (Upwork messages, call notes, the proposal and the onboarding doc) and updates context/client.md. Run it any time.
---

# /pull-context

Brings this folder up to date with everything known about the client. It never contacts the
client or Upwork.

1. Read `.client.json` for `job_id` and `upwork_repo`.
2. Run `python3 "<upwork_repo>/code/client_workspace.py" pull <job_id>`. It copies what is new
   or changed for this client into `context/`, and the onboarding doc into
   `output/onboarding.md`. Each line it prints is one file: `ADDED`, `CHANGED`, or `YOURS` for
   a file you put in `context/` yourself since the last pull.
3. Read every file it printed.
4. Update `context/client.md` from them: correct what is out of date, fill each
   `_not recorded yet_` that is now known, and add anything new under its heading. Keep the
   client's own words and never guess. Update `**Next:**` in `CLAUDE.md` if it changed.
5. Say in three lines or fewer what changed in `context/client.md`. If the script printed
   `Nothing new`, say so and stop.

For today's Upwork messages, run `/dashboard` in the Upwork repo first: this skill copies
what that repo already has.
