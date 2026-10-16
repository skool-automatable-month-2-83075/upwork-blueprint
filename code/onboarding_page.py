#!/usr/bin/env python3
"""The onboarding checklist as one page, built from jobs/<id>/project.md.

    python3 code/onboarding_page.py <job_id>            write onboarding.html, ticks shown, not editable
    python3 code/onboarding_page.py <job_id> --serve    run it on this computer, ticks save as you go

The member screenshares this page with the client on the kickoff call, so it carries the
client's name, the project and the six client-facing sections, and nothing internal. Served,
each tick is written straight back into `## What I need from you` in project.md as `- [x]`, so the next open
starts where the call left off. Only this computer can reach it, and only the page it
served can save.

The look is the shared sheet of `code/context_page.py` on the tokens in
`website/app/tokens.css`; only the checklist is styled here.
"""
import argparse
import http.server
import json
import os
import pathlib
import re
import secrets
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code'))
import call_prep_page as page  # noqa: E402  (inline, split, items)
import context_page as cp  # noqa: E402  (the shared sheet)
import document_check  # noqa: E402  (the four sections a brief must have)
import pipeline  # noqa: E402  (read-only use: jobs_dir)

ID = re.compile(r'^[0-9]{6,25}$')
TICK = re.compile(r'^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$')
HEADINGS = [heading[3:] for heading in document_check.ARTIFACTS['project'][1]]
CHECKLIST = 'What I need from you'
SHOWN = ('The goal', 'Done looks like', CHECKLIST, 'How we talk', 'The roadmap', 'Check-ins')
PORT = 8765
LOCAL = ('127.0.0.1', 'localhost')

CSS = """
  .sheet { max-width: 860px; margin-top: 36px; padding: 32px 44px 30px; }
  h1 { font-size: clamp(30px, 3.4vw, 42px); letter-spacing: -1px; }
  section { padding-top: 22px; }
  h2 { margin-bottom: 10px; display: flex; justify-content: space-between; align-items: baseline; }
  .count { font: 400 11px/1 var(--mono); letter-spacing: 1.4px; color: var(--label); }
  .checks label { display: grid; grid-template-columns: 26px 1fr; gap: 12px; align-items: start; padding: 12px 0;
                  border-top: 1px solid var(--hairline); font-size: 16px; line-height: 1.45; color: var(--ink); cursor: pointer; }
  .checks label:first-child { border-top: 0; }
  .checks input { width: 20px; height: 20px; margin: 2px 0 0; accent-color: var(--terracotta); cursor: pointer; }
  .checks input:disabled { cursor: default; } .checks input:disabled + span { cursor: default; }
  .checks input:focus-visible { outline: 2px solid var(--terracotta-text); outline-offset: 2px; }
  .checks input:checked + span { color: var(--label); text-decoration: line-through; }
  .plain li { padding: 3px 0; font-size: 16px; line-height: 1.45; color: var(--ink); }
  .unsaved { margin-top: 10px; font-size: 13px; color: var(--bad-text); }
  a { color: var(--terracotta-text); text-decoration: underline; text-underline-offset: 2px; }
  @media (max-width: 880px) { .sheet { margin-top: 16px; padding: 24px 18px; } }
"""

SCRIPT = """
(function () {
  var boxes = document.querySelectorAll('.checks input'), count = document.getElementById('count'),
      note = document.getElementById('unsaved');
  function show() {
    var done = 0; boxes.forEach(function (b) { if (b.checked) done++; });
    count.textContent = done + ' of ' + boxes.length + ' done';
  }
  boxes.forEach(function (box, i) {
    box.addEventListener('change', function () {
      show();
      fetch('/tick', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Token': TOKEN },
                       body: JSON.stringify({ i: i, done: box.checked }) })
        .then(function (r) { if (!r.ok) throw new Error(); note.hidden = true; })
        .catch(function () { box.checked = !box.checked; show(); note.hidden = false; });
    });
  });
})();
"""


class NotReady(Exception):
    """The brief is missing or is not in the shape this page reads."""


def checklist(body):
    rows = [TICK.match(line) for line in body.splitlines()]
    return [(mark.group(1).lower() == 'x', mark.group(2)) for mark in rows if mark]


def sections_of(text):
    head, sections = page.split(text, 2)
    if [name for name, _ in sections] != HEADINGS:
        raise NotReady('project.md is not in the four-section shape. Run /onboarding <job id> again to rewrite it.')
    return head, dict(sections)


def block(name, body, ticks, done, boxes):
    """One section of the page: the checklist with its ticks, or the short lines under a heading."""
    if name != CHECKLIST:
        lines = [re.sub(r'^\s*[-*]\s+', '', line).strip() for line in body.splitlines() if line.strip()]
        return f'<section><h2>{cp.esc(name)}</h2>{page.items(lines, "plain")}</section>\n'
    return (f'<section><h2>{cp.esc(name)} <span class="count" id="count">{done} of {len(ticks)} done</span></h2>'
            f'<div class="checks">{boxes}</div>'
            '<p class="unsaved" id="unsaved" hidden>That tick did not save. Reopen the checklist and try again.</p></section>\n')


