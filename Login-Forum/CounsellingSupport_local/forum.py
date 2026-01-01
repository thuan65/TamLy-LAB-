from flask import Blueprint, render_template, request, redirect, session
from toxic_filter import is_toxic
from db import get_db, get_all_forum_posts

forum = Blueprint("forum", __name__)

# Disable SBERT to avoid loading heavy model while debugging low-memory issues
model = None


def compute_similarity(query_text, posts, top_k=5):
    """Return empty results when the embedding model is disabled."""
    if model is None:
        return []
    return []


@forum.route("/forum")
def show_forum():
    conn = get_db()
    posts = conn.execute(
        "SELECT posts.*, users.username FROM posts JOIN users ON posts.user_id = users.id ORDER BY created_at DESC"
    ).fetchall()

    posts_with_answers = []
    for post in posts:
        answers = conn.execute(
            "SELECT answers.*, users.username AS expert_username FROM answers JOIN users ON answers.expert_id = users.id WHERE post_id=?",
            (post["id"],),
        ).fetchall()
        post_dict = dict(post)
        post_dict["answers"] = [dict(a) for a in answers]
        posts_with_answers.append(post_dict)

    return render_template("forum.html", posts=posts_with_answers)


@forum.route("/post/new", methods=["GET", "POST"])
def new_post():
    if "user_id" not in session or session.get("role") != "student":
        return "Chỉ student mới được tạo bài!", 403

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if is_toxic(content) or is_toxic(title):
            return render_template(
                "new_post.html",
                error="Nội dung câu hỏi/tiêu đề không phù hợp. Vui lòng viết lại.",
            )
        conn = get_db()
        conn.execute(
            "INSERT INTO posts(title, content, user_id) VALUES(?,?,?)",
            (title, content, session["user_id"]),
        )
        conn.commit()
        return redirect("/forum")

    return render_template("new_post.html")


@forum.route("/post/<int:post_id>/reply", methods=["GET", "POST"])
def reply_post(post_id):
    if "user_id" not in session or session.get("role") != "expert":
        return "Bạn không có quyền trả lời!", 403

    conn = get_db()
    post = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not post:
        return "Bài viết không tồn tại", 404

    if request.method == "POST":
        content = request.form["content"]
        conn.execute(
            "INSERT INTO answers(content, expert_id, post_id) VALUES(?,?,?)",
            (content, session["user_id"], post_id),
        )
        conn.execute(
            "UPDATE posts SET tag='answered' WHERE id=?",
            (post_id,),
        )
        conn.commit()
        return redirect("/forum")

    return render_template("reply_post.html", post=post)


@forum.route("/search_forum")
def search_forum():
    query = request.args.get("q", "").strip()
    if not query:
        return render_template("search_results.html", query=query, posts=[])

    posts = get_all_forum_posts()
    top_results = compute_similarity(query, posts)
    filtered_results = [p for p in top_results if not is_toxic(p["content"])]
    db = get_db()
    for post in filtered_results:
        answers = db.execute(
            "SELECT a.content, u.username as expert_username "
            "FROM answers a "
            "JOIN users u ON a.expert_id = u.id "
            "WHERE a.post_id=?",
            (post["id"],),
        ).fetchall()
        post["answers"] = [
            {"content": a["content"], "expert_username": a["expert_username"]}
            for a in answers
        ]

    return render_template("search_results.html", posts=filtered_results, query=query)
