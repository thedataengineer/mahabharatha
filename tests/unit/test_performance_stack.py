"""Tests for mahabharatha.performance.stack_detector module."""

from __future__ import annotations

import json
from pathlib import Path

from mahabharatha.performance.stack_detector import detect_stack


class TestDetectStack:
    """Tests for detect_stack() function."""

    def test_empty_directory(self, tmp_path: Path) -> None:
        stack = detect_stack(str(tmp_path))
        assert stack.languages == []
        assert stack.frameworks == []
        assert stack.has_docker is False
        assert stack.has_kubernetes is False

    def test_detect_python_files(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("x = 1")
        stack = detect_stack(str(tmp_path))
        assert "python" in stack.languages

    def test_detect_react_framework(self, tmp_path: Path) -> None:
        pkg = {"dependencies": {"react": "^18.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        stack = detect_stack(str(tmp_path))
        assert "react" in stack.frameworks

    def test_detect_dockerfile(self, tmp_path: Path) -> None:
        (tmp_path / "Dockerfile").write_text("FROM python:3.12")
        stack = detect_stack(str(tmp_path))
        assert stack.has_docker is True

    def test_detect_kubernetes_manifest(self, tmp_path: Path) -> None:
        k8s_dir = tmp_path / "k8s"
        k8s_dir.mkdir()
        manifest = k8s_dir / "deployment.yaml"
        manifest.write_text("apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: app")
        stack = detect_stack(str(tmp_path))
        assert stack.has_kubernetes is True

    def test_detect_multiple_languages(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("pass")
        (tmp_path / "index.ts").write_text("export {}")
        (tmp_path / "server.go").write_text("package main")
        stack = detect_stack(str(tmp_path))
        assert "python" in stack.languages
        assert "typescript" in stack.languages
        assert "go" in stack.languages
