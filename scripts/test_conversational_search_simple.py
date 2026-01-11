"""Simplified test script for conversational search functionality."""
import asyncio
import sys
import os
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.conversation import ChatSearchRequest, ConversationContext, SearchFilters
from app.services.conversation_service import ConversationService


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"\n{status}: {test_name}")
    if details:
        print(f"   {details}")


async def test_filter_merging():
    """Test filter merging logic."""
    print_section("Test: Filter Merging Logic")
    
    service = ConversationService()
    
    # Test 1: Merge city filter
    previous = SearchFilters(city="Mumbai", interest_categories=["Fitness"])
    new = SearchFilters(city="Delhi")
    merged = service._merge_filters(previous, new)
    
    assert merged.city == "Delhi", "City should be replaced"
    assert "Fitness" in (merged.interest_categories or []), "Previous categories should be preserved"
    print_test_result("City Filter Merge", True, "City replaced, categories preserved")
    
    # Test 2: Merge numeric filters (min_followers)
    previous = SearchFilters(min_followers=50000)
    new = SearchFilters(min_followers=100000)
    merged = service._merge_filters(previous, new)
    
    assert merged.min_followers == 100000, "Should use higher value"
    print_test_result("Numeric Filter Merge (Higher)", True, f"Min followers: {merged.min_followers}")
    
    # Test 3: Merge categories
    previous = SearchFilters(interest_categories=["Fitness", "Health"])
    new = SearchFilters(interest_categories=["Fashion", "Lifestyle"])
    merged = service._merge_filters(previous, new)
    
    assert len(merged.interest_categories or []) >= 2, "Categories should be combined"
    print_test_result("Category Merge", True, f"Categories: {merged.interest_categories}")
    
    # Test 4: No previous filters
    merged = service._merge_filters(None, new)
    assert merged.interest_categories == new.interest_categories, "Should use new filters"
    print_test_result("No Previous Filters", True, "New filters applied")
    
    return True


async def test_conversation_context():
    """Test conversation context management."""
    print_section("Test: Conversation Context Management")
    
    service = ConversationService()
    conversation_id = "test-123"
    
    # Test storing context
    context = ConversationContext(
        previous_filters=SearchFilters(city="Mumbai"),
        previous_query="Find fitness influencers",
        previous_results_count=25
    )
    service.conversations[conversation_id] = context
    
    # Test retrieving context
    retrieved = service.get_conversation(conversation_id)
    assert retrieved is not None, "Context should be retrievable"
    assert retrieved.previous_filters.city == "Mumbai", "Context should preserve filters"
    print_test_result("Context Storage & Retrieval", True, "Context stored and retrieved correctly")
    
    # Test clearing context
    cleared = service.clear_conversation(conversation_id)
    assert cleared, "Context should be clearable"
    assert service.get_conversation(conversation_id) is None, "Context should be removed"
    print_test_result("Context Clearing", True, "Context cleared successfully")
    
    return True


async def test_refinement_summary():
    """Test refinement summary generation."""
    print_section("Test: Refinement Summary Generation")
    
    service = ConversationService()
    
    # Test with previous filters
    previous = SearchFilters(city="Mumbai")
    new = SearchFilters(min_followers=100000)
    merged = SearchFilters(city="Mumbai", min_followers=100000)
    
    summary = service._generate_refinement_summary(previous, new, merged)
    assert "increased minimum followers" in summary.lower() or "minimum followers" in summary.lower(), "Summary should mention changes"
    print_test_result("Refinement Summary", True, f"Summary: {summary[:60]}...")
    
    return True


async def test_suggestions():
    """Test suggestion generation."""
    print_section("Test: Suggestion Generation")
    
    service = ConversationService()
    
    # Test with many results
    filters = SearchFilters()
    suggestions = service._generate_suggestions(filters, total=100)
    assert len(suggestions) > 0, "Should generate suggestions"
    print_test_result("Suggestion Generation", True, f"Generated {len(suggestions)} suggestions")
    
    return True


async def test_request_models():
    """Test request/response models."""
    print_section("Test: Request/Response Models")
    
    # Test ChatSearchRequest
    request = ChatSearchRequest(
        query="Find fitness influencers",
        limit=10
    )
    assert request.query == "Find fitness influencers", "Query should be set"
    assert request.limit == 10, "Limit should be set"
    print_test_result("ChatSearchRequest Model", True, "Model created correctly")
    
    # Test with conversation_id
    request2 = ChatSearchRequest(
        query="Show me only those in Mumbai",
        conversation_id="test-123",
        limit=5
    )
    assert request2.conversation_id == "test-123", "Conversation ID should be set"
    print_test_result("ChatSearchRequest with Context", True, "Context included correctly")
    
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CONVERSATIONAL SEARCH - FUNCTIONALITY TEST")
    print("=" * 60)
    print("\nThis test verifies the core functionality without requiring")
    print("full database connections or API calls.")
    
    results = []
    
    try:
        # Test 1: Request Models
        results.append(await test_request_models())
    except Exception as e:
        print_test_result("Request Models", False, str(e))
        results.append(False)
    
    try:
        # Test 2: Filter Merging
        results.append(await test_filter_merging())
    except Exception as e:
        print_test_result("Filter Merging", False, str(e))
        results.append(False)
    
    try:
        # Test 3: Conversation Context
        results.append(await test_conversation_context())
    except Exception as e:
        print_test_result("Conversation Context", False, str(e))
        results.append(False)
    
    try:
        # Test 4: Refinement Summary
        results.append(await test_refinement_summary())
    except Exception as e:
        print_test_result("Refinement Summary", False, str(e))
        results.append(False)
    
    try:
        # Test 5: Suggestions
        results.append(await test_suggestions())
    except Exception as e:
        print_test_result("Suggestions", False, str(e))
        results.append(False)
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests PASSED!")
        print("\n🎉 Conversational search core functionality is working correctly!")
        print("\n📝 Next Steps:")
        print("   1. Start the API server: uvicorn main:app --reload")
        print("   2. Test with curl (see docs/CONVERSATIONAL_SEARCH.md)")
        print("   3. Or test the full integration with database")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("   Check the errors above for details")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
