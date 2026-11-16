package authz

import rego.v1

default allow := false

# Helper to get user
user := data.users[input.subject] if {
    data.users[input.subject]
}

# Luật 1: Giảng viên sửa Syllabus nếu cùng khoa
allow if {
    input.resource.type == "syllabus"
    input.action == "edit"
    user.role == "giang_vien"
    syllabus := data.syllabi[input.resource.id]
    user.khoa == syllabus.khoa
}

# Luật 2: Giảng viên xem Syllabus nếu cùng khoa
allow if {
    input.resource.type == "syllabus"
    input.action == "view"
    user.role == "giang_vien"
    syllabus := data.syllabi[input.resource.id]
    user.khoa == syllabus.khoa
}

# Luật 3: Xem Course nếu là giảng viên phụ trách hoặc sinh viên đã ghi danh
allow if {
    input.resource.type == "course"
    input.action == "view"
    course := data.courses[input.resource.id]
    user_in_list(input.subject, course.enrolled)
}

allow if {
    input.resource.type == "course"
    input.action == "view"
    course := data.courses[input.resource.id]
    user_in_list(input.subject, course.instructors)
}

# Luật 4: Sửa Course nếu là giảng viên phụ trách
allow if {
    input.resource.type == "course"
    input.action == "edit"
    course := data.courses[input.resource.id]
    user_in_list(input.subject, course.instructors)
}

# Helper kiểm tra phần tử trong mảng
user_in_list(target, list) if {
    some item in list
    item == target
}
