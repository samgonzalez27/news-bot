"""
Markdown Sanitizer Utility

Provides deterministic sanitization of markdown content to remove:
- Backspace characters (ASCII 0x08)
- Zero-width characters
- Carriage returns and mixed line endings
- Stray control characters
- Malformed markdown artifacts

This should be applied immediately before saving any digest content.
"""

import re
import unicodedata
from typing import Optional


# Control characters to remove (ASCII 0x00-0x08, 0x0B-0x0C, 0x0E-0x1F, 0x7F)
# Excludes: 0x09 (tab), 0x0A (newline), 0x0D (carriage return - handled separately)
CONTROL_CHAR_PATTERN = re.compile(
    r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]'
)

# Zero-width and invisible characters
ZERO_WIDTH_PATTERN = re.compile(
    r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff9-\ufffc]'
)

# Malformed bold markers (triple or more asterisks)
MALFORMED_BOLD_PATTERN = re.compile(r'\*{3,}')

# Multiple consecutive newlines (more than 2)
EXCESSIVE_NEWLINES_PATTERN = re.compile(r'\n{3,}')

# Multiple consecutive spaces
MULTIPLE_SPACES_PATTERN = re.compile(r' {2,}')

# Trailing whitespace on lines
TRAILING_WHITESPACE_PATTERN = re.compile(r'[ \t]+$', re.MULTILINE)


def sanitize_markdown(content: str) -> str:
    """
    Sanitize markdown content by removing control characters and fixing formatting.
    
    This function performs the following sanitization steps:
    1. Normalize Unicode (NFC form)
    2. Remove backspace characters (ASCII 0x08)
    3. Remove zero-width and invisible characters
    4. Normalize line endings (CRLF/CR -> LF)
    5. Remove other control characters
    6. Fix malformed bold/italic markers
    7. Normalize excessive whitespace
    8. Ensure consistent list formatting
    9. Strip trailing whitespace
    
    Args:
        content: Raw markdown string
        
    Returns:
        Sanitized markdown string
    """
    if not content:
        return ""
    
    # Step 1: Normalize Unicode to NFC form
    content = unicodedata.normalize('NFC', content)
    
    # Step 2: Remove backspace characters explicitly
    content = content.replace('\x08', '')
    content = content.replace('\b', '')
    
    # Step 3: Remove zero-width and invisible characters
    content = ZERO_WIDTH_PATTERN.sub('', content)
    
    # Step 4: Normalize line endings (CRLF -> LF, CR -> LF)
    content = content.replace('\r\n', '\n')
    content = content.replace('\r', '\n')
    
    # Step 5: Remove other control characters
    content = CONTROL_CHAR_PATTERN.sub('', content)
    
    # Step 6: Fix malformed bold markers (*** -> **)
    content = MALFORMED_BOLD_PATTERN.sub('**', content)
    
    # Step 7: Fix unbalanced asterisks at line boundaries
    content = _fix_unbalanced_markers(content)
    
    # Step 8: Normalize excessive newlines (max 2 consecutive)
    content = EXCESSIVE_NEWLINES_PATTERN.sub('\n\n', content)
    
    # Step 9: Remove trailing whitespace from each line
    content = TRAILING_WHITESPACE_PATTERN.sub('', content)
    
    # Step 10: Normalize multiple spaces (but preserve single space after list markers)
    lines = content.split('\n')
    normalized_lines = []
    for line in lines:
        # Preserve list item formatting
        if line.lstrip().startswith(('-', '*')) or re.match(r'^\s*\d+\.', line):
            # Only normalize spaces after the list marker content
            match = re.match(r'^(\s*[-*]|\s*\d+\.)\s*', line)
            if match:
                prefix = match.group(0)
                rest = line[len(match.group(0)):]
                line = prefix + MULTIPLE_SPACES_PATTERN.sub(' ', rest)
        else:
            line = MULTIPLE_SPACES_PATTERN.sub(' ', line)
        normalized_lines.append(line)
    content = '\n'.join(normalized_lines)
    
    # Step 11: Ensure proper spacing after headings
    content = re.sub(r'^(#{1,6}\s+.+)$\n(?!\n)', r'\1\n\n', content, flags=re.MULTILINE)
    
    # Step 12: Ensure bullet lists have consistent markers (use - not *)
    content = re.sub(r'^(\s*)\* ', r'\1- ', content, flags=re.MULTILINE)
    
    # Step 13: Final trim
    content = content.strip()
    
    return content


def _fix_unbalanced_markers(content: str) -> str:
    """
    Fix unbalanced bold/italic markers.
    
    Args:
        content: Markdown content
        
    Returns:
        Content with balanced markers
    """
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Count double asterisks (bold markers)
        double_asterisks = len(re.findall(r'\*\*', line))
        
        if double_asterisks % 2 != 0:
            # Unbalanced - try to fix by removing trailing **
            if line.rstrip().endswith('**') and not line.rstrip().endswith('***'):
                line = line.rstrip()[:-2].rstrip()
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def sanitize_headline_field(text: Optional[str], max_length: int = 500) -> str:
    """
    Sanitize a single headline field (title, description, source).
    
    Removes control characters and truncates to max length.
    
    Args:
        text: Input text, may be None
        max_length: Maximum length to preserve
        
    Returns:
        Sanitized text string
    """
    if not text:
        return ""
    
    # Normalize Unicode
    text = unicodedata.normalize('NFC', text)
    
    # Remove control characters
    text = CONTROL_CHAR_PATTERN.sub('', text)
    text = ZERO_WIDTH_PATTERN.sub('', text)
    text = text.replace('\x08', '')
    text = text.replace('\b', '')
    
    # Normalize whitespace
    text = text.replace('\r\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('\n', ' ')
    text = MULTIPLE_SPACES_PATTERN.sub(' ', text)
    
    # Trim and truncate
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    
    return text


def verify_clean_markdown(content: str) -> dict:
    """
    Verify that markdown content is clean.
    
    Returns a dict with verification results.
    
    Args:
        content: Markdown content to verify
        
    Returns:
        Dict with 'is_clean', 'issues' list, and 'details'
    """
    issues = []
    
    # Check for control characters
    control_matches = CONTROL_CHAR_PATTERN.findall(content)
    if control_matches:
        issues.append(f"Found {len(control_matches)} control characters")
    
    # Check for backspace
    if '\x08' in content or '\b' in content:
        issues.append("Found backspace characters")
    
    # Check for zero-width characters
    zero_width_matches = ZERO_WIDTH_PATTERN.findall(content)
    if zero_width_matches:
        issues.append(f"Found {len(zero_width_matches)} zero-width characters")
    
    # Check for carriage returns
    if '\r' in content:
        issues.append("Found carriage return characters")
    
    # Check for excessive newlines
    if '\n\n\n' in content:
        issues.append("Found excessive consecutive newlines")
    
    # Check for malformed bold markers
    if MALFORMED_BOLD_PATTERN.search(content):
        issues.append("Found malformed bold markers (3+ asterisks)")
    
    # Check for unbalanced bold markers per line
    for i, line in enumerate(content.split('\n'), 1):
        double_count = len(re.findall(r'\*\*', line))
        if double_count % 2 != 0:
            issues.append(f"Unbalanced bold markers on line {i}")
            break  # Only report first occurrence
    
    return {
        'is_clean': len(issues) == 0,
        'issues': issues,
        'character_count': len(content),
        'line_count': content.count('\n') + 1,
    }
