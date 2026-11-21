# Nutcracker ticket watcher

Checks the Teatr Wielki Poznań ticket shop every 15 minutes for free seats at
"Dziadek do orzechów" (12–22 Dec 2026) and sends a push notification via [ntfy](https://ntfy.sh)
when seats show up. It runs on GitHub Actions, so your PC can be off.

## Setup

1. **Phone:** install the **ntfy** app (Android / iOS), tap **+**, and subscribe to a hard-to-guess
   topic name, e.g. `dziadek-7f3k9q2x`. Anyone who knows the name can read the messages, so keep it secret.
2. **Repo secret:** in the GitHub repo, go to *Settings → Secrets and variables → Actions →
   New repository secret*. Name it `NTFY_TOPIC` and set the value to your topic name.
3. **Test:** go to *Actions → Check Nutcracker tickets → Run workflow*, leave "Send a test
   notification" ticked, and run it. Your phone should get a "Ticket watcher test" message.

## How it works

- `check_tickets.py` reads `https://bilety.opera.poznan.pl/termin.html?id_wydarzenia=28`, parses
  "Ilość wolnych miejsc" for each performance, and alerts when a show has more free seats than on
  the previous run. Tapping the notification opens the ticket shop.
- `state.json` remembers the last seen counts, so you aren't alerted every 15 minutes about the same seats.
- If the page can't be read (shop down, layout changed), the run fails and GitHub emails you.

## Notes

- Keep the repo **public**: Actions minutes are then free and unlimited. A private repo gets 2,000
  free minutes a month, which runs every 15 minutes would exceed; there, change the cron to
  `*/30 * * * *`.
- GitHub may start scheduled runs a few minutes late.
- After 22 Dec, disable the workflow (*Actions → Check Nutcracker tickets → ⋯ → Disable workflow*)
  or delete the repo.
