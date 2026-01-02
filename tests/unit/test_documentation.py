"""Tests for documentation integrity and completeness."""

import re
from pathlib import Path

import pytest


@pytest.fixture
def docs_dir():
    """Get the docs directory path."""
    return Path(__file__).parent.parent.parent / "docs"


@pytest.fixture
def readme_path():
    """Get the README path."""
    return Path(__file__).parent.parent.parent / "README.md"


class TestInstallationGuide:
    """Tests for INSTALLATION.md documentation."""

    def test_installation_guide_exists(self, docs_dir):
        """Test that INSTALLATION.md exists."""
        installation_md = docs_dir / "INSTALLATION.md"
        assert installation_md.exists(), "INSTALLATION.md should exist in docs directory"

    def test_installation_guide_structure(self, docs_dir):
        """Test that INSTALLATION.md has proper structure."""
        installation_md = docs_dir / "INSTALLATION.md"
        content = installation_md.read_text()

        # Check for required sections
        required_sections = [
            "Prerequisites",
            "Platform-Specific Prerequisites",
            "Installation Methods",
            "Configuration",
            "Running ATOLL",
            "Running as a System Service",
            "Troubleshooting",
            "Uninstallation",
        ]

        for section in required_sections:
            assert section in content, f"Section '{section}' should be in INSTALLATION.md"

    def test_installation_guide_has_linux_instructions(self, docs_dir):
        """Test that guide includes Linux instructions."""
        installation_md = docs_dir / "INSTALLATION.md"
        content = installation_md.read_text()

        # Check for Linux-specific content
        linux_indicators = [
            "Linux",
            "Ubuntu",
            "systemd",
            "apt",
            "source venv/bin/activate",
        ]

        found = sum(1 for indicator in linux_indicators if indicator in content)
        assert found >= 3, "Should have Linux-specific installation instructions"

    def test_installation_guide_has_windows_instructions(self, docs_dir):
        """Test that guide includes Windows instructions."""
        installation_md = docs_dir / "INSTALLATION.md"
        content = installation_md.read_text()

        # Check for Windows-specific content
        windows_indicators = [
            "Windows",
            "PowerShell",
            "venv\\Scripts\\activate",
            "NSSM",
            "sc.exe",
        ]

        found = sum(1 for indicator in windows_indicators if indicator in content)
        assert found >= 3, "Should have Windows-specific installation instructions"

    def test_installation_guide_code_blocks_balanced(self, docs_dir):
        """Test that code blocks are properly closed."""
        installation_md = docs_dir / "INSTALLATION.md"
        content = installation_md.read_text()

        # Count code block markers
        code_blocks = content.count("```")
        assert code_blocks % 2 == 0, "Code blocks should be balanced (equal opening/closing)"

    def test_installation_guide_internal_links(self, docs_dir):
        """Test that internal links in INSTALLATION.md are valid."""
        installation_md = docs_dir / "INSTALLATION.md"
        content = installation_md.read_text()

        # Find all internal links
        internal_links = re.findall(r"\[([^\]]+)\]\(#([^\)]+)\)", content)

        # Find all headers
        headers = re.findall(r"^#{1,6}\s+(.+)$", content, re.MULTILINE)

        # Convert headers to IDs (GitHub markdown style)
        header_ids = set()
        for header in headers:
            # Remove markdown formatting, convert to lowercase, handle spaces/hyphens
            # This matches GitHub's anchor generation algorithm
            header_id = re.sub(r"[^\w\s-]", "", header).strip().lower()
            # Replace spaces and multiple hyphens with single hyphen
            header_id = re.sub(r"[\s]+", "-", header_id)
            header_id = re.sub(r"-+", "-", header_id)
            # Remove leading/trailing hyphens
            header_id = header_id.strip("-")
            header_ids.add(header_id)

        # Check each internal link
        broken_links = []
        for link_text, link_id in internal_links:
            if link_id not in header_ids:
                broken_links.append(f"[{link_text}](#{link_id})")

        assert not broken_links, f"Found broken internal links: {broken_links}"

    def test_installation_guide_has_service_setup(self, docs_dir):
        """Test that guide includes service setup instructions."""
        installation_md = docs_dir / "INSTALLATION.md"
        content = installation_md.read_text()

        # Check for service-related content
        assert "systemd" in content, "Should include systemd service setup"
        assert "Windows Service" in content, "Should include Windows service setup"
        assert "/etc/systemd/system" in content, "Should have systemd service file path"


