"""Smart filename parsing for manga files."""

import re
from pathlib import Path

from app.models.schemas import FilenameParseResult


class FilenameParserService:
    """Parses manga filenames to extract series, chapter, and volume info."""

    # Patterns ordered by specificity
    PATTERNS = [
        # "Series Name - Vol.01 Ch.001"
        r"^(.+?)\s*[-_]\s*[Vv]ol\.?\s*(\d+)\s*[Cc]h(?:apter)?\.?\s*(\d+)",
        # "Series Name Vol.01 Ch.001"
        r"^(.+?)\s+[Vv]ol\.?\s*(\d+)\s*[Cc]h(?:apter)?\.?\s*(\d+)",
        # "Series Name - Chapter 001"
        r"^(.+?)\s*[-_]\s*[Cc]h(?:apter)?\.?\s*(\d+)",
        # "Series Name Chapter 001"
        r"^(.+?)\s+[Cc]h(?:apter)?\.?\s*(\d+)",
        # "Issue #1", "Issue #2", etc.
        r"^(.+?)\s*#\s*(\d+)",
        # "Series Name - Vol.01"
        r"^(.+?)\s*[-_]\s*[Vv]ol(?:ume)?\.?\s*(\d+)",
        # "Series Name Vol.01"
        r"^(.+?)\s+[Vv]ol(?:ume)?\.?\s*(\d+)",
        # "Part 1", "Part 2", etc.
        r"^(.+?)\s+[Pp]art\.?\s*(\d+)",
        # "Series Name - 001"
        r"^(.+?)\s*[-_]\s*(\d{2,4})(?:\s|$|\.)",
        # "Series Name 001"
        r"^(.+?)\s+(\d{2,4})(?:\s|$|\.)",
        # "[Group] Series Name - 001"
        r"^\[.+?\]\s*(.+?)\s*[-_]\s*(\d{2,4})",
        # "(Group) Series Name - 001"
        r"^\(.+?\)\s*(.+?)\s*[-_]\s*(\d{2,4})",
    ]

    def parse(self, filename: str) -> FilenameParseResult:
        """
        Parse a filename to extract series, chapter, and volume.

        Args:
            filename: The filename to parse (with or without extension)

        Returns:
            FilenameParseResult with extracted info
        """
        # Remove extension
        name = Path(filename).stem

        # Try each pattern
        for pattern in self.PATTERNS:
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                groups = match.groups()

                if len(groups) == 3:
                    # Volume and chapter
                    return FilenameParseResult(
                        series=self._clean_series(groups[0]),
                        volume=int(groups[1]),
                        chapter=int(groups[2]),
                        title=name,
                    )
                elif len(groups) == 2:
                    series = self._clean_series(groups[0])
                    number = int(groups[1])

                    # Determine if it's volume or chapter based on context
                    if "vol" in name.lower():
                        return FilenameParseResult(
                            series=series,
                            volume=number,
                            title=name,
                        )
                    else:
                        return FilenameParseResult(
                            series=series,
                            chapter=number,
                            title=name,
                        )

        # No pattern matched - use filename as title
        return FilenameParseResult(
            title=name,
            series=self._clean_series(name),
        )

    def suggest_order(self, filenames: list[str]) -> list[int]:
        """
        Suggest reading order based on parsed chapter/volume numbers.

        Args:
            filenames: List of filenames to order

        Returns:
            List of indices representing suggested order
        """
        parsed = [(idx, self.parse(f)) for idx, f in enumerate(filenames)]

        def sort_key(item: tuple[int, FilenameParseResult]) -> tuple[int, int, int, str]:
            idx, result = item
            vol = result.volume or 0
            ch = result.chapter or 0

            # If no chapter/volume found, try to extract any number from filename
            fallback_num = 0
            if ch == 0 and vol == 0:
                fallback_num = self._extract_number(filenames[idx])

            # Sort by volume, then chapter, then fallback number, then original filename
            return (vol, ch, fallback_num, filenames[idx])

        sorted_items = sorted(parsed, key=sort_key)
        return [item[0] for item in sorted_items]

    def _extract_number(self, filename: str) -> int:
        """Extract the most relevant number from a filename for sorting."""
        name = Path(filename).stem

        # Look for patterns like #1, #2, etc.
        hash_match = re.search(r"#\s*(\d+)", name)
        if hash_match:
            return int(hash_match.group(1))

        # Look for any number in the filename
        numbers = re.findall(r"(\d+)", name)
        if numbers:
            # Return the last number (usually the most specific, e.g., "Series Vol 1 Ch 5" -> 5)
            return int(numbers[-1])

        return 0

    def suggest_series_name(self, filenames: list[str]) -> str | None:
        """
        Suggest a common series name from multiple filenames.

        Args:
            filenames: List of filenames

        Returns:
            Suggested series name or None
        """
        series_names: list[str] = []

        for filename in filenames:
            result = self.parse(filename)
            if result.series:
                series_names.append(result.series)

        if not series_names:
            return None

        # Find common prefix among all series names
        if len(set(series_names)) == 1:
            return series_names[0]

        # Try to find longest common prefix
        common = self._longest_common_prefix(series_names)
        if len(common) >= 3:
            return common.strip(" -_")

        # Return most common series name
        from collections import Counter

        counter = Counter(series_names)
        return counter.most_common(1)[0][0]

    def _clean_series(self, series: str) -> str:
        """Clean up a series name."""
        # Remove common prefixes/suffixes
        series = series.strip(" -_.")

        # Remove trailing numbers that might be chapter indicators
        series = re.sub(r"\s*[-_]?\s*\d+\s*$", "", series)

        # Remove quality indicators
        series = re.sub(r"\s*\[.*?\]\s*$", "", series)
        series = re.sub(r"\s*\(.*?\)\s*$", "", series)

        # Clean up extra whitespace
        series = re.sub(r"\s+", " ", series)

        return series.strip()

    def _longest_common_prefix(self, strings: list[str]) -> str:
        """Find the longest common prefix among strings."""
        if not strings:
            return ""

        prefix = strings[0]
        for s in strings[1:]:
            while not s.startswith(prefix) and prefix:
                prefix = prefix[:-1]

        return prefix
