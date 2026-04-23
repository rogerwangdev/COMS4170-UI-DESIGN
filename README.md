# COMS4170-UI-DESIGN — Charcoal Grill Coach

A ~10-minute interactive tutorial that teaches the basics of charcoal grilling.
HW 10 technical prototype: Flask + HTML/JS/jQuery/Bootstrap.

## Status

Current focus is on basic functionality and page transitions. Most visuals
(lesson images, quiz illustrations, final result graphics) are still
placeholders and will be swapped in as we finish art in a later pass.

## Run it

```bash
cd FinalProject/COMS4170-UI-DESIGN
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000/>.

## Routes

| Path | Purpose |
|------|---------|
| `GET  /`                     | Home page with Start button |
| `POST /api/start`            | Reset user state, stamp start time |
| `GET  /learn/<n>`            | Learning page N (1–5) |
| `POST /api/learn/<n>`        | Record enter-time + selection for lesson N |
| `GET  /quiz/<n>`             | Quiz question N (teammate stub) |
| `POST /api/quiz/<n>`         | Record quiz answer N (teammate stub) |
| `GET  /result`               | Quiz result page (teammate stub) |
| `GET  /api/state`            | Debug: dump current user state |

## Layout

```
app.py                Flask routes + state storage
data/content.json     All lesson + quiz content (edit here, not HTML)
data/user_state.json  Runtime snapshot of user actions (gitignored)
templates/            base, home, learn, quiz, result
static/css/           styles.css
static/js/            app.js   (record-and-advance helper)
static/media/         images
```

## Responsibilities (HW 10)

- **Learning portion + home page** — this skeleton
- **Quiz portion + result page** — teammate. See TODO comments in
  `templates/quiz.html` and `templates/result.html`, and the 5 pre-filled
  slots in `data/content.json -> quiz`.
