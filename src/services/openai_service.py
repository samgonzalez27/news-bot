"""
OpenAI service for generating news digests.
"""

from typing import Any, Dict, List, Optional

import httpx

from src.config import get_settings
from src.exceptions import OpenAIError
from src.logging_config import get_logger
from src.utils.markdown_sanitizer import (
    sanitize_markdown,
    sanitize_headline_field,
    verify_clean_markdown,
)

logger = get_logger("openai_service")

# OpenAI API base URL
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Hardened system prompt for digest generation
DIGEST_SYSTEM_PROMPT = """You are an expert news analyst and writer. Your task is to create a cohesive, well-written daily news digest based on the headlines and articles provided.

CRITICAL OUTPUT REQUIREMENTS:
- Output ONLY valid, clean Markdown text
- Use ONLY printable ASCII characters (codes 32-126) plus standard newlines
- NEVER output control characters, backspaces, or invisible formatting bytes
- NEVER output zero-width spaces or other Unicode control characters
- Use exactly two asterisks for bold (**text**) - never three or more
- Use exactly one asterisk for italic (*text*)
- Use a single hyphen followed by a space for bullet points (- item)
- Use standard newlines (LF) for line breaks - never carriage returns
- Ensure all bold/italic markers are properly balanced (opened and closed)

STRUCTURE REQUIREMENTS:
1. Start with the exact header format shown below
2. Follow with Executive Summary (2-3 sentences)
3. Organize by topic/category using ## headers
4. End with Key Takeaways section (3-5 bullet points)
5. Keep total length between 600-1000 words

FORMATTING:
- Use ## for section headers (not ### or #)
- Use - for all bullet points (not * or numbers for bullet lists)
- Use **text** for bold emphasis
- Leave one blank line between sections
- No trailing spaces on any line

EXACT OUTPUT FORMAT:

# Daily News Digest – [EXACT DATE FROM USER PROMPT]

**Executive Summary:** [2-3 sentence overview of the day's key news]

## [Topic Category 1]

[Paragraph summarizing related stories. Use **bold** for key terms.]

- [Key point 1]
- [Key point 2]

## [Topic Category 2]

[Content following same pattern]

## Key Takeaways

- [Takeaway 1]
- [Takeaway 2]
- [Takeaway 3]

CONTENT GUIDELINES:
1. Write in a professional, objective journalistic style
2. Summarize key developments clearly and concisely
3. Highlight connections between related stories when relevant
4. Focus on facts, not speculation
5. Use the EXACT date provided in the user prompt for the header

Remember: Clean, parseable Markdown only. No hidden characters. No formatting artifacts."""


