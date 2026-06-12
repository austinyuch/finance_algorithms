"""Showcase read surfaces for QuantLab F slices."""

from quantlab.showcase.api import ShowcaseReadAPI, build_dashboard_summary
from quantlab.showcase.html import render_dashboard_html
from quantlab.showcase.scenario import (
    build_canonical_dashboard_artifact,
    write_canonical_dashboard_artifact,
)

__all__ = [
    "ShowcaseReadAPI",
    "build_dashboard_summary",
    "build_canonical_dashboard_artifact",
    "render_dashboard_html",
    "write_canonical_dashboard_artifact",
]
