"""OpenQC smoke evidence tests for pyatb-lsp.

Verifies language detection, executable configuration, CLI availability,
and compatibility-report entry for fleet integration.
"""

from __future__ import annotations

from pathlib import Path

from pyatb_lsp.tool import _capabilities_payload, _file_type


class TestLanguageDetection:
    def test_python_file_type(self):
        assert _file_type(Path("input.py")) == "py"

    def test_poscar_file_type(self):
        assert _file_type(Path("POSCAR")) == "POSCAR"

    def test_kpoints_file_type(self):
        assert _file_type(Path("KPOINTS")) == "KPOINTS"

    def test_potcar_file_type(self):
        assert _file_type(Path("POTCAR")) == "POTCAR"

    def test_json_file_type(self):
        assert _file_type(Path("config.json")) == "json"

    def test_log_file_type(self):
        assert _file_type(Path("output.log")) == "log"

    def test_no_extension_file_type(self):
        assert _file_type(Path("README")) == "readme"


class TestCapabilitiesManifest:
    def test_capabilities_json_exists(self):
        manifest = _capabilities_payload()
        assert manifest["software"] == "pyatb"
        assert manifest["schema"] == "OpenQCLspCapabilities"

    def test_capabilities_include_fix_preview(self):
        manifest = _capabilities_payload()
        assert "fix-preview" in manifest["capabilities"]

    def test_agent_cli_operations(self):
        manifest = _capabilities_payload()
        operations = manifest["agentCli"]["operations"]
        assert "check" in operations
        assert "fix" in operations
        assert "context" in operations
        assert "hover" in operations
        assert "symbols" in operations


class TestCLIAvailability:
    def test_pyatb_lsp_tool_importable(self):
        from pyatb_lsp.tool import main

        assert callable(main)


class TestCompatibilityReport:
    def test_compatibility_entry(self):
        manifest = _capabilities_payload()
        assert "version" in manifest
        assert isinstance(manifest["version"], int)
