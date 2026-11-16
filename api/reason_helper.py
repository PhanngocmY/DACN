import json
import os
from typing import Dict, Any, Optional

class ReasonHelper:
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or os.getenv("DATA_JSON_PATH", "/app/data/data.json")
        self.data: Dict[str, Any] = {}
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {"users": {}, "syllabi": {}, "courses": {}}

    def evaluate_reason(self, subject: str, action: str, resource_type: str, resource_id: str, decision: str) -> str:
        """
        Sinh lý do quyết định chung chung, khách quan, không làm lộ PII của người khác (NFR-04).
        """
        if decision == "allow":
            return "Hợp lệ / Cho phép truy cập"

        # Quyết định từ chối (deny)
        users = self.data.get("users", {})
        syllabi = self.data.get("syllabi", {})
        courses = self.data.get("courses", {})

        # 1. Kiểm tra chủ thể tồn tại
        if subject not in users:
            return "Chủ thể không tồn tại trong hệ thống"

        user = users[subject]
        user_role = user.get("role", "")
        user_khoa = user.get("khoa", "")
        user_khoa_phu = user.get("khoa_phu", [])

        res_type_lower = resource_type.lower()

        # 2. Xử lý tài nguyên Syllabus (Đề cương)
        if res_type_lower == "syllabus":
            if user_role != "giang_vien":
                return "Chỉ giảng viên mới có quyền thao tác trên đề cương"
            syllabus = syllabi.get(resource_id)
            if syllabus:
                syl_khoa = syllabus.get("khoa", "")
                if user_khoa != syl_khoa:
                    if syl_khoa in user_khoa_phu:
                        return "Chỉ khoa chính mới có quyền chỉnh sửa đề cương (CT06)"
                    return "Khác Khoa quản lý"
            return "Không có quyền truy cập đề cương"

        # 3. Xử lý tài nguyên Course (Khóa học)
        if res_type_lower == "course":
            course = courses.get(resource_id)
            if not course:
                return "Khóa học không tồn tại"

            instructors = course.get("instructors", [])
            enrolled = course.get("enrolled", [])
            unenrolled = course.get("unenrolled", [])

            if action == "edit":
                if subject not in instructors:
                    return "Không thuộc danh sách giảng viên phụ trách khóa học"

            if action == "view":
                if subject in unenrolled:
                    return "Đã hủy ghi danh khóa học"
                if subject not in enrolled and subject not in instructors:
                    if user_role == "sinh_vien":
                        return "Chưa ghi danh vào khóa học"
                    if user_role == "giang_vien":
                        return "Không phụ trách khóa học này"
                    return "Không thuộc danh sách được xem khóa học"

        return "Yêu cầu bị từ chối theo chính sách mặc định (Default Deny)"
