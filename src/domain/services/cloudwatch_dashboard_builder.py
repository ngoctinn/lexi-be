"""CloudWatch dashboard builder for metrics visualization."""

import json
from dataclasses import dataclass
from typing import Optional

from shared.http_utils import dumps


@dataclass
class DashboardWidget:
    """Represents a CloudWatch dashboard widget."""
    
    type: str  # "metric", "number", "gauge", "text", "alarm"
    title: str
    properties: dict


class CloudWatchDashboardBuilder:
    """Builds CloudWatch dashboards for metrics visualization."""
    
    NAMESPACE = "Lexi/ConversationQuality"
    
    # SLA thresholds
    TTFT_SLA_MS = 400  # 95th percentile
    LATENCY_SLA_MS = 2000  # 95th percentile
    COST_WARNING_USD = 0.01  # per turn
    COST_CRITICAL_USD = 0.02  # per turn
    FALLBACK_TARGET_PERCENT = 15  # target fallback rate
    
    @staticmethod
    def build_latency_dashboard() -> dict:
        """
        Build latency metrics dashboard.
        
        Displays:
        - TTFT by level (line graph)
        - Total latency by level (line graph)
        - TTFT by model source (primary vs fallback)
        - Total latency by model source
        - SLA compliance (number widgets)
        
        Returns:
            Dashboard JSON
        """
        widgets = []
        
        # TTFT by level
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "TTFT", {"stat": "Average"}],
                ],
                "period": 60,
                "stat": "Average",
                "region": "us-east-1",
                "title": "TTFT by Level (Average)",
                "yAxis": {"left": {"min": 0, "max": 500}},
            }
        })
        
        # Total latency by level
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "TotalLatency", {"stat": "Average"}],
                ],
                "period": 60,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Total Latency by Level (Average)",
                "yAxis": {"left": {"min": 0, "max": 3000}},
            }
        })
        
        # TTFT by model source
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "TTFT", {"stat": "p95"}],
                ],
                "period": 300,
                "stat": "p95",
                "region": "us-east-1",
                "title": "TTFT 95th Percentile (Primary vs Fallback)",
            }
        })
        
        # Total latency 95th percentile
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "TotalLatency", {"stat": "p95"}],
                ],
                "period": 300,
                "stat": "p95",
                "region": "us-east-1",
                "title": "Total Latency 95th Percentile",
                "yAxis": {"left": {"min": 0, "max": 3000}},
            }
        })
        
        # SLA compliance text
        widgets.append({
            "type": "text",
            "properties": {
                "markdown": f"""
# Latency SLA

- **TTFT Target**: < {CloudWatchDashboardBuilder.TTFT_SLA_MS}ms (95th percentile)
- **Total Latency Target**: < {CloudWatchDashboardBuilder.LATENCY_SLA_MS}ms (95th percentile)
- **Streaming Success Rate**: > 98%

Monitor these metrics to ensure SLA compliance.
                """
            }
        })
        
        return CloudWatchDashboardBuilder._build_dashboard(
            "Latency Metrics",
            widgets
        )
    
    @staticmethod
    def build_cost_dashboard() -> dict:
        """
        Build cost metrics dashboard.
        
        Displays:
        - Cost per turn by level (line graph)
        - Cost per session by level (line graph)
        - Blended cost across all levels (number widget)
        - Cost savings vs Haiku (number widget)
        - Cost alerts (alarm widget)
        
        Returns:
            Dashboard JSON
        """
        widgets = []
        
        # Cost per turn by level
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "CostPerTurn", {"stat": "Average"}],
                ],
                "period": 60,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Cost per Turn by Level (Average)",
                "yAxis": {"left": {"min": 0}},
            }
        })
        
        # Cost per turn max
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "CostPerTurn", {"stat": "Maximum"}],
                ],
                "period": 300,
                "stat": "Maximum",
                "region": "us-east-1",
                "title": "Cost per Turn (Maximum)",
                "yAxis": {"left": {"min": 0}},
            }
        })
        
        # Cost warning threshold
        widgets.append({
            "type": "text",
            "properties": {
                "markdown": f"""
# Cost Thresholds

- **Warning**: ${CloudWatchDashboardBuilder.COST_WARNING_USD:.4f} per turn
- **Critical**: ${CloudWatchDashboardBuilder.COST_CRITICAL_USD:.4f} per turn

Monitor cost metrics to prevent budget overruns.
                """
            }
        })
        
        # Cost by model
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "CostPerTurn", {"stat": "Sum"}],
                ],
                "period": 3600,
                "stat": "Sum",
                "region": "us-east-1",
                "title": "Total Cost by Model (Hourly)",
            }
        })
        
        return CloudWatchDashboardBuilder._build_dashboard(
            "Cost Metrics",
            widgets
        )
    
    @staticmethod
    def build_quality_dashboard() -> dict:
        """
        Build quality metrics dashboard.
        
        Displays:
        - Response length compliance (number widget)
        - Format compliance (number widget)
        - Delivery cue presence (number widget)
        - Overall quality score (gauge widget)
        - Quality trends (line graph)
        
        Returns:
            Dashboard JSON
        """
        widgets = []
        
        # Quality compliance text
        widgets.append({
            "type": "text",
            "properties": {
                "markdown": """
# Quality Metrics

- **Length Compliance**: Response within token limits
- **Format Compliance**: No markdown, one question
- **Delivery Cues**: Present in response
- **Overall Score**: Weighted average of all metrics

Target: > 95% compliance, > 80 overall score
                """
            }
        })
        
        # Placeholder for quality metrics (would need custom metric)
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "OutputTokens", {"stat": "Average"}],
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Response Length (Output Tokens)",
            }
        })
        
        return CloudWatchDashboardBuilder._build_dashboard(
            "Quality Metrics",
            widgets
        )
    
    @staticmethod
    def build_usage_dashboard() -> dict:
        """
        Build usage metrics dashboard.
        
        Displays:
        - Sessions per hour (line graph)
        - Turns per session (number widget)
        - Models used (pie chart)
        - Proficiency level distribution (bar chart)
        
        Returns:
            Dashboard JSON
        """
        widgets = []
        
        # Output tokens (proxy for usage)
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "OutputTokens", {"stat": "Sum"}],
                ],
                "period": 3600,
                "stat": "Sum",
                "region": "us-east-1",
                "title": "Total Output Tokens (Hourly)",
            }
        })
        
        # Output tokens by model
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "OutputTokens", {"stat": "Average"}],
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Average Output Tokens by Model",
            }
        })
        
        # Usage info
        widgets.append({
            "type": "text",
            "properties": {
                "markdown": """
# Usage Metrics

- **Sessions**: Number of active sessions
- **Turns**: Average turns per session
- **Models**: Distribution of models used
- **Levels**: Distribution of proficiency levels

Monitor usage to understand learner engagement.
                """
            }
        })
        
        return CloudWatchDashboardBuilder._build_dashboard(
            "Usage Metrics",
            widgets
        )
    
    @staticmethod
    def build_fallback_dashboard() -> dict:
        """
        Build fallback rate dashboard.
        
        Displays:
        - Fallback rate by level (line graph)
        - Fallback reasons (bar chart)
        - Fallback count by level (number widgets)
        - Target vs actual (comparison)
        
        Returns:
            Dashboard JSON
        """
        widgets = []
        
        # Fallback count
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "FallbackCount", {"stat": "Sum"}],
                ],
                "period": 3600,
                "stat": "Sum",
                "region": "us-east-1",
                "title": "Fallback Count (Hourly)",
            }
        })
        
        # Fallback target
        widgets.append({
            "type": "text",
            "properties": {
                "markdown": f"""
# Fallback Rate Target

- **Target**: {CloudWatchDashboardBuilder.FALLBACK_TARGET_PERCENT}% fallback rate
- **Tolerance**: ±10% (acceptable range: {CloudWatchDashboardBuilder.FALLBACK_TARGET_PERCENT - 10}% - {CloudWatchDashboardBuilder.FALLBACK_TARGET_PERCENT + 10}%)

Monitor fallback rates to ensure model quality and cost efficiency.
                """
            }
        })
        
        # Fallback by reason
        widgets.append({
            "type": "metric",
            "properties": {
                "metrics": [
                    [CloudWatchDashboardBuilder.NAMESPACE, "FallbackCount", {"stat": "Sum"}],
                ],
                "period": 3600,
                "stat": "Sum",
                "region": "us-east-1",
                "title": "Fallback Count by Reason",
            }
        })
        
        return CloudWatchDashboardBuilder._build_dashboard(
            "Fallback Rates",
            widgets
        )
    
    @staticmethod
    def _build_dashboard(title: str, widgets: list) -> dict:
        """
        Build dashboard JSON structure.
        
        Args:
            title: Dashboard title
            widgets: List of widget definitions
            
        Returns:
            Dashboard JSON
        """
        dashboard_body = {
            "widgets": []
        }
        
        # Add widgets with positioning
        for i, widget in enumerate(widgets):
            x = (i % 2) * 12  # 2 columns
            y = (i // 2) * 6  # 6 rows per widget
            
            dashboard_body["widgets"].append({
                "type": widget["type"],
                "x": x,
                "y": y,
                "width": 12,
                "height": 6,
                "properties": widget["properties"]
            })
        
        return {
            "DashboardName": title.replace(" ", "-").lower(),
            "DashboardBody": dumps(dashboard_body)
        }
    
    @staticmethod
    def get_all_dashboards() -> dict:
        """
        Get all dashboard definitions.
        
        Returns:
            Dictionary of dashboard name -> dashboard JSON
        """
        return {
            "latency": CloudWatchDashboardBuilder.build_latency_dashboard(),
            "cost": CloudWatchDashboardBuilder.build_cost_dashboard(),
            "quality": CloudWatchDashboardBuilder.build_quality_dashboard(),
            "usage": CloudWatchDashboardBuilder.build_usage_dashboard(),
            "fallback": CloudWatchDashboardBuilder.build_fallback_dashboard(),
        }
