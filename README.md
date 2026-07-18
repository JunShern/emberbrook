# Emberbrook 🕯

A couch co-op story RPG for two players. The TV (a MacBook browser, fullscreened)
is the game screen; each phone becomes a controller over your home Wi-Fi.

**Chapter One — Emberwake.** A traveling mapmaker arrives in a village that isn't
on any map, an hour before the night that erases it. Two strangers — the only two
the Hush cannot touch — are thrust together to carry the last warm flame in the
valley. One knows the way; one holds the fire. A cat has opinions.

Played in three acts: **P1 plays June's arrival alone**, then **P2 plays Cole's
lamplighting rounds alone**, then their stories converge and it's one shared
screen from there.

## How to play

1. Install & start (install needed once):

   ```sh
   npm install
   npm start
   ```

2. Connect the MacBook to the TV, open **http://localhost:3000**, fullscreen it
   (`⌃⌘F`), and click once anywhere to enable music (`M` mutes).

3. Each phone (on the **same Wi-Fi**) scans the QR code on screen, then claims a
   keeper: **June** (plays first) or **Cole** (enters in Act II).

4. Left thumb = walk. **A** = talk / act / advance dialogue. Some moments need
   you both to **hold A together**.

### Notes

- Testing without phones: `WASD`+`E` plays June, arrow keys+`Enter` plays Cole.
- If a phone locks or drops, reopen the page and tap your keeper again — you
  resume where you were.
- If phones can't connect: System Settings → Network → Firewall → allow `node`.
- Refreshing the TV page restarts the chapter.

See `ROADMAP.md` for the world bible, planned party members, and chapters 2–10.
