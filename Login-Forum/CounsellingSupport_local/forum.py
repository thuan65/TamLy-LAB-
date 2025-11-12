from flask import Blueprint, render_template, request, redirect, session
from db import get_db

forum = Blueprint("forum", __name__)

@forum.route("/forum")
def show_forum():
    conn = get_db()
    # Lấy tất cả post kèm tên người đăng
    posts = conn.execute(
        "SELECT posts.*, users.username FROM posts JOIN users ON posts.user_id = users.id ORDER BY created_at DESC"
    ).fetchall()

    posts_with_answers = []
    for post in posts:
        # Lấy câu trả lời cho mỗi post
        answers = conn.execute(
            "SELECT answers.*, users.username AS expert_username FROM answers JOIN users ON answers.expert_id = users.id WHERE post_id=?",
            (post['id'],)
        ).fetchall()
        post_dict = dict(post)
        post_dict['answers'] = [dict(a) for a in answers]
        posts_with_answers.append(post_dict)

    return render_template("forum.html", posts=posts_with_answers)

@forum.route("/post/new", methods=["GET","POST"])
def new_post():
    if "user_id" not in session or session.get("role") != "student":
        return "Chỉ student mới được tạo bài!", 403

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        conn = get_db()
        conn.execute(
            "INSERT INTO posts(title, content, user_id) VALUES(?,?,?)",
            (title, content, session["user_id"])
        )
        conn.commit()
        return redirect("/forum")

    return render_template("new_post.html")

@forum.route("/post/<int:post_id>/reply", methods=["GET","POST"])
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
            (content, session["user_id"], post_id)
        )
        conn.execute(
            "UPDATE posts SET tag='answered' WHERE id=?",
            (post_id,)
        )
        conn.commit()
        return redirect("/forum")

    return render_template("reply_post.html", post=post)
