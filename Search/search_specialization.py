from flask import Blueprint, request, jsonify, current_app
from sentence_transformers import util, SentenceTransformer
from models import ExpertProfile, User
from database import TherapySession
import torch

sbert_model  = SentenceTransformer("keepitreal/vietnamese-sbert")

search_specialization_bp = Blueprint("search_specialization", __name__)

def to_dict(expert, user):
    """Chuyển đổi object sang dict để trả về JSON"""
    return {
        "user_id": expert.user_id,
        "full_name": expert.full_name,
        "title": expert.title,
        "qualification": expert.qualification,
        "specialization": expert.specialization,
        "years_of_experience": expert.years_of_experience,
        "bio": expert.bio,
        "is_online": user.is_online
    }

@search_specialization_bp.route("/api/search_specialization", methods=["GET"])
def search_experts():
    user_query = request.args.get("query", "").strip()
    
    if not user_query:
        return jsonify({"message": "Vui lòng nhập từ khóa."}), 400
    
    session = TherapySession()

    try:
        # 1. Lấy tất cả chuyên gia đang hoạt động
        experts_data = (
            session.query(ExpertProfile, User)
            .join(User, ExpertProfile.user_id == User.id)
            .filter(
                User.role == "EXPERT",                
                ExpertProfile.verification_status == "VERIFIED"  
            )
            .all()
        )

        
        if not experts_data:
            return jsonify([])

        # 2. Chuẩn bị dữ liệu để so khớp ngữ nghĩa
        # Chúng ta sẽ embed cột 'specialization' kết hợp với 'bio' để có kết quả chính xác hơn
        expert_texts = []
        for exp, user in experts_data:
            # Kết hợp các trường văn bản để máy hiểu ngữ cảnh tốt hơn
            combined_text = f"{exp.specialization} {exp.bio if exp.bio else ''}"
            expert_texts.append(combined_text)

        # 3. Tính toán Embedding
        query_embedding = sbert_model.encode(user_query, convert_to_tensor=True)
        expert_embeddings = sbert_model.encode(expert_texts, convert_to_tensor=True)

        # 4. Tính toán độ tương đồng Cosine
        cosine_scores = util.cos_sim(query_embedding, expert_embeddings)[0]

        # 5. Lọc và sắp xếp kết quả
        results = []
        threshold = 0.1  # Ngưỡng tương đồng tối thiểu
        
        for i, score in enumerate(cosine_scores):
            if score.item() >= threshold:
                expert, user = experts_data[i]
                data = to_dict(expert, user)
                data['score'] = float(score.item())
                results.append(data)

        # Sắp xếp theo điểm số từ cao xuống thấp
        results.sort(key=lambda x: x['score'], reverse=True)

        return jsonify(results)

    except Exception as e:
        print(f"Lỗi Semantic Search: {e}")
        return jsonify({"error": "Đã xảy ra lỗi hệ thống"}), 500
    finally:
        session.close()