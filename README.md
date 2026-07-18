# Emberbrook ✦

A cozy couch co-op RPG for two. The TV (your MacBook's browser) shows the world;
each phone becomes a controller over your home Wi-Fi.

**Chapter One — The Dimming Heartlight**: wander the village of Emberbrook, meet
the townsfolk, receive a quest from Elder Rowan, and open the Old Gate — together.

## How to play

1. Install & start (first time only needs the install):

   ```sh
   npm install
   npm start
   ```

2. Connect the MacBook to the TV, open **http://localhost:3000** in a browser,
   and make it fullscreen (`⌃⌘F` in Chrome/Safari).

3. Each phone (on the **same Wi-Fi**) scans the QR code on screen — or types the
   `http://<your-mac-ip>:3000/join` address shown under it. Pick a name and a
   hero, then **Set forth**.

4. Left thumb = walk. **A** = talk / act. Find the ✦ marker.

Click anywhere on the TV page once to enable the music (`M` mutes it).

### Notes

- Testing without phones: on the TV keyboard, `WASD`+`E` controls Player One and
  arrow keys+`Enter` controls Player Two.
- If a phone locks or drops off Wi-Fi, just reopen the page and join with the
  same name — you'll get your character back where you left them.
- If phones can't connect, macOS may be blocking the port: System Settings →
  Network → Firewall, allow incoming connections for `node`.
- Refreshing the TV page restarts the chapter.
