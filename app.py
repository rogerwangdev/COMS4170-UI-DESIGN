"""Charcoal Grill Coach — HW 10 technical prototype.

Single-user Flask app (per HW requirement #8). All lesson and quiz content
lives in data/content.json; user actions are recorded in-memory and snapshotted
to data/user_state.json after every write.
"""
import json
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, abort, jsonify, redirect, render_template, request, url_for
)

BASE_DIR = Path(__file__).parent
CONTENT_PATH = BASE_DIR / "data" / "content.json"
STATE_PATH = BASE_DIR / "data" / "user_state.json"

app = Flask(__name__)


def load_content():
    with open(CONTENT_PATH, encoding="utf-8") as f:
        return json.load(f)


CONTENT = load_content()
LESSON_COUNT = len(CONTENT["lessons"])
QUIZ_COUNT = len(CONTENT["quiz"])

user_state = {
    "start_time": None,
    "lessons": {},
    "quiz_answers": {},
}


def persist_state():
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(user_state, f, indent=2)


def now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


@app.route("/")
def home():
    return render_template("home.html")


@app.post("/api/start")
def api_start():
    user_state["start_time"] = now_iso()
    user_state["lessons"] = {}
    user_state["quiz_answers"] = {}
    persist_state()
    return jsonify(ok=True, redirect=url_for("learn", lesson_id=1))


@app.route("/learn/<int:lesson_id>")
def learn(lesson_id):
    if lesson_id < 1 or lesson_id > LESSON_COUNT:
        abort(404)
    lesson = CONTENT["lessons"][lesson_id - 1]
    prev_url = url_for("learn", lesson_id=lesson_id - 1) if lesson_id > 1 else url_for("home")
    if lesson_id < LESSON_COUNT:
        next_url = url_for("learn", lesson_id=lesson_id + 1)
        next_label = "Next \u2192"
    else:
        next_url = url_for("quiz", q_id=1)
        next_label = "Start Quiz \u2192"
    entry = user_state["lessons"].setdefault(str(lesson_id), {})
    entry.setdefault("first_seen_at", now_iso())
    entry["last_seen_at"] = now_iso()
    persist_state()
    return render_template(
        "learn.html",
        lesson=lesson,
        lesson_id=lesson_id,
        lesson_count=LESSON_COUNT,
        prev_url=prev_url,
        next_url=next_url,
        next_label=next_label,
        prior_selection=entry.get("selection"),
    )


@app.post("/api/learn/<int:lesson_id>")
def api_learn(lesson_id):
    if lesson_id < 1 or lesson_id > LESSON_COUNT:
        abort(404)
    payload = request.get_json(silent=True) or {}
    entry = user_state["lessons"].setdefault(str(lesson_id), {})
    entry["last_action_at"] = now_iso()
    if "selection" in payload:
        entry["selection"] = payload["selection"]
    persist_state()
    return jsonify(ok=True, state=entry)


# ---------------------------------------------------------------------------
# Quiz + Result routes  —  teammate fills these in.
# The scaffolding (routes, data loading, state storage) is already wired.
# ---------------------------------------------------------------------------

@app.route("/quiz/<int:q_id>")
def quiz(q_id):
    if q_id < 1 or q_id > QUIZ_COUNT:
        abort(404)
    question = CONTENT["quiz"][q_id - 1]
    prev_url = url_for("quiz", q_id=q_id - 1) if q_id > 1 else url_for("learn", lesson_id=LESSON_COUNT)
    if q_id < QUIZ_COUNT:
        next_url = url_for("quiz", q_id=q_id + 1)
        next_label = "Next \u2192"
    else:
        next_url = url_for("result")
        next_label = "See Results \u2192"
    prior_answer = user_state["quiz_answers"].get(str(q_id), {}).get("answer")
    return render_template(
        "quiz.html",
        question=question,
        q_id=q_id,
        quiz_count=QUIZ_COUNT,
        prev_url=prev_url,
        next_url=next_url,
        next_label=next_label,
        prior_answer=prior_answer,
    )


@app.post("/api/quiz/<int:q_id>")
def api_quiz(q_id):
    if q_id < 1 or q_id > QUIZ_COUNT:
        abort(404)
    payload = request.get_json(silent=True) or {}
    user_state["quiz_answers"][str(q_id)] = {
        "answer": payload.get("answer"),
        "answered_at": now_iso(),
    }
    persist_state()
    return jsonify(ok=True)


@app.route("/result")
def result():
    correct = 0
    breakdown = []
    for q in CONTENT["quiz"]:
        chosen = user_state["quiz_answers"].get(str(q["id"]), {}).get("answer")
        is_correct = chosen is not None and int(chosen) == q["answer"]
        if is_correct:
            correct += 1
        breakdown.append({
            "id": q["id"],
            "question": q["question"],
            "chosen_index": chosen,
            "chosen_label": q["options"][int(chosen)] if chosen is not None else None,
            "correct_label": q["options"][q["answer"]],
            "is_correct": is_correct,
        })
    return render_template(
        "result.html",
        correct=correct,
        total=QUIZ_COUNT,
        breakdown=breakdown,
    )


@app.route("/api/state")
def api_state():
    """Debug helper so the team can inspect what was recorded."""
    return jsonify(user_state)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