class TestREADME:
    """Tests for README.md documentation."""

    def test_readme_exists(self, readme_path):
        """Test that README.md exists."""
        assert readme_path.exists(), "README.md should exist"

    def test_readme_references_installation_guide(self, readme_path):
        """Test that README links to INSTALLATION.md."""
        content = readme_path.read_text()

        # Check for link to installation guide
        assert "docs/INSTALLATION.md" in content, "README should link to INSTALLATION.md"
        assert "Installation Guide" in content, "README should reference Installation Guide"

    def test_readme_has_installation_section(self, readme_path):
        """Test that README has an Installation section."""
        content = readme_path.read_text()

        # Check for installation section
        installation_section = re.search(r"^## .* Installation", content, re.MULTILINE)
        assert installation_section, "README should have an Installation section"

    def test_readme_navigation_links(self, readme_path):
        """Test that README has proper navigation links."""
        content = readme_path.read_text()

        # Key navigation items that should exist
        required_nav = [
            "features",
            "installation",
            "quick-start",
            "documentation",
        ]

        for nav_item in required_nav:
            # Check if link exists (case-insensitive)
            pattern = rf"\(#.*{nav_item}.*\)"
            assert re.search(
                pattern, content, re.IGNORECASE
            ), f"README should have navigation link for '{nav_item}'"

    def test_readme_version_badge(self, readme_path):
        """Test that README includes version badge."""
        content = readme_path.read_text()

        # Check for version badge
        assert (
            "version-2.0.0" in content or "v2.0.0" in content
        ), "README should include version 2.0.0"

    def test_readme_prerequisites(self, readme_path):
        """Test that README mentions prerequisites."""
        content = readme_path.read_text()

        # Key prerequisites
        assert "Python 3.9" in content, "README should mention Python 3.9+ requirement"
        assert "Ollama" in content, "README should mention Ollama requirement"


class TestDocumentationCompleteness:
    """Tests for overall documentation completeness."""

    def test_deployment_docs_exist(self, docs_dir):
        """Test that deployment documentation exists."""
        deployment_docs = [
            "DEPLOYMENT_SERVER_V2_USAGE.md",
            "DEPLOYMENT_QUICK_REFERENCE.md",
        ]

        for doc in deployment_docs:
            doc_path = docs_dir / doc
            assert doc_path.exists(), f"{doc} should exist in docs directory"

    def test_contributing_guide_exists(self):
        """Test that CONTRIBUTING.md exists."""
        contributing_md = Path(__file__).parent.parent.parent / "CONTRIBUTING.md"
        assert contributing_md.exists(), "CONTRIBUTING.md should exist"

    def test_all_markdown_files_have_content(self, docs_dir):
        """Test that all markdown files in docs/ have content."""
        md_files = list(docs_dir.glob("*.md"))

        for md_file in md_files:
            content = md_file.read_text()
            assert len(content) > 100, f"{md_file.name} should have substantial content"


class TestCodeExamples:
    """Tests for code examples in documentation."""

    def test_installation_guide_has_code_examples(self, docs_dir):
        """Test that INSTALLATION.md includes code examples."""
        installation_md = docs_dir / "INSTALLATION.md"
        content = installation_md.read_text()

        # Count code blocks
        code_blocks = content.count("```")
        assert code_blocks >= 20, "INSTALLATION.md should have multiple code examples"

        # Check for specific language markers
        assert "```bash" in content, "Should have bash code examples"
        assert "```json" in content, "Should have JSON configuration examples"
        assert "```powershell" in content, "Should have PowerShell examples for Windows"

    def test_code_examples_syntax(self, docs_dir):
        """Test that code examples have proper syntax markers."""
        installation_md = docs_dir / "INSTALLATION.md"
        content = installation_md.read_text()

        # Find all code blocks
        code_blocks = re.findall(r"```(\w+)?\n(.*?)```", content, re.DOTALL)

        # At least some should have language markers
        with_lang = sum(1 for lang, _ in code_blocks if lang)
        assert (
            with_lang >= 10
        ), "Most code blocks should have language markers for proper highlighting"
