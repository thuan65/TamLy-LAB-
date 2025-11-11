-- Bảng người dùng (student hoặc expert)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'student' -- student hoặc expert
);

-- Bảng bài đăng câu hỏi
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    user_id INTEGER,
    tag TEXT DEFAULT 'unanswered', -- trạng thái câu hỏi
    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Bảng câu trả lời
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    expert_id INTEGER,
    post_id INTEGER,
    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (expert_id) REFERENCES users(id),
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

-- Bảng lưu tin nhắn giữa user và expert
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    message TEXT,
    created_at DATETIME DEFAULT (datetime('now','localtime')),
    is_read INTEGER DEFAULT 0,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);
