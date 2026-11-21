"""Watch Teatr Wielki Poznań's ticket shop for free Nutcracker seats and push an ntfy alert.

Env vars:
  NTFY_TOPIC   ntfy topic to publish to (keep it secret; anyone who knows it can read it)
  TEST_NOTIFY  "true" -> always send a notification with the current status (to test your phone)
"""

import json
import os
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

EVENT_URL = "https://bilety.opera.poznan.pl/termin.html?id_wydarzenia=28"  # Dziadek do orzechów
STATE_FILE = Path(__file__).with_name("state.json")

SHOW_RE = re.compile(
    r"<h3>(\d{4}-\d{2}-\d{2})</h3>\s*<div>Ilo\S* wolnych miejsc:\s*(\d+)</div>"
    r".*?godz\.\s*(\d{1,2}:\d{2})",
    re.DOTALL,
)


def fetch_shows() -> dict[str, int]:
    req = urllib.request.Request(EVENT_URL, headers={"User-Agent": "Mozilla/5.0 (ticket-watcher)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    shows = {f"{d} {t}": int(n) for d, n, t in SHOW_RE.findall(html)}
    if not shows:
        # Page layout changed or the shop is down: fail loudly so GitHub emails you.
        raise RuntimeError("No performances found on the ticket page - check the URL/HTML.")
    return shows


def notify(topic: str, title: str, message: str, priority: str = "high") -> None:
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": priority, "Tags": "ticket", "Click": EVENT_URL},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=30).read()


def describe(shows: dict[str, int]) -> str:
    return "\n".join(f"{k}: {n} free" for k, n in sorted(shows.items()))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    test = os.environ.get("TEST_NOTIFY", "").lower() == "true"

    shows = fetch_shows()
    today = date.today().isoformat()
    shows = {k: n for k, n in shows.items() if k[:10] >= today}
    available = {k: n for k, n in shows.items() if n > 0}
    print(describe(shows) or "No upcoming performances.")

    previous = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    # Alert when a show gains seats compared with the last run (new returns), not on every run.
    new_seats = {k: n for k, n in available.items() if n > previous.get(k, 0)}
    STATE_FILE.write_text(json.dumps(available, indent=2, sort_keys=True) + "\n")

    if not topic:
        print("NTFY_TOPIC not set - skipping notification.")
        return
    if new_seats:
        notify(topic, "Nutcracker tickets available!", describe(available) + "\n\nTap to open the ticket shop.")
        print("Sent alert for:", ", ".join(sorted(new_seats)))
    elif test:
        body = describe(available) if available else "No free seats right now. The watcher is working."
        notify(topic, "Ticket watcher test", body, priority="default")
        print("Sent test notification.")


if __name__ == "__main__":
    main()
