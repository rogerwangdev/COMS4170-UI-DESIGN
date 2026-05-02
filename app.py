"""Charcoal Grill Coach - Flask app.

Single-user app per the HW requirement. Lesson + quiz content lives in
data/content.json; user actions are recorded in-memory and snapshotted to
data/user_state.json after every write.
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


@app.before_request
def _reload_content_in_debug():
    """Re-read content.json on every request in debug mode so edits to
    lesson/quiz JSON show up without having to restart the server."""
    if not app.debug:
        return
    global CONTENT, LESSON_COUNT, QUIZ_COUNT
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


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Learning
# ---------------------------------------------------------------------------

@app.route("/learn/<int:lesson_id>")
def learn(lesson_id):
    if lesson_id < 1 or lesson_id > LESSON_COUNT:
        abort(404)
    lesson = CONTENT["lessons"][lesson_id - 1]
    prev_url = (
        url_for("learn", lesson_id=lesson_id - 1)
        if lesson_id > 1 else url_for("home")
    )
    if lesson_id < LESSON_COUNT:
        next_url = url_for("learn", lesson_id=lesson_id + 1)
        next_label = "Next →"
    else:
        # Final lesson routes through the transition page, not straight to quiz.
        next_url = url_for("transition")
        next_label = "Continue →"
    entry = user_state["lessons"].setdefault(str(lesson_id), {})
    entry.setdefault("first_seen_at", now_iso())
    entry["last_seen_at"] = now_iso()
    persist_state()

    # Lesson 1 is the editorial-style intro with alternating image/text rows.
    if lesson_id == 1:
        return render_template(
            "learn_charcoal_intro.html",
            lesson=lesson,
            lesson_id=lesson_id,
            lesson_count=LESSON_COUNT,
            prev_url=prev_url,
            next_url=next_url,
            next_label=next_label,
        )

    # Lesson 2 is the Types of Charcoal overview: hero image + 4 cards that
    # drill into per-type detail pages. Studied state is tracked per-type.
    if lesson_id == 2:
        studied = set(entry.get("studied", []))
        types = lesson.get("types_of_charcoal", [])
        return render_template(
            "learn_charcoal_overview.html",
            lesson=lesson,
            lesson_id=lesson_id,
            lesson_count=LESSON_COUNT,
            prev_url=prev_url,
            next_url=next_url,
            next_label=next_label,
            types=types,
            studied=studied,
            all_studied=len(studied) >= len(types) and len(types) > 0,
        )

    # Lesson 3 is the Grilling Techniques overview: hero image + 4 cards that
    # drill into per-technique detail pages. Studied state is tracked per-technique.
    if lesson_id == 3:
        studied = set(entry.get("studied", []))
        techniques = lesson.get("techniques", [])
        return render_template(
            "learn_techniques_overview.html",
            lesson=lesson,
            lesson_id=lesson_id,
            lesson_count=LESSON_COUNT,
            prev_url=prev_url,
            next_url=next_url,
            next_label=next_label,
            techniques=techniques,
            studied=studied,
            all_studied=len(studied) >= len(techniques) and len(techniques) > 0,
        )

    # Lesson 4 is the Safety & Disposal lesson: editorial-style intro like Lesson 1
    # with alternating image/text rows.
    if lesson_id == 4:
        return render_template(
            "learn_safety.html",
            lesson=lesson,
            lesson_id=lesson_id,
            lesson_count=LESSON_COUNT,
            prev_url=prev_url,
            next_url=next_url,
            next_label=next_label,
        )

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


# Per-charcoal detail pages (drilled into from the Types of Charcoal overview).

def _charcoal_by_slug(slug):
    for t in CONTENT["lessons"][1].get("types_of_charcoal", []):
        if t["slug"] == slug:
            return t
    return None


def _technique_by_slug(slug):
    for t in CONTENT["lessons"][2].get("techniques", []):
        if t["slug"] == slug:
            return t
    return None


@app.route("/learn/2/charcoal/<slug>")
def charcoal_detail(slug):
    charcoal = _charcoal_by_slug(slug)
    if charcoal is None:
        abort(404)
    types = CONTENT["lessons"][1].get("types_of_charcoal", [])
    entry = user_state["lessons"].setdefault("2", {})
    studied = set(entry.get("studied", []))
    # Mark studied as soon as the user lands on the detail page.
    if slug not in studied:
        studied.add(slug)
        entry["studied"] = sorted(studied)
        entry["last_action_at"] = now_iso()
        persist_state()
    idx = next(i for i, t in enumerate(types) if t["slug"] == slug)
    prev_slug = types[idx - 1]["slug"] if idx > 0 else None
    next_slug = types[idx + 1]["slug"] if idx + 1 < len(types) else None
    return render_template(
        "learn_charcoal_detail.html",
        lesson_id=2,
        lesson_count=LESSON_COUNT,
        charcoal=charcoal,
        position=idx + 1,
        total=len(types),
        overview_url=url_for("learn", lesson_id=2),
        prev_slug=prev_slug,
        next_slug=next_slug,
    )


@app.route("/learn/3/technique/<slug>")
def technique_detail(slug):
    technique = _technique_by_slug(slug)
    if technique is None:
        abort(404)
    techniques = CONTENT["lessons"][2].get("techniques", [])
    entry = user_state["lessons"].setdefault("3", {})
    studied = set(entry.get("studied", []))
    # Mark studied as soon as the user lands on the detail page.
    if slug not in studied:
        studied.add(slug)
        entry["studied"] = sorted(studied)
        entry["last_action_at"] = now_iso()
        persist_state()
    idx = next(i for i, t in enumerate(techniques) if t["slug"] == slug)
    prev_slug = techniques[idx - 1]["slug"] if idx > 0 else None
    next_slug = techniques[idx + 1]["slug"] if idx + 1 < len(techniques) else None
    return render_template(
        "learn_techniques_detail.html",
        lesson_id=3,
        lesson_count=LESSON_COUNT,
        technique=technique,
        position=idx + 1,
        total=len(techniques),
        overview_url=url_for("learn", lesson_id=3),
        prev_slug=prev_slug,
        next_slug=next_slug,
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
# Transition (learning -> quiz)
# ---------------------------------------------------------------------------

def _short_topic(q):
    """A 2-4 word scannable topic label built from the question/topic."""
    overrides = {
        1: "Longest-lasting",
        2: "Hottest burn",
        3: "Least ash",
        4: "Ribs layout",
        5: "Disposal bin",
    }
    return overrides.get(q["id"], q.get("topic", "").replace("-", " ").title())


@app.route("/transition")
def transition():
    """Confirmation screen between lesson 5 and quiz 1."""
    return render_template(
        "transition.html",
        lesson_count=LESSON_COUNT,
        quiz_count=QUIZ_COUNT,
    )


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------

@app.route("/quiz/<int:q_id>")
def quiz(q_id):
    if q_id < 1 or q_id > QUIZ_COUNT:
        abort(404)
    question = CONTENT["quiz"][q_id - 1]
    prev_url = (
        url_for("quiz", q_id=q_id - 1)
        if q_id > 1 else url_for("transition")
    )
    if q_id < QUIZ_COUNT:
        next_url = url_for("quiz", q_id=q_id + 1)
        next_label = "Next →"
    else:
        next_url = url_for("result")
        next_label = "See Results →"
    # Preserve user's prior selection so nav back/forward keeps the pill lit.
    prior_answer = user_state["quiz_answers"].get(str(q_id), {}).get("answer")
    if prior_answer is not None:
        prior_answer = int(prior_answer)
    return render_template(
        "quiz.html",
        question=question,
        q_id=q_id,
        quiz_count=QUIZ_COUNT,
        prev_url=prev_url,
        next_url=next_url,
        next_label=next_label,
        prior_answer=prior_answer,
        difficulty=question.get("difficulty", ""),
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


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

def _performance_copy(correct, total):
    """Headline + encouragement tailored to the score band."""
    if total == 0:
        return "", "No questions answered yet."
    pct = correct / total
    if pct >= 0.9:
        return (
            "Excellent",
            "Every fundamental locked in. You're ready to fire up the grill "
            "with confidence.",
        )
    if pct >= 0.8:
        return (
            "Nice work",
            "Charcoal type and technique are solid. A quick second pass on "
            "the question you missed will lock everything in.",
        )
    if pct >= 0.6:
        return (
            "Good start",
            "You've got the basics down. Revisit the lessons tied to the "
            "questions you missed and the rest will fall into place.",
        )
    if pct >= 0.4:
        return (
            "Keep going",
            "A handful clicked, a handful didn't. The lessons below go "
            "straight at the topics you stumbled on.",
        )
    return (
        "Worth another pass",
        "Skim the lessons again: each one is short and builds on the last. "
        "You'll see the pattern second time through.",
    )


@app.route("/result")
def result():
    correct = 0
    breakdown = []
    weak_topics = {}

    for q in CONTENT["quiz"]:
        chosen = user_state["quiz_answers"].get(str(q["id"]), {}).get("answer")
        is_correct = chosen is not None and int(chosen) == q["answer"]

        if is_correct:
            correct += 1
        else:
            topic = q.get("topic", "unknown")
            weak_topics[topic] = weak_topics.get(topic, 0) + 1

        chosen_label = None
        explanation = None
        if chosen is not None:
            chosen_i = int(chosen)
            if 0 <= chosen_i < len(q["options"]):
                chosen_label = q["options"][chosen_i]
            explanations = q.get("explanations", [])
            if 0 <= chosen_i < len(explanations):
                explanation = explanations[chosen_i]

        breakdown.append({
            "id": q["id"],
            "question": q["question"],
            "short_topic": _short_topic(q),
            "chosen_index": chosen,
            "chosen_label": chosen_label,
            "correct_label": q["options"][q["answer"]],
            "is_correct": is_correct,
            "explanation": explanation,
            "key_takeaway": q.get("key_takeaway", ""),
            "related_lesson_id": q.get("related_lesson_id"),
        })

    # Session timing
    total_session_time = None
    if user_state.get("start_time"):
        try:
            start = datetime.fromisoformat(
                user_state["start_time"].replace("Z", "+00:00")
            ).replace(tzinfo=None)
            total_session_time = (datetime.utcnow() - start).total_seconds()
        except (ValueError, TypeError):
            total_session_time = None

    # Recommendations (dedup by lesson_id, max 2, ordered by wrong-count desc)
    recommendations = []
    if weak_topics:
        sorted_topics = sorted(weak_topics.items(), key=lambda t: -t[1])
        seen = set()
        for topic, wrong_count in sorted_topics:
            for lesson in CONTENT["lessons"]:
                if lesson.get("topic") == topic and lesson["id"] not in seen:
                    pretty_topic = topic.replace("-", " ")
                    miss_word = "question" if wrong_count == 1 else "questions"
                    recommendations.append({
                        "lesson_id": lesson["id"],
                        "lesson_title": lesson["title"],
                        "reason": (
                            f"You missed {wrong_count} {miss_word} on "
                            f"{pretty_topic}."
                        ),
                    })
                    seen.add(lesson["id"])
                    break
            if len(recommendations) >= 2:
                break

    score_percentage = (correct / QUIZ_COUNT * 100) if QUIZ_COUNT > 0 else 0
    performance_headline, performance_message = _performance_copy(
        correct, QUIZ_COUNT
    )

    time_per_question = None
    if total_session_time and QUIZ_COUNT:
        time_per_question = round(total_session_time / QUIZ_COUNT, 1)

    return render_template(
        "result.html",
        correct=correct,
        total=QUIZ_COUNT,
        score_percentage=score_percentage,
        performance_headline=performance_headline,
        performance_message=performance_message,
        breakdown=breakdown,
        recommendations=recommendations,
        total_session_time=total_session_time,
        time_per_question=time_per_question,
        lessons_count=LESSON_COUNT,
    )


@app.route("/api/state")
def api_state():
    """Debug helper so the team can inspect what was recorded."""
    return jsonify(user_state)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
