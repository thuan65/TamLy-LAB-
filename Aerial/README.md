# 🧠 Aerial – Mental Health Assistant

Ứng dụng Aerial giúp người dùng quản lý và cải thiện sức khỏe tâm lý bằng cách kết hợp các mô-đun Python độc lập với Flask API và AI (Gemini).

## 📁 Chi tiết từng file

### 1️⃣ `database_fetcher.py`
**Chức năng:**  
Thu thập thông tin về các phòng khám và chuyên gia tâm lý thông qua SerpAPI (Google Maps).

**Sử dụng:**  
```bash
python database_fetcher.py --cities "Hà Nội" "Đà Nẵng" "TP.HCM"
```
Tạo thư mục `database/` chứa file JSON dữ liệu:
```
database/
 ├── Hanoi_therapists.json
 ├── Danang_therapists.json
 └── HoChiMinh_therapists.json
```

---

### 2️⃣ `therapists_recommender.py`
**Chức năng:**  
Phân tích nhu cầu người dùng và đề xuất chuyên gia phù hợp.

**Các bước:**  
1. Phân tích ngôn ngữ tự nhiên tiếng Việt → trích xuất nhu cầu & vị trí.  
2. Xác định khu vực (HUB_HANOI, HUB_DN, HUB_HCMC).  
3. Đọc dữ liệu từ JSON tương ứng và tính điểm gợi ý.  
4. Trả kết quả JSON hoặc Markdown (tùy endpoint).

**Chạy thử:**  
```bash
python therapists_recommender.py "Tôi ở Đà Nẵng, cảm thấy căng thẳng"
```

---

### 3️⃣ `health_helper.py`
**Chức năng:**  
Hỗ trợ hoặc kiểm thử API phụ (có thể bỏ nếu `GUI.py` đã thay thế hoàn toàn).

---

### 4️⃣ `GUI.py`
**Chức năng:**  
Server Flask chính — kết nối mọi thành phần với giao diện web.

**Endpoint chính:**  
| Endpoint | Mô tả | Đầu ra |
|-----------|--------|--------|
| `/api/stress_text` | Gợi ý giảm căng thẳng | Markdown tiếng Việt |
| `/api/plan_text` | Kế hoạch cải thiện sức khỏe | Markdown |
| `/api/recommend_text` | Đề xuất chuyên gia | Markdown tự nhiên |
| `/api/recommend` | (cũ) Gợi ý chuyên gia dạng JSON | JSON |

**Chạy:**  
```bash
python GUI.py
```
Mở [http://localhost:8000](http://localhost:8000)

---

### 5️⃣ `templates/GUI_new.html`
**Chức năng:**  
Giao diện web dạng chat (giống ChatGPT).  
- Nhấn **Enter** để gửi, **Shift+Enter** để xuống dòng.  
- Có hiệu ứng **“Đang soạn…”** khi AI phản hồi.  
- Dấu “+” mở menu chọn chế độ.  
- Hiển thị Markdown đẹp (tích hợp `marked.js`).  

---

## ⚙️ Cấu hình `.env`
Tạo file `.env` cùng thư mục `GUI.py`:
```
SERPAPI_API_KEY=your_serpapi_key_here
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash
THROTTLE_SECONDS=0.5
```

---

## 🧩 Luồng xử lý
```
Người dùng nhập văn bản
   ↓
GUI.py (Flask) xác định mode
   ↓
  ├── stress_text → Gemini sinh tư vấn giảm stress
  ├── plan_text → Gemini tạo kế hoạch chăm sóc
  └── recommend_text → therapists_recommender.py + database_fetcher.py
                            ↓
                        SerpAPI (Google Maps)
                            ↓
                    Trả kết quả Markdown tiếng Việt
```

---

## 📄 Ghi chú
- Tất cả kết quả đều hiển thị **tiếng Việt tự nhiên**.  
- Khi vượt quota Gemini (`429`), hệ thống tự retry và fallback model nhanh hơn.  
- Hệ thống phân chia vùng miền theo 3 hub: Bắc (HN), Trung (ĐN), Nam (HCM).  
- Có thể mở rộng database cho nhiều tỉnh thành khác.
