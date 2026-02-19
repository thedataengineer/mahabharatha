"""ZERG performance analysis package — comprehensive performance auditing."""

from mahabharatha.performance.aggregator import PerformanceAuditor
from mahabharatha.performance.catalog import FactorCatalog
from mahabharatha.performance.formatters import format_json, format_markdown, format_rich, format_sarif
from mahabharatha.performance.stack_detector import detect_stack
from mahabharatha.performance.tool_registry import ToolRegistry
from mahabharatha.performance.types import (
    CategoryScore,
    DetectedStack,
    PerformanceFinding,
    PerformanceReport,
    Severity,
    ToolStatus,
)

__all__ = [
    "CategoryScore",
    "DetectedStack",
    "FactorCatalog",
    "PerformanceAuditor",
    "PerformanceFinding",
    "PerformanceReport",
    "Severity",
    "ToolRegistry",
    "ToolStatus",
    "detect_stack",
    "format_json",
    "format_markdown",
    "format_rich",
    "format_sarif",
]
