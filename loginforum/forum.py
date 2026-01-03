from flask import Blueprint, render_template, request, redirect, session, url_for
from sentence_transformers import SentenceTransformer, util
from .toxic_filter import is_toxic
from .db import get_db, get_all_forum_posts

forum = Blueprint("forum", __name__, url_prefix="/forum", template_folder="htmltemplates")

model = SentenceTransformer("keepitreal/vietnamese-sbert")

def compute_similarity(query_text, posts, top_k=5):
    """So sánh độ tương đồng giữa query và posts trong DB"""
    query_embedding = model.encode(query_text, convert_to_tensor=True)

    scored = []
    for post in posts:
        # combine title + content
        post_text = f"{post['title']} {post['content']}"
        post_embedding = model.encode(post_text, convert_to_tensor=True)
        similarity = util.cos_sim(query_embedding, post_embedding).item()
        scored.append((similarity, post))

    # Sắp xếp giảm dần
    scored.sort(reverse=True, key=lambda x: x[0])

    # Trả về top_k
    results = [dict(x[1]) for x in scored[:top_k]]
    # Nếu muốn, có thể thêm score vào dict
    for i, r in enumerate(results):
        r["score"] = float(scored[i][0])
    return results

@forum.route("/")
def show_forum():
    if "user_id" not in session:
        return redirect(url_for("auth.login", next=request.full_path))

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

        if is_toxic(content) or is_toxic(title):
            return render_template("new_post.html", error="Nội dung câu hỏi/tiêu đề không phù hợp. Vui lòng viết lại.")
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

# @forum.route("/search_forum", methods=["GET"])
# def search_forum():
#     query = request.args.get("q", "").strip()
#     if not query:
#         return render_template("search_results.html", posts=[], query=query)

#     posts = get_all_forum_posts()

#     top_results = compute_similarity(query, posts)

#     filtered_results = [p for p in top_results if not is_toxic(p["content"])]

#     return render_template("search_results.html", posts=filtered_results, query=query)

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
            (post["id"],)
        ).fetchall()
        post["answers"] = [{"content": a["content"], "expert_username": a["expert_username"]} for a in answers]

    return render_template("search_results.html", posts=filtered_results, query=query)

# print(is_toxic("fuck"))   # phải trả về True
# print(is_toxic("you are stupid"))  # True
# print(is_toxic("hello world"))  # False
# print(is_toxic("đụ"))  # True
# print(is_toxic("bạn thật ngu ngốc"))  # True
# print(is_toxic("chào bạn"))  # False
# print(is_toxic("đm"))  # True
# print(is_toxic("bạn là đồ khốn nạn"))  # True
# print(is_toxic("vl"))  # True
