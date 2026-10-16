---
description: Turns a started Upwork contract into an onboarding doc to screenshare on the kickoff call, a kickoff message and a client folder.
argument-hint: "<job id>"
---

# /onboarding

**Before anything else, read [references/upwork-compliance.md](../../references/upwork-compliance.md) in full.** Where a step below reads looser, that file wins.

Before starting, read and follow [analytics capture: onboarding](../../references/analytics-capture.md#onboarding).

Six steps: match the contract, pull in the client's info, write the onboarding doc, pick the
kickoff message, create the client folder, open the doc. This command never accepts
an offer, starts a contract or sends a message.

## ROADMAP

Give this roadmap before the first tool call, including any read.

WHAT HAPPENS: match the contract, pull in what we know about the client, write the onboarding doc you go through on the kickoff call, give you two kickoff messages to pick from, create the client's folder and open the doc. About five minutes.
I NEED FROM YOU: confirm which contract is this job, and pick a message.
WHAT MIGHT GO WRONG: a pending offer is not a contract yet. A folder name already taken means you pick another.

## Step 1 · Find the contract and match it

If `jobs/<id>/project.md` already exists, onboarding was done: go straight to Step 5.

Run `python3 code/workspace.py` and `python3 code/pipeline.py get $ARGUMENTS`. The lead must
be `replied`, `call`, `offer` or `won`; an earlier one goes back to `/dashboard`.

Read `list_contracts` action `search`, using the stored `contract_id` or the job title. Page
only until it is found or results end. For fixed-price work read `list_milestones` too. Ask
the member which contract is this job, as a single choice with "none of these" last. None
means stop: no started contract, no onboarding.

Record the match: `{"contract_id": "...", "contract_client": "..."}` through
`python3 code/pipeline.py record <id> --file -`, then
`python3 code/pipeline.py set <id> won --note "Contract confirmed by the member"`.

## Step 2 · Pull in everything about the client

Read the pipeline record, everything in `jobs/<id>/` (job post, application, proposal, call
prep, call transcript, saved thread) and the contract from Step 1. From them, take:

- the business: name, website, what they do, where they serve, who decides
- what was sold: contract type, price or rate, milestones, start, deadline, scope and what is not included

The contract wins where it disagrees with the proposal. Anything not found is written as
"not recorded yet", never guessed.

## Step 3 · Write the onboarding doc

Write `jobs/<id>/project.md`. The first three lines are `# <client> - <project>`,
`Recorded <date>.` and `**Next:** <the first item the client owes>`. Then these sections,
in order. The first two are for the member only; the six after them are the onboarding doc
the member screenshares on the kickoff call:

- `## The client`: the business facts from Step 2
- `## What was sold`: the sold facts from Step 2
- `## The goal`: the result they hired you for, in their words, one sentence
- `## Done looks like`: one sentence, something you both watch happen, so done is never argued
- `## What I need from you`: one `- [ ] ` line each, asked once, up front
- `## How we talk`: one channel and one reply time, e.g. `Upwork messages, I reply within a day`
- `## The roadmap`: one line per milestone, in order, as `1. Build it: done = a test lead lands`
- `## Check-ins`: the same day every week, e.g. `Every Friday, 10 minutes on Upwork`
- `## Message`: Step 4

The six doc sections are short and client-facing: no reasons, no explanations, no
internal notes. Each `What I need from you` line is the thing, and the access level when
there is one, six words or fewer, usually four to seven lines:

```
- [ ] Google Ads: admin access
- [ ] Google Tag Manager: publish access
- [ ] Your booking link
- [ ] Who signs off each milestone
```

How we talk and Check-ins are proposals the member confirms on the call; use the examples
unless the thread already agreed something else.

## Step 4 · Pick the kickoff message

Fill both versions in [templates/onboarding/message.md](../../templates/onboarding/message.md):
replace every `<...>` and change nothing else. In the client's language. Show both in the
chat, in full, each in its own block. Then ask which to use as a single choice: Version A,
Version B. Write the picked one, without its heading, under `## Message`. Never send it.

Run `python3 code/document_check.py check project <id>` and fix every FAIL.

## Step 5 · Create the client folder

Run `python3 code/client_workspace.py where <id>` and say the path it prints. If it prints
`TAKEN`, offer another folder name as a single choice and pass it as `--slug` to every
command below.

Run `python3 code/client_workspace.py new <id>`, with no `--blueprint` flag. It creates the
client's own Claude Code project on this computer, outside this repository:

```
<client>/
  CLAUDE.md                     loads context/client.md every time Claude opens here
  .claude/skills/pull-context/  /pull-context: brings in anything new about this client
  references/                   docs and guides for this job
  .env                          keys and logins, never committed
  .gitignore
  context/                      client.md, call-notes.md, proposal.md, thread.json
  output/                       onboarding.md, then everything built for the client
```

If the folder was already there, run `python3 code/client_workspace.py pull <id>` instead,
which brings in whatever changed. Fill `context/client.md` from Step 2: replace each
`_not recorded yet_` you found and leave the rest. Set `**Next:**` in the folder's
`CLAUDE.md` to the first item the client still owes. Run
`python3 code/client_workspace.py check <id>` and fix every FAIL.

## Step 6 · Open the onboarding doc

Start `python3 code/onboarding_page.py <id> --serve` in the background and give the address
it prints. That page is the onboarding doc the member screenshares on the kickoff call. Each
tick saves straight into `## What I need from you` in `jobs/<id>/project.md`, so opening it
again shows where the call left off. To open it again later, run `/onboarding <id>`.

## Report

Use the completion report from `CLAUDE.md`, under 90 words, verdict first. **Built**: the
onboarding doc address, and the client folder's absolute path. **Still needed**: send the message
on Upwork. Then the picked message again in its own block, ready to paste. Last line:
`Upwork calls: N`, counting actual calls.
