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
    "Không bao giờ",
    "Vài ngày",
    "Hơn một nửa số ngày",
    "Gần như mỗi ngày"
]

ANH_HUONG = [
    "Không gây ảnh hưởng",
    "Có chút ảnh hưởng",
    "Hơi khó khăn",
    "Rất khó khăn"
]

def tinh_muc_do(diem):
    if diem <= 4:
        return "Không/Ít triệu chứng", "success"
    elif diem <= 9:
        return "Nhẹ", "info"
    elif diem <= 14:
        return "Trung bình", "warning"
    elif diem <= 19:
        return "Tương đối nặng", "danger"
    else:
        return "Nặng", "danger"


def tao_loi_khuyen(diem, muc_do):
    loi_khuyen = []

    if diem <= 4:
        loi_khuyen = [
            "Bạn đang có tâm trạng tốt! Hãy duy trì lối sống tích cực.",
            "Tiếp tục tập thể dục đều đặn và giữ kết nối bạn bè."
        ]
    elif diem <= 9:
        loi_khuyen = [
            "Bạn có triệu chứng nhẹ, hãy chú ý đến tâm trạng.",
            "Thử thiền, yoga, hoặc viết journal."
        ]
    elif diem <= 14:
        loi_khuyen = [
            "Mức độ trung bình, nên tìm tư vấn tâm lý.",
            "Duy trì thói quen sống lành mạnh."
        ]
    else:
        loi_khuyen = [
            "Triệu chứng nặng, vui lòng tìm chuyên gia ngay.",
            "Bạn không một mình — hãy nhờ hỗ trợ từ người tin tưởng."
        ]

    return loi_khuyen
