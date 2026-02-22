Web version — Hosting & Usage

This folder includes a simple static web app (hot-seat/pass-and-play) to play the Scenario & Response game in a browser.

Files
- index.html
- css/styles.css
- js/app.js
- data/cards.json

Local testing
From the project root, run a simple static server, for example:

```bash
python -m http.server 8000
# then open http://localhost:8000 in a browser
```

Hosting online
- GitHub Pages: push the folder to a repo and enable Pages on the `main` branch (or use a `/docs` folder).
- Netlify/Vercel: drag & drop the project root or connect the repo for automated deploys.

Notes on multiplayer
- This implementation is single-device hot-seat (players pass the device).
- For real-time online multiplayer, a small server with WebSocket support is needed. I can scaffold a Node.js server with WebSocket endpoints and a simple lobby system if you want a live online game.
