"""Tests for CloudWatch dashboard builder."""

import json
import pytest
from src.domain.services.cloudwatch_dashboard_builder import (
    CloudWatchDashboardBuilder,
)


class TestCloudWatchDashboardBuilder:
    """Test CloudWatch dashboard builder."""
    
    def test_build_latency_dashboard(self):
        """Test building latency dashboard."""
        dashboard = CloudWatchDashboardBuilder.build_latency_dashboard()
        
        assert "DashboardName" in dashboard
        assert dashboard["DashboardName"] == "latency-metrics"
        assert "DashboardBody" in dashboard
        
        body = json.loads(dashboard["DashboardBody"])
        assert "widgets" in body
        assert len(body["widgets"]) >= 4  # At least 4 widgets
        
        # Check widget types
        widget_types = [w["type"] for w in body["widgets"]]
        assert "metric" in widget_types
        assert "text" in widget_types
    
    def test_build_cost_dashboard(self):
        """Test building cost dashboard."""
        dashboard = CloudWatchDashboardBuilder.build_cost_dashboard()
        
        assert "DashboardName" in dashboard
        assert dashboard["DashboardName"] == "cost-metrics"
        assert "DashboardBody" in dashboard
        
        body = json.loads(dashboard["DashboardBody"])
        assert "widgets" in body
        assert len(body["widgets"]) >= 3
    
    def test_build_quality_dashboard(self):
        """Test building quality dashboard."""
        dashboard = CloudWatchDashboardBuilder.build_quality_dashboard()
        
        assert "DashboardName" in dashboard
        assert dashboard["DashboardName"] == "quality-metrics"
        assert "DashboardBody" in dashboard
        
        body = json.loads(dashboard["DashboardBody"])
        assert "widgets" in body
        assert len(body["widgets"]) >= 2
    
    def test_build_usage_dashboard(self):
        """Test building usage dashboard."""
        dashboard = CloudWatchDashboardBuilder.build_usage_dashboard()
        
        assert "DashboardName" in dashboard
        assert dashboard["DashboardName"] == "usage-metrics"
        assert "DashboardBody" in dashboard
        
        body = json.loads(dashboard["DashboardBody"])
        assert "widgets" in body
        assert len(body["widgets"]) >= 2
    
    def test_build_fallback_dashboard(self):
        """Test building fallback dashboard."""
        dashboard = CloudWatchDashboardBuilder.build_fallback_dashboard()
        
        assert "DashboardName" in dashboard
        assert dashboard["DashboardName"] == "fallback-rates"
        assert "DashboardBody" in dashboard
        
        body = json.loads(dashboard["DashboardBody"])
        assert "widgets" in body
        assert len(body["widgets"]) >= 2
    
    def test_dashboard_body_valid_json(self):
        """Test that all dashboard bodies are valid JSON."""
        dashboards = CloudWatchDashboardBuilder.get_all_dashboards()
        
        for name, dashboard in dashboards.items():
            body_str = dashboard["DashboardBody"]
            try:
                body = json.loads(body_str)
                assert "widgets" in body
            except json.JSONDecodeError:
                pytest.fail(f"Dashboard {name} has invalid JSON")
    
    def test_dashboard_widgets_have_required_fields(self):
        """Test that all widgets have required fields."""
        dashboards = CloudWatchDashboardBuilder.get_all_dashboards()
        
        for name, dashboard in dashboards.items():
            body = json.loads(dashboard["DashboardBody"])
            
            for i, widget in enumerate(body["widgets"]):
                assert "type" in widget, f"Widget {i} in {name} missing type"
                assert "x" in widget, f"Widget {i} in {name} missing x"
                assert "y" in widget, f"Widget {i} in {name} missing y"
                assert "width" in widget, f"Widget {i} in {name} missing width"
                assert "height" in widget, f"Widget {i} in {name} missing height"
                assert "properties" in widget, f"Widget {i} in {name} missing properties"
    
    def test_dashboard_widget_positioning(self):
        """Test that widgets are positioned correctly."""
        dashboard = CloudWatchDashboardBuilder.build_latency_dashboard()
        body = json.loads(dashboard["DashboardBody"])
        
        for i, widget in enumerate(body["widgets"]):
            # Check positioning
            assert widget["x"] in [0, 12], f"Widget {i} has invalid x position"
            assert widget["y"] >= 0, f"Widget {i} has invalid y position"
            assert widget["width"] == 12, f"Widget {i} has invalid width"
            assert widget["height"] == 6, f"Widget {i} has invalid height"
    
    def test_latency_dashboard_has_sla_info(self):
        """Test that latency dashboard includes SLA information."""
        dashboard = CloudWatchDashboardBuilder.build_latency_dashboard()
        body = json.loads(dashboard["DashboardBody"])
        
        # Find text widget with SLA info
        text_widgets = [w for w in body["widgets"] if w["type"] == "text"]
        assert len(text_widgets) > 0, "No text widget found"
        
        text_content = text_widgets[0]["properties"]["markdown"]
        assert "400" in text_content, "TTFT SLA not in text"
        assert "2000" in text_content, "Latency SLA not in text"
    
    def test_cost_dashboard_has_thresholds(self):
        """Test that cost dashboard includes cost thresholds."""
        dashboard = CloudWatchDashboardBuilder.build_cost_dashboard()
        body = json.loads(dashboard["DashboardBody"])
        
        # Find text widget with threshold info
        text_widgets = [w for w in body["widgets"] if w["type"] == "text"]
        assert len(text_widgets) > 0, "No text widget found"
        
        text_content = text_widgets[0]["properties"]["markdown"]
        assert "0.01" in text_content, "Warning threshold not in text"
        assert "0.02" in text_content, "Critical threshold not in text"
    
    def test_fallback_dashboard_has_target(self):
        """Test that fallback dashboard includes target rate."""
        dashboard = CloudWatchDashboardBuilder.build_fallback_dashboard()
        body = json.loads(dashboard["DashboardBody"])
        
        # Find text widget with target info
        text_widgets = [w for w in body["widgets"] if w["type"] == "text"]
        assert len(text_widgets) > 0, "No text widget found"
        
        text_content = text_widgets[0]["properties"]["markdown"]
        assert "15" in text_content, "Target fallback rate not in text"
    
    def test_get_all_dashboards(self):
        """Test getting all dashboards."""
        dashboards = CloudWatchDashboardBuilder.get_all_dashboards()
        
        assert "latency" in dashboards
        assert "cost" in dashboards
        assert "quality" in dashboards
        assert "usage" in dashboards
        assert "fallback" in dashboards
        
        # Verify each dashboard has required fields
        for name, dashboard in dashboards.items():
            assert "DashboardName" in dashboard
            assert "DashboardBody" in dashboard
    
    def test_dashboard_names_are_valid(self):
        """Test that dashboard names are valid."""
        dashboards = CloudWatchDashboardBuilder.get_all_dashboards()
        
        for name, dashboard in dashboards.items():
            dashboard_name = dashboard["DashboardName"]
            # CloudWatch dashboard names must be lowercase with hyphens
            assert dashboard_name.islower() or "-" in dashboard_name
            assert " " not in dashboard_name
    
    def test_metric_widgets_have_metrics(self):
        """Test that metric widgets have metrics defined."""
        dashboard = CloudWatchDashboardBuilder.build_latency_dashboard()
        body = json.loads(dashboard["DashboardBody"])
        
        metric_widgets = [w for w in body["widgets"] if w["type"] == "metric"]
        assert len(metric_widgets) > 0, "No metric widgets found"
        
        for widget in metric_widgets:
            props = widget["properties"]
            assert "metrics" in props, "Metric widget missing metrics"
            assert len(props["metrics"]) > 0, "Metric widget has no metrics"
    
    def test_metric_widgets_have_region(self):
        """Test that metric widgets have region specified."""
        dashboard = CloudWatchDashboardBuilder.build_cost_dashboard()
        body = json.loads(dashboard["DashboardBody"])
        
        metric_widgets = [w for w in body["widgets"] if w["type"] == "metric"]
        
        for widget in metric_widgets:
            props = widget["properties"]
            assert "region" in props, "Metric widget missing region"
            assert props["region"] == "us-east-1"
    
    def test_text_widgets_have_markdown(self):
        """Test that text widgets have markdown content."""
        dashboard = CloudWatchDashboardBuilder.build_quality_dashboard()
        body = json.loads(dashboard["DashboardBody"])
        
        text_widgets = [w for w in body["widgets"] if w["type"] == "text"]
        
        for widget in text_widgets:
            props = widget["properties"]
            assert "markdown" in props, "Text widget missing markdown"
            assert len(props["markdown"]) > 0, "Text widget has empty markdown"
    
    def test_dashboard_namespace_is_correct(self):
        """Test that dashboards use correct namespace."""
        dashboard = CloudWatchDashboardBuilder.build_latency_dashboard()
        body = json.loads(dashboard["DashboardBody"])
        
        metric_widgets = [w for w in body["widgets"] if w["type"] == "metric"]
        
        for widget in metric_widgets:
            props = widget["properties"]
            for metric in props["metrics"]:
                # Metric format: [namespace, metric_name, ...]
                assert metric[0] == "Lexi/ConversationQuality"
    
    def test_sla_constants_are_reasonable(self):
        """Test that SLA constants are reasonable."""
        assert CloudWatchDashboardBuilder.TTFT_SLA_MS == 400
        assert CloudWatchDashboardBuilder.LATENCY_SLA_MS == 2000
        assert CloudWatchDashboardBuilder.COST_WARNING_USD == 0.01
        assert CloudWatchDashboardBuilder.COST_CRITICAL_USD == 0.02
        assert CloudWatchDashboardBuilder.FALLBACK_TARGET_PERCENT == 15
    
    def test_dashboard_body_is_string(self):
        """Test that dashboard body is a JSON string."""
        dashboards = CloudWatchDashboardBuilder.get_all_dashboards()
        
        for name, dashboard in dashboards.items():
            assert isinstance(dashboard["DashboardBody"], str)
            # Should be valid JSON
            json.loads(dashboard["DashboardBody"])
