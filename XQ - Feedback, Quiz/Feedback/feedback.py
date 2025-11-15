from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return "<h3>Đi tới /feedback để gửi phản hồi</h3>"

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        name = request.form.get("name")
        rating = request.form.get("rating")
        comments = request.form.get("comments")

        with open("feedback.txt", "a", encoding="utf-8") as f:
            f.write(f"{name} | {rating} | {comments}\n")

        return "<h3>Cảm ơn bạn đã phản hồi</h3><a href='/feedback'>Gửi thêm</a>"

    return render_template("feedback.html")

if __name__ == "__main__":
    app.run(debug=True)
