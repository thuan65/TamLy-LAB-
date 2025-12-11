# ============================================================================
# FILE LOGIC TÍNH ĐIỂM VÀ KHUYẾN NGHỊ CHO PHQ-9
# ============================================================================

CAU_HOI = [
    "Ít hứng thú hoặc không thích thú khi làm các việc hàng ngày",
    "Cảm thấy buồn bã, chán nản hoặc tuyệt vọng",
    "Khó ngủ, ngủ nông hoặc ngủ quá nhiều",
    "Cảm thấy mệt mỏi hoặc thiếu năng lượng",
    "Kém ăn hoặc ăn quá nhiều",
    "Cảm thấy bản thân là kẻ thất bại hoặc làm phiền người khác",
    "Khó tập trung vào công việc hoặc việc học",
    "Cử động hoặc nói chậm lại; hoặc bồn chồn, không thể ngồi yên",
    "Nghĩ rằng thà mình chết đi hoặc muốn tự làm đau bản thân"
]

TAN_SUAT = [
    "Không bao giờ",           # 0 điểm
    "Vài ngày",                # 1 điểm
    "Hơn một nửa số ngày",     # 2 điểm
    "Gần như mỗi ngày"         # 3 điểm
]

ANH_HUONG = [
    "Không gây ảnh hưởng",
    "Có chút ảnh hưởng",
    "Hơi khó khăn",
    "Rất khó khăn"
]

def tinh_muc_do(diem):
    """
    Xác định mức độ dựa trên tổng điểm PHQ-9 (0-27)
    
    Args:
        diem (int): Tổng điểm từ 0-27
        
    Returns:
        tuple: (mô tả mức độ, loại bootstrap, icon)
    """
    if diem <= 4:
        return "Không/Ít triệu chứng", "success", "🟢"
    elif diem <= 9:
        return "Nhẹ", "info", "🟡"
    elif diem <= 14:
        return "Trung bình", "warning", "🟠"
    elif diem <= 19:
        return "Tương đối nặng", "danger", "🔴"
    else:
        return "Nặng", "danger", "🔴"

def tao_loi_khuyen(diem, muc_do):
    """
    Tạo danh sách lời khuyên và hành động dựa trên kết quả
    
    Args:
        diem (int): Tổng điểm từ 0-27
        muc_do (str): Mức độ triệu chứng
        
    Returns:
        tuple: (danh sách lời khuyên, danh sách hành động)
    """
    loi_khuyen = []
    hanh_dong = []
    
    if diem <= 4:
        # Không/Ít triệu chứng
        loi_khuyen = [
            "Tuyệt vời! Bạn đang có tâm trạng tốt và ổn định.",
            "Hãy duy trì lối sống tích cực và thói quen lành mạnh.",
            "Tiếp tục kết nối với bạn bè và gia đình."
        ]
        hanh_dong = [
            "Tiếp tục duy trì các hoạt động thư giãn như yoga, thiền định",
            "Tham gia các câu lạc bộ, hoạt động xã hội tại trường",
            "Chia sẻ kinh nghiệm tích cực với bạn bè",
            "Duy trì thói quen ngủ đủ giấc và ăn uống lành mạnh"
        ]
        
    elif diem <= 9:
        # Triệu chứng nhẹ
        loi_khuyen = [
            "Bạn có một số triệu chứng nhẹ về tâm trạng.",
            "Đây là lúc nên chú ý chăm sóc sức khỏe tinh thần nhiều hơn.",
            "Chia sẻ cảm xúc với người thân sẽ giúp bạn thoải mái hơn.",
            "Tìm hiểu thêm về các kỹ thuật tự chăm sóc."
        ]
        hanh_dong = [
            "Thử các kỹ thuật thư giãn: thiền, yoga, breathing exercises",
            "Xây dựng thói quen ngủ đều đặn (7-8 giờ/đêm)",
            "Viết nhật ký cảm xúc để theo dõi tâm trạng hàng ngày",
            "Tăng cường hoạt động thể chất nhẹ nhàng",
            "Tham khảo tài liệu tự chăm sóc sức khỏe tinh thần"
        ]
        
    elif diem <= 14:
        # Triệu chứng trung bình
        loi_khuyen = [
            "Bạn có triệu chứng ở mức trung bình - cần quan tâm.",
            "Nên cân nhắc tìm sự hỗ trợ từ chuyên gia tư vấn.",
            "Đừng ngần ngại, việc tìm kiếm hỗ trợ là dấu hiệu của sự mạnh mẽ.",
            "Hãy chia sẻ với người thân để được động viên và hỗ trợ."
        ]
        hanh_dong = [
            "Liên hệ tư vấn viên tâm lý tại trường hoặc trung tâm",
            "Tăng cường hoạt động thể chất (30 phút/ngày)",
            "Chú ý chế độ ăn uống cân bằng, hạn chế caffeine",
            "Tham gia nhóm hỗ trợ hoặc hoạt động cộng đồng",
            "Xem danh sách chuyên gia tư vấn trong hệ thống",
            "Theo dõi và ghi chép các triệu chứng hàng ngày"
        ]
        
    else:  # diem >= 15
        # Triệu chứng nặng
        loi_khuyen = [
            "Kết quả cho thấy bạn có triệu chứng nghiêm trọng.",
            "RẤT KHUYẾN NGHỊ tìm kiếm sự hỗ trợ chuyên môn NGAY.",
            "Bạn không đơn độc - có nhiều người sẵn sàng giúp đỡ bạn.",
            "Đừng chần chừ, hãy liên hệ với chuyên gia hoặc hotline hỗ trợ.",
            "Đây là tình huống cần can thiệp chuyên môn."
        ]
        hanh_dong = [
            "Liên hệ NGAY với chuyên gia tâm lý hoặc bác sĩ tâm thần",
            "Hotline hỗ trợ tâm lý 24/7: 1800-1010",
            "Chia sẻ với gia đình/người thân để được hỗ trợ NGAY",
            "Nếu có ý nghĩ tự hại, gọi cấp cứu: 115",
            "Xem danh sách chuyên gia có sẵn trong hệ thống",
            "Cân nhắc đến cơ sở y tế chuyên khoa tâm thần",
            "Không trì hoãn - hành động ngay hôm nay!"
        ]
    
    return loi_khuyen, hanh_dong

def phan_tich_chi_tiet(tra_loi):
    """
    Phân tích chi tiết các câu trả lời
    Đặc biệt cảnh báo nếu câu 9 (ý nghĩ tự hại) > 0
    
    Args:
        tra_loi (list): Danh sách 9 câu trả lời
        
    Returns:
        dict: Phân tích chi tiết và cảnh báo (nếu có)
    """
    phan_tich = {
        "tam_trang": tra_loi[0] + tra_loi[1],  # Câu 1, 2
        "giac_ngu": tra_loi[2],                # Câu 3
        "nang_luong": tra_loi[3],              # Câu 4
        "an_uong": tra_loi[4],                 # Câu 5
        "tu_danh_gia": tra_loi[5],            # Câu 6
        "tap_trung": tra_loi[6],               # Câu 7
        "van_dong": tra_loi[7],                # Câu 8
        "nguy_hiem": tra_loi[8]                # Câu 9: Ý nghĩ tự hại
    }
    
    # Cảnh báo đặc biệt nếu câu 9 > 0
    if phan_tich["nguy_hiem"] > 0:
        phan_tich["canh_bao"] = "CẢNH BÁO: Có dấu hiệu ý nghĩ tự hại. Cần hỗ trợ khẩn cấp!"
    
    return phan_tich