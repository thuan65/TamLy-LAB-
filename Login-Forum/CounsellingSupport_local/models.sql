-- Bảng người dùng (student hoặc expert)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'student', -- student hoặc expert
    -- NỘI DUng MỚI (TỪ BẠN)
    status_tag TEXT DEFAULT NULL,    -- Để lưu tag (ví dụ: 'cured_depression')
    chat_opt_in INTEGER DEFAULT 0    -- = 1 nếu người dùng 'cured' đồng ý chat
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

-- NỘI DUNG MỚI (TỪ BẠN)
-- BẢNG MỚI: Hàng đợi chat
CREATE TABLE IF NOT EXISTS chat_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,             -- ID của người đang chờ
    illness_type TEXT,           -- Loại bệnh họ muốn nói (ví dụ: 'depression')
    status TEXT DEFAULT 'waiting', -- 'waiting', 'matched', 'expired'
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- BẢNG MỚI: Phiên chat
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key TEXT UNIQUE,       -- Một chuỗi ngẫu nhiên (UUID) cho phòng chat
    seeker_id INTEGER,             -- ID người đi tìm (người bệnh)
    helper_id INTEGER,             -- ID người giúp (người hết bệnh HOẶC chuyên gia)
    status TEXT DEFAULT 'active', -- 'active', 'ended'
    is_expert_fallback INTEGER DEFAULT 0, -- = 1 nếu đây là chat với chuyên gia
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seeker_id) REFERENCES users(id),
    FOREIGN KEY (helper_id) REFERENCES users(id)
);

-- BẢNG MỚI: Cảnh báo AI (dùng sau)
CREATE TABLE IF NOT EXISTS chat_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    message_content TEXT,       -- Nội dung tin nhắn gây báo động
    status TEXT DEFAULT 'new',  -- 'new', 'acknowledged' (đã xem)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

-- BẢNG MỚI: Lịch sử hội thoại
CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_type TEXT NOT NULL,
    session_key TEXT NOT NULL,
    user_message TEXT,
    system_response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- NỘI DUNG MỚI (TỪ BẠN BẠN)
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