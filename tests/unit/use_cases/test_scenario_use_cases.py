import pytest
from unittest.mock import Mock
from datetime import datetime, timezone

from application.use_cases.scenario_use_cases import ListScenariosUseCase
from domain.entities.scenario import Scenario


class TestListScenariosUseCase:
    """Test cases for ListScenariosUseCase."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_repo = Mock()
        self.use_case = ListScenariosUseCase(self.mock_repo)

    def test_execute_success_with_scenarios(self):
        """Test successful execution with scenarios."""
        # Arrange
        now = datetime.now(timezone.utc).isoformat()
        scenarios = [
            Scenario(
                scenario_id="test-1",
                scenario_title="Test Scenario 1",
                context="Test context 1",
                roles=["role1", "role2"],
                goals=["goal1", "goal2"],
                is_active=True,
                usage_count=5,
                difficulty_level="A2",
                order=1,
                created_at=now,
                updated_at=now,
            ),
            Scenario(
                scenario_id="test-2",
                scenario_title="Test Scenario 2",
                context="Test context 2",
                roles=["role3", "role4"],
                goals=["goal3", "goal4"],
                is_active=True,
                usage_count=3,
                difficulty_level="B1",
                order=2,
                created_at=now,
                updated_at=now,
            ),
        ]
        self.mock_repo.list_active.return_value = scenarios

        # Act
        result = self.use_case.execute()

        # Assert
        assert result.is_success
        data = result.value
        assert data["total"] == 2
        assert len(data["scenarios"]) == 2
        
        # Check first scenario
        scenario_1 = data["scenarios"][0]
        assert scenario_1["scenario_id"] == "test-1"
        assert scenario_1["scenario_title"] == "Test Scenario 1"
        assert scenario_1["context"] == "Test context 1"
        assert scenario_1["roles"] == ["role1", "role2"]
        assert scenario_1["goals"] == ["goal1", "goal2"]
        assert scenario_1["is_active"] is True
        assert scenario_1["usage_count"] == 5
        assert scenario_1["difficulty_level"] == "A2"
        assert scenario_1["order"] == 1
        
        # Verify repository was called
        self.mock_repo.list_active.assert_called_once()

    def test_execute_success_empty_list(self):
        """Test successful execution with empty scenario list."""
        # Arrange
        self.mock_repo.list_active.return_value = []

        # Act
        result = self.use_case.execute()

        # Assert
        assert result.is_success
        data = result.value
        assert data["total"] == 0
        assert data["scenarios"] == []
        self.mock_repo.list_active.assert_called_once()

    def test_execute_sorts_by_order(self):
        """Test that scenarios are sorted by order field."""
        # Arrange
        now = datetime.now(timezone.utc).isoformat()
        scenarios = [
            Scenario(
                scenario_id="test-3",
                scenario_title="Third",
                order=3,
                created_at=now,
                updated_at=now,
            ),
            Scenario(
                scenario_id="test-1",
                scenario_title="First",
                order=1,
                created_at=now,
                updated_at=now,
            ),
            Scenario(
                scenario_id="test-2",
                scenario_title="Second",
                order=2,
                created_at=now,
                updated_at=now,
            ),
        ]
        self.mock_repo.list_active.return_value = scenarios

        # Act
        result = self.use_case.execute()

        # Assert
        assert result.is_success
        data = result.value
        scenario_orders = [s["order"] for s in data["scenarios"]]
        assert scenario_orders == [1, 2, 3]

    def test_execute_handles_repository_exception(self):
        """Test handling of repository exceptions."""
        # Arrange
        self.mock_repo.list_active.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            self.use_case.execute()