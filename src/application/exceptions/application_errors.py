class ApplicationError(Exception):
    """
    Lớp ngoại lệ cơ bản cho tầng Application.
    Tất cả các lỗi nghiệp vụ trong ứng dụng nên kế thừa từ lớp này.
    """
    pass