def build(text, token=None):
    """The page. With a token it saves ticks to the server that served it; without one it only shows them."""
    head, found = sections_of(text)
    ticks = checklist(found[CHECKLIST])
    if not ticks:
        raise NotReady(f'the {CHECKLIST} section has no "- [ ] item" lines.')
    title = next((line[2:].strip() for line in head.splitlines() if line.startswith('# ')), 'Onboarding')
    client, _, project = title.partition(' - ')
    lock = '' if token else ' disabled'
    boxes = ''.join(f'<label><input type="checkbox"{" checked" if done else ""}{lock}><span>{page.inline(item)}</span></label>'
                    for done, item in ticks)
    done = sum(1 for ticked, _ in ticks if ticked)
    script = f'<script>var TOKEN = {json.dumps(token)};{SCRIPT}</script>\n' if token else ''
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{cp.esc(client)} · Onboarding</title>\n<style>' + cp.tokens() + cp.CSS + CSS + '</style>\n</head>\n<body>\n'
            '<main class="sheet">\n'
            f'<p class="kicker">Onboarding</p><h1>{cp.esc(client)}</h1>'
            + (f'<p class="headline">{cp.esc(project)}</p>' if project else '') + '\n'
            + ''.join(block(name, found[name], ticks, done, boxes) for name in SHOWN)
            + '</main>\n' + script + '</body>\n</html>\n')


def set_tick(text, index, done):
    """project.md with one checklist line ticked or unticked, and nothing else changed."""
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.strip() == f'## {CHECKLIST}'), None)
    if start is None:
        raise NotReady(f'project.md has no {CHECKLIST} section.')
    seen = -1
    for i in range(start + 1, len(lines)):
        if lines[i].lstrip().startswith('## '):
            break
        if TICK.match(lines[i]):
            seen += 1
            if seen == index:
                lines[i] = re.sub(r'\[[ xX]\]', '[x]' if done else '[ ]', lines[i], count=1)
                return ''.join(lines)
    raise NotReady('that checklist item is not in project.md.')


def write(path, text):
    """Replace a file whole, so a stopped save never leaves half a brief."""
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}.')
    with os.fdopen(handle, 'w', encoding='utf-8') as out:
        out.write(text)
    os.replace(temporary, path)


def serve(job_id, source, target):
    token = secrets.token_urlsafe(24)

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def local(self):
            return (self.headers.get('Host') or '').rsplit(':', 1)[0] in LOCAL

        def reply(self, code, body, kind='application/json'):
            data = body.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', f'{kind}; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self.local() or self.path.split('?')[0] not in ('/', '/onboarding.html'):
                return self.reply(404, 'Not found', 'text/plain')
            try:
                self.reply(200, build(source.read_text(encoding='utf-8'), token), 'text/html')
            except (OSError, UnicodeError, NotReady) as problem:
                self.reply(500, str(problem), 'text/plain')

        def do_POST(self):
            if (not self.local() or self.path != '/tick'
                    or not secrets.compare_digest(self.headers.get('X-Token') or '', token)):
                return self.reply(403, '{"error": "refused"}')
            try:
                length = min(int(self.headers.get('Content-Length') or 0), 1000)
                value = json.loads(self.rfile.read(length))
                index, done = value['i'], value['done']
                if type(index) is not int or type(done) is not bool:
                    raise ValueError
                text = set_tick(source.read_text(encoding='utf-8'), index, done)
                write(source, text)
                write(target, build(text))
            except (OSError, UnicodeError, ValueError, KeyError, TypeError, NotReady):
                return self.reply(400, '{"error": "not saved"}')
            self.reply(200, '{"ok": true}')

    for port in range(PORT, PORT + 20):
        try:
            server = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
            break
        except OSError:
            continue
    else:
        print(f'ABORT: ports {PORT} to {PORT + 19} are all in use.')
        return 1
    print(f'Checklist for {job_id}: http://127.0.0.1:{port}/  (ticks save to {pipeline.shown(source)})', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('job_id')
    parser.add_argument('--serve', action='store_true', help='run it on this computer so ticks save')
    args = parser.parse_args(argv)
    if not ID.fullmatch(args.job_id):
        print('ABORT: that job id is not valid.')
        return 1
    folder = pipeline.jobs_dir() / args.job_id
    source, target = folder / 'project.md', folder / 'onboarding.html'
    try:
        built = build(source.read_text(encoding='utf-8'))
    except (OSError, UnicodeError):
        print(f'ABORT: no project.md for {args.job_id} yet. /onboarding {args.job_id} writes it.')
        return 1
    except NotReady as problem:
        print(f'ABORT: {problem}')
        return 1
    write(target, built)
    if args.serve:
        return serve(args.job_id, source, target)
    print(f'{pipeline.shown(target)} written')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
