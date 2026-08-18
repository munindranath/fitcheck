"""Unit tests for Fitcheck tools.

Tests individual tools in isolation. No LLM, no network, no API key — which is the
point: the banned-claim gate is the part that must never be probabilistic, so it must
be testable without a model in the loop.

Strings here come from the fictional example profile (`profile.yaml`). If you are
running against your own `profile.local.yaml`, these will not match your banned list —
that is expected; copy this file and adapt it locally rather than committing your own
banned strings.
"""

import pytest
from fitcheck.tools import check_banned_claims


class TestBannedClaimsDetection:
    """Test banned claims detection logic."""

    def test_exact_match(self):
        """Exact banned claim should be detected."""
        text = "At Meridian we had ~500 customers"
        result = check_banned_claims.invoke({"text": text})
        assert not result.clean
        assert "~500 customers" in result.violations

    def test_fuzzy_match_dollar_sign(self):
        """Should detect $4M ARR variations."""
        text = "Generated $4M ARR for Meridian"
        result = check_banned_claims.invoke({"text": text})
        assert not result.clean
        assert any("$4M ARR" in v for v in result.violations)

    def test_fuzzy_match_tilde(self):
        """Should detect ~$180M variations where the tilde is dropped."""
        text = "Portfolio was approximately $180M"
        result = check_banned_claims.invoke({"text": text})
        assert not result.clean
        assert any("180m" in v.lower() for v in result.violations)

    def test_clean_text(self):
        """Real, allowed evidence should pass."""
        text = "Cut time-to-first-API-call from 11 days to under 4 hours at Meridian"
        result = check_banned_claims.invoke({"text": text})
        assert result.clean
        assert len(result.violations) == 0

    def test_multiple_violations(self):
        """Multiple banned claims should all be detected."""
        text = """
        At Meridian, managed ~500 customers with ~$180M ARR and ~9% churn.
        Also achieved $4M ARR for Meridian.
        """
        result = check_banned_claims.invoke({"text": text})
        assert not result.clean
        assert len(result.violations) >= 3  # Should catch multiple

    def test_case_insensitive(self):
        """Detection should be case-insensitive."""
        text = "Portfolio included ~500 CUSTOMERS"
        result = check_banned_claims.invoke({"text": text})
        assert not result.clean


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
