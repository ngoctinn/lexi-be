from typing import List, Optional

from application.repositories.scenario_repository import ScenarioRepository
from domain.entities.scenario import Scenario


def _scenario(
    scenario_id: str,
    scenario_title: str,
    context: str,
    roles: list[str],
    goals: list[str],
    usage_count: int,
    is_active: bool = True,
) -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        scenario_title=scenario_title,
        context=context,
        roles=list(roles),
        goals=goals,
        is_active=is_active,
        usage_count=usage_count,
    )


class StaticScenarioRepository(ScenarioRepository):
    def __init__(self):
        self._scenarios: dict[str, Scenario] = {
            "s1": _scenario("s1", "Chào hỏi cơ bản", "Giao tiếp xã hội", ["Người mới", "Bạn mới quen"], ["Giới thiệu tên", "Hỏi thăm", "Tạm biệt lịch sự"], 210),
            "s1_2": _scenario("s1_2", "Gọi cà phê", "Tại quán cà phê", ["Khách hàng", "Barista"], ["Chọn đồ uống", "Chọn size", "Hỏi về giá"], 150),
            "s1_3": _scenario("s1_3", "Hỏi đường", "Đi lại & Hỏi đường", ["Du khách", "Người dân địa phương"], ["Hỏi vị trí", "Hỏi phương tiện", "Cảm ơn"], 95),
            "s1_4": _scenario("s1_4", "Tại hiệu thuốc", "Sức khỏe & Y tế", ["Bệnh nhân", "Dược sĩ"], ["Mô tả triệu chứng", "Hỏi liều dùng", "Thanh toán"], 40),
            "s1_5": _scenario("s1_5", "Check-in khách sạn", "Du lịch & Khách sạn", ["Khách du lịch", "Lễ tân"], ["Cung cấp thông tin đặt phòng", "Hỏi giờ ăn sáng", "Nhận phòng"], 120),
            "s1_6": _scenario("s1_6", "Mua vé xem phim", "Đời sống hàng ngày", ["Người xem", "Nhân viên quầy vé"], ["Chọn phim", "Chọn chỗ ngồi", "Thanh toán"], 80),
            "s1_7": _scenario("s1_7", "Đổi tiền ngoại tệ", "Tài chính & Ngân hàng", ["Khách hàng", "Giao dịch viên"], ["Hỏi tỷ giá", "Yêu cầu đổi tiền", "Xác nhận số tiền"], 30),
            "s2": _scenario("s2", "Mua sắm ở cửa hàng", "Mua sắm", ["Khách hàng", "Nhân viên bán hàng"], ["Hỏi giá sản phẩm", "Nhờ tư vấn kích cỡ", "Thanh toán lịch sự"], 45),
            "s3": _scenario("s3", "Đặt món ăn", "Ẩm thực & Nhà hàng", ["Thực khách", "Nhân viên phục vụ"], ["Gọi món từ menu", "Hỏi về nguyên liệu", "Thanh toán và tip"], 133),
            "s4": _scenario("s4", "Làm thủ tục sân bay", "Du lịch & Hàng không", ["Hành khách", "Nhân viên check-in"], ["Check-in chuyến bay", "Hỏi hành lý", "Trao đổi về cổng lên máy bay"], 89),
            "s5": _scenario("s5", "Phỏng vấn xin việc", "Công việc & Sự nghiệp", ["Ứng viên", "Nhà tuyển dụng"], ["Giới thiệu bản thân", "Nêu kinh nghiệm làm việc", "Trả lời câu hỏi tình huống"], 124),
            "s6": _scenario("s6", "Họp nhóm công việc", "Công sở & Hội họp", ["Thành viên nhóm", "Trưởng nhóm"], ["Báo cáo tiến độ", "Đề xuất ý kiến", "Phản hồi feedback lịch sự"], 77),
            "s7": _scenario("s7", "Thuyết trình sản phẩm", "Kinh doanh & Thuyết trình", ["Người thuyết trình", "Nhà đầu tư"], ["Trình bày vấn đề & giải pháp", "Demo tính năng chính", "Trả lời câu hỏi khó"], 55),
            "s8": _scenario("s8", "Thảo luận tin tức thời sự", "Xã hội & Thế giới", ["Người tham gia", "Chuyên gia bình luận"], ["Nêu quan điểm rõ ràng", "Phân tích vấn đề đa chiều", "Phản biện lịch sự"], 38),
        }

    def list_active(self) -> List[Scenario]:
        return [scenario for scenario in self._scenarios.values() if scenario.is_active]

    def list_all(self) -> List[Scenario]:
        return list(self._scenarios.values())

    def get_by_id(self, scenario_id: str) -> Optional[Scenario]:
        return self._scenarios.get(str(scenario_id))

    def save(self, scenario: Scenario) -> None:
        self._scenarios[str(scenario.scenario_id)] = scenario

    def create(self, scenario: Scenario) -> None:
        self._scenarios[str(scenario.scenario_id)] = scenario

    def update(self, scenario: Scenario) -> None:
        self._scenarios[str(scenario.scenario_id)] = scenario
