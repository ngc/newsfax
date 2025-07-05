#!/usr/bin/env python3
"""
Integration test script for the Newsfax API.
Tests both mock and real fact checking capabilities.
"""

import asyncio
import sys
from api import extract_content_from_url, analyze_facts_with_ai, FACT_CHECKING_ENABLED


async def test_content_extraction():
    """Test content extraction functionality"""
    print("🧪 Testing content extraction...")

    try:
        url = "https://example.com/test"
        content = await extract_content_from_url(url)

        print(f"✅ Content extracted: {content[:100]}...")
        assert isinstance(content, str)
        assert len(content) > 0
        print("✅ Content extraction test passed")
        return True

    except Exception as e:
        print(f"❌ Content extraction test failed: {e}")
        return False


async def test_fact_analysis():
    """Test fact analysis functionality"""
    print("\n🧪 Testing fact analysis...")

    try:
        test_content = """
        Climate change is causing global temperatures to rise.
        The Earth is flat according to some theories.
        Vaccines are important for public health.
        """

        facts = await analyze_facts_with_ai(test_content)

        print(f"✅ Found {len(facts)} facts:")
        for i, fact in enumerate(facts):
            print(f"  {i+1}. '{fact.text}' - {fact.truthfulness}")
            print(f"     Summary: {fact.summary[:60]}...")
            print(f"     Sources: {len(fact.sources)} sources")

        assert len(facts) > 0
        assert all(hasattr(fact, "text") for fact in facts)
        assert all(hasattr(fact, "truthfulness") for fact in facts)
        assert all(hasattr(fact, "summary") for fact in facts)
        assert all(hasattr(fact, "sources") for fact in facts)

        print("✅ Fact analysis test passed")
        return True

    except Exception as e:
        print(f"❌ Fact analysis test failed: {e}")
        return False


async def main():
    """Run all integration tests"""
    print("🚀 Starting Newsfax API Integration Tests")
    print(f"📊 Fact checking enabled: {FACT_CHECKING_ENABLED}")

    if not FACT_CHECKING_ENABLED:
        print("⚠️  Running in mock mode (real fact checking disabled)")
    else:
        print("🤖 Running with real AI fact checking")

    print("=" * 50)

    # Run tests
    results = []
    results.append(await test_content_extraction())
    results.append(await test_fact_analysis())

    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 All {total} tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} of {total} tests failed!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
