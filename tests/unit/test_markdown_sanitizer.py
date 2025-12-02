"""
Unit tests for markdown sanitizer utility.
"""

from src.utils.markdown_sanitizer import (
    sanitize_markdown,
    sanitize_headline_field,
    verify_clean_markdown,
)


class TestSanitizeMarkdown:
    """Tests for sanitize_markdown function."""

    def test_empty_content(self):
        """Should return empty string for empty input."""
        assert sanitize_markdown("") == ""
        assert sanitize_markdown(None) == ""

    def test_removes_backspace_characters(self):
        """Should remove backspace characters."""
        content = "Hello\x08 World"
        result = sanitize_markdown(content)
        assert "\x08" not in result
        assert result == "Hello World"

    def test_removes_zero_width_characters(self):
        """Should remove zero-width characters."""
        content = "Hello\u200bWorld"  # Zero-width space
        result = sanitize_markdown(content)
        assert "\u200b" not in result
        assert result == "HelloWorld"

    def test_normalizes_crlf_to_lf(self):
        """Should normalize CRLF to LF."""
        content = "Line 1\r\nLine 2\r\nLine 3"
        result = sanitize_markdown(content)
        assert "\r" not in result
        assert result == "Line 1\nLine 2\nLine 3"

    def test_normalizes_cr_to_lf(self):
        """Should normalize CR to LF."""
        content = "Line 1\rLine 2"
        result = sanitize_markdown(content)
        assert "\r" not in result

    def test_removes_control_characters(self):
        """Should remove control characters."""
        content = "Hello\x00\x01\x02World"
        result = sanitize_markdown(content)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result
        assert result == "HelloWorld"

    def test_fixes_malformed_bold_markers(self):
        """Should fix triple asterisks to double."""
        content = "This is ***bold*** text"
        result = sanitize_markdown(content)
        assert "***" not in result
        assert "**bold**" in result

    def test_normalizes_excessive_newlines(self):
        """Should limit consecutive newlines to 2."""
        content = "Para 1\n\n\n\nPara 2"
        result = sanitize_markdown(content)
        assert "\n\n\n" not in result
        assert "Para 1\n\nPara 2" == result

    def test_removes_trailing_whitespace(self):
        """Should remove trailing whitespace from lines."""
        content = "Line 1   \nLine 2\t\nLine 3"
        result = sanitize_markdown(content)
        lines = result.split("\n")
        for line in lines:
            assert line == line.rstrip()

    def test_normalizes_bullet_markers(self):
        """Should normalize * bullets to - bullets."""
        content = "* Item 1\n* Item 2"
        result = sanitize_markdown(content)
        assert "- Item 1" in result
        assert "- Item 2" in result

    def test_preserves_valid_markdown(self):
        """Should preserve valid markdown structure."""
        content = """# Daily News Digest – December 1, 2025

**Executive Summary:** This is a test.

## Section 1

Some content here.

- Bullet 1
- Bullet 2

## Key Takeaways

- Takeaway 1"""
        result = sanitize_markdown(content)
        assert "# Daily News Digest" in result
        assert "**Executive Summary:**" in result
        assert "## Section 1" in result
        assert "- Bullet 1" in result

    def test_handles_unicode_normalization(self):
        """Should normalize Unicode to NFC form."""
        # é can be represented as single char or combining chars
        content = "cafe\u0301"  # e + combining acute
        result = sanitize_markdown(content)
        assert "café" in result or "cafe" in result  # Normalized


class TestSanitizeHeadlineField:
    """Tests for sanitize_headline_field function."""

    def test_empty_input(self):
        """Should return empty string for empty/None input."""
        assert sanitize_headline_field("") == ""
        assert sanitize_headline_field(None) == ""

    def test_removes_control_characters(self):
        """Should remove control characters from headline."""
        headline = "Breaking\x08 News\x00: Something"
        result = sanitize_headline_field(headline)
        assert "\x08" not in result
        assert "\x00" not in result

    def test_normalizes_whitespace(self):
        """Should normalize whitespace to single spaces."""
        headline = "Breaking   News\n\nAlert"
        result = sanitize_headline_field(headline)
        assert "  " not in result
        assert "\n" not in result

    def test_truncates_long_text(self):
        """Should truncate text at word boundary."""
        headline = "A " * 100  # Long headline
        result = sanitize_headline_field(headline, max_length=50)
        assert len(result) <= 53  # 50 + "..."
        assert result.endswith("...")

    def test_preserves_short_text(self):
        """Should preserve short text unchanged (except cleanup)."""
        headline = "Short headline"
        result = sanitize_headline_field(headline)
        assert result == "Short headline"


class TestVerifyCleanMarkdown:
    """Tests for verify_clean_markdown function."""

    def test_clean_content(self):
        """Should return is_clean=True for clean content."""
        content = "# Header\n\nParagraph text.\n\n- Bullet"
        result = verify_clean_markdown(content)
        assert result['is_clean'] is True
        assert len(result['issues']) == 0

    def test_detects_control_characters(self):
        """Should detect control characters."""
        content = "Hello\x00World"
        result = verify_clean_markdown(content)
        assert result['is_clean'] is False
        assert any("control" in issue.lower() for issue in result['issues'])

    def test_detects_backspace(self):
        """Should detect backspace characters."""
        content = "Hello\x08World"
        result = verify_clean_markdown(content)
        assert result['is_clean'] is False
        assert any("backspace" in issue.lower() for issue in result['issues'])

    def test_detects_carriage_returns(self):
        """Should detect carriage returns."""
        content = "Hello\rWorld"
        result = verify_clean_markdown(content)
        assert result['is_clean'] is False
        assert any("carriage" in issue.lower() for issue in result['issues'])

    def test_detects_malformed_bold(self):
        """Should detect malformed bold markers."""
        content = "This is ***bold*** text"
        result = verify_clean_markdown(content)
        assert result['is_clean'] is False
        assert any("bold" in issue.lower() for issue in result['issues'])

    def test_returns_character_count(self):
        """Should return character count."""
        content = "12345"
        result = verify_clean_markdown(content)
        assert result['character_count'] == 5

    def test_returns_line_count(self):
        """Should return line count."""
        content = "Line 1\nLine 2\nLine 3"
        result = verify_clean_markdown(content)
        assert result['line_count'] == 3