class OpenAIService:
    """Service for generating content using OpenAI API."""

    def __init__(self):
        """Initialize OpenAI service with HTTP client."""
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _format_headlines_for_prompt(
        self,
        headlines: List[Dict[str, Any]],
    ) -> str:
        """
        Format headlines into a structured prompt.

        Args:
            headlines: List of headline dictionaries.

        Returns:
            Formatted string for the prompt.
        """
        # Group by category
        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for headline in headlines:
            category = headline.get("interest_slug", headline.get("category", "general"))
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(headline)

        # Format each category with sanitized fields
        sections = []
        for category, articles in by_category.items():
            # Sanitize category name
            clean_category = sanitize_headline_field(
                category.replace('-', ' ').title(),
                max_length=50
            )
            section_lines = [f"### {clean_category}"]
            
            for article in articles[:5]:  # Limit articles per category
                # Sanitize all fields from external source
                title = sanitize_headline_field(article.get("title", ""), max_length=200)
                description = sanitize_headline_field(article.get("description", ""), max_length=300)
                source = sanitize_headline_field(article.get("source", ""), max_length=50)
                
                if title:
                    section_lines.append(f"- **{title}** ({source})")
                    if description:
                        section_lines.append(f"  {description}")
            
            sections.append("\n".join(section_lines))

        return "\n\n".join(sections)

    async def generate_digest(
        self,
        headlines: List[Dict[str, Any]],
        digest_date: str,
        interests: List[str],
    ) -> Dict[str, Any]:
        """
        Generate a news digest from headlines.

        Args:
            headlines: List of headline dictionaries.
            digest_date: Date string for the digest.
            interests: List of interest slugs included.

        Returns:
            Dict with 'content', 'summary', and 'word_count'.

        Raises:
            OpenAIError: If API call fails.
        """
        if not headlines:
            logger.warning("No headlines provided for digest generation")
            content = (
                f"# Daily News Digest – {digest_date}\n\n"
                f"**Executive Summary:** No news articles available for today's digest.\n\n"
                f"## Key Takeaways\n\n"
                f"- No news articles were available for the selected interests."
            )
            return {
                "content": sanitize_markdown(content),
                "summary": "No news available",
                "word_count": 20,
            }

        # Format headlines for the prompt (with sanitization)
        formatted_headlines = self._format_headlines_for_prompt(headlines)

        # Sanitize interests list
        clean_interests = [sanitize_headline_field(i, max_length=30) for i in interests]

        user_prompt = f"""Create a news digest for {digest_date} based on the following headlines and summaries.

The user is interested in: {', '.join(clean_interests)}

Headlines:

{formatted_headlines}

Create a cohesive, well-written digest following the guidelines provided. Use the exact date "{digest_date}" in the header."""

        try:
            response = await self.client.post(
                OPENAI_API_URL,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            data = response.json()

            # Extract and sanitize content
            raw_content = data["choices"][0]["message"]["content"]
            content = sanitize_markdown(raw_content)
            
            # Verify content is clean
            verification = verify_clean_markdown(content)
            if not verification['is_clean']:
                logger.warning(
                    f"Content sanitization issues detected: {verification['issues']}"
                )
            
            word_count = len(content.split())

            # Generate a brief summary (first paragraph after executive summary)
            summary = self._extract_summary(content)

            logger.info(
                f"Generated digest: {word_count} words, "
                f"{len(headlines)} headlines used"
            )

            return {
                "content": content,
                "summary": summary,
                "word_count": word_count,
            }

        except httpx.HTTPStatusError as e:
            error_body = e.response.json() if e.response.content else {}
            error_msg = error_body.get("error", {}).get("message", str(e))
            logger.error(f"OpenAI API error: {error_msg}")
            raise OpenAIError(
                error_msg,
                {"status_code": e.response.status_code},
            )
        except httpx.RequestError as e:
            logger.error(f"OpenAI request error: {e}")
            raise OpenAIError("Failed to connect to OpenAI API")
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected OpenAI response format: {e}")
            raise OpenAIError("Invalid response from OpenAI API")

    def _extract_summary(self, content: str, max_length: int = 200) -> str:
        """
        Extract a brief summary from the digest content.

        Args:
            content: Full digest content.
            max_length: Maximum summary length.

        Returns:
            Brief summary string.
        """
        import re
        
        # Try to find executive summary
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "executive summary" in line.lower() or line.startswith("**Executive"):
                # Get the next non-empty line
                for next_line in lines[i:i + 3]:
                    # Remove markdown bold markers and common prefixes
                    clean_line = next_line.strip()
                    # Remove **Executive Summary:** or similar patterns
                    clean_line = re.sub(
                        r'^\*{0,2}(Executive\s+Summary:?\s*)\*{0,2}\s*',
                        '',
                        clean_line,
                        flags=re.IGNORECASE
                    )
                    # Remove any remaining leading/trailing asterisks
                    clean_line = clean_line.strip("*").strip()
                    
                    if clean_line and not clean_line.startswith("#"):
                        if len(clean_line) > max_length:
                            return clean_line[:max_length].rsplit(" ", 1)[0] + "..."
                        return clean_line

        # Fallback: use first substantial paragraph
        for line in lines:
            clean_line = line.strip()
            # Remove any markdown bold markers
            clean_line = re.sub(r'\*{2}([^*]+)\*{2}', r'\1', clean_line)
            if (
                clean_line
                and not clean_line.startswith("#")
                and not clean_line.startswith("-")
                and len(clean_line) > 50
            ):
                if len(clean_line) > max_length:
                    return clean_line[:max_length].rsplit(" ", 1)[0] + "..."
                return clean_line

        return "Daily news digest generated"


# Singleton instance
_openai_service: Optional[OpenAIService] = None


async def get_openai_service() -> OpenAIService:
    """
    Get or create the OpenAIService singleton.

    Returns:
        OpenAIService: Singleton instance.
    """
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service


async def close_openai_service():
    """Close the OpenAIService singleton."""
    global _openai_service
    if _openai_service:
        await _openai_service.close()
        _openai_service = None
