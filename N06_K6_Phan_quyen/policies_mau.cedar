// Chính sách mẫu khởi đầu — nhóm hoàn thiện và kiểm thử với cases.yaml
permit (principal, action == Action::"edit", resource is Syllabus)
when { principal.role == "giang_vien" && principal.khoa == resource.khoa };
permit (principal, action == Action::"view", resource is Syllabus)
when { principal.role == "giang_vien" && principal.khoa == resource.khoa };
permit (principal, action == Action::"view", resource is Course)
when { resource.enrolled.contains(principal) || resource.instructors.contains(principal) };
permit (principal, action == Action::"edit", resource is Course)
when { resource.instructors.contains(principal) };
