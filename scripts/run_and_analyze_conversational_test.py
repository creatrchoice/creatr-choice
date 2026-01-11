"""Run conversational search test and provide detailed analysis."""
import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.conversation_service import ConversationService
from app.models.conversation import ChatSearchRequest


class TestAnalyzer:
    """Analyze conversational search test results."""
    
    def __init__(self):
        self.test_results = []
        self.conversation_flow = []
    
    def record_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Record a message in the conversation flow."""
        self.conversation_flow.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
    
    def record_test_result(self, test_name: str, passed: bool, details: Dict[str, Any]):
        """Record test result."""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def generate_analysis_report(self) -> str:
        """Generate detailed analysis report."""
        report = []
        report.append("=" * 80)
        report.append("CONVERSATIONAL SEARCH TEST - DETAILED ANALYSIS")
        report.append("=" * 80)
        report.append(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Tests: {len(self.test_results)}")
        report.append(f"Passed: {sum(1 for t in self.test_results if t['passed'])}")
        report.append(f"Failed: {sum(1 for t in self.test_results if not t['passed'])}")
        
        # Conversation Flow Analysis
        report.append("\n" + "=" * 80)
        report.append("CONVERSATION FLOW ANALYSIS")
        report.append("=" * 80)
        
        for i, msg in enumerate(self.conversation_flow, 1):
            report.append(f"\n[{i}] {msg['role'].upper()}:")
            report.append(f"    Message: {msg['content']}")
            if msg['metadata']:
                report.append(f"    Metadata: {json.dumps(msg['metadata'], indent=6)}")
        
        # Test Results Analysis
        report.append("\n" + "=" * 80)
        report.append("TEST RESULTS ANALYSIS")
        report.append("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            report.append(f"\n{status}: {result['test']}")
            
            details = result['details']
            if 'query' in details:
                report.append(f"   Query: {details['query']}")
            if 'conversation_id' in details:
                report.append(f"   Conversation ID: {details['conversation_id']}")
            if 'total_results' in details:
                report.append(f"   Total Results: {details['total_results']:,}")
            if 'applied_filters' in details:
                report.append(f"   Applied Filters: {json.dumps(details['applied_filters'], indent=6)}")
            if 'refinement_summary' in details:
                report.append(f"   Refinement: {details['refinement_summary']}")
            if 'suggestions' in details:
                report.append(f"   Suggestions: {', '.join(details['suggestions'])}")
            if 'error' in details:
                report.append(f"   Error: {details['error']}")
        
        # Overall Analysis
        report.append("\n" + "=" * 80)
        report.append("OVERALL ANALYSIS")
        report.append("=" * 80)
        
        # Analyze conversation progression
        if len(self.conversation_flow) >= 2:
            report.append("\n📊 Conversation Progression:")
            user_messages = [m for m in self.conversation_flow if m['role'] == 'user']
            assistant_responses = [m for m in self.conversation_flow if m['role'] == 'assistant']
            
            report.append(f"   - User Messages: {len(user_messages)}")
            report.append(f"   - Assistant Responses: {len(assistant_responses)}")
            
            if len(user_messages) > 1:
                report.append("\n   Refinement Pattern:")
                for i, msg in enumerate(user_messages, 1):
                    report.append(f"      {i}. {msg['content']}")
        
        # Filter Evolution Analysis
        report.append("\n🔍 Filter Evolution:")
        filter_evolution = []
        for result in self.test_results:
            if result['passed'] and 'applied_filters' in result['details']:
                filters = result['details']['applied_filters']
                filter_evolution.append({
                    "test": result['test'],
                    "filters": filters
                })
        
        if filter_evolution:
            report.append("   How filters evolved through the conversation:")
            for i, evo in enumerate(filter_evolution, 1):
                report.append(f"\n   Step {i}: {evo['test']}")
                filters = evo['filters']
                if filters:
                    for key, value in filters.items():
                        if value:
                            report.append(f"      - {key}: {value}")
        
        # Performance Analysis
        report.append("\n⚡ Performance Analysis:")
        search_times = []
        for result in self.test_results:
            if result['passed'] and 'search_time_ms' in result['details']:
                search_times.append(result['details']['search_time_ms'])
        
        if search_times:
            avg_time = sum(search_times) / len(search_times)
            max_time = max(search_times)
            min_time = min(search_times)
            report.append(f"   - Average Search Time: {avg_time:.2f}ms")
            report.append(f"   - Min Search Time: {min_time:.2f}ms")
            report.append(f"   - Max Search Time: {max_time:.2f}ms")
        
        # Success Rate Analysis
        report.append("\n📈 Success Rate:")
        total = len(self.test_results)
        passed = sum(1 for t in self.test_results if t['passed'])
        success_rate = (passed / total * 100) if total > 0 else 0
        report.append(f"   - Success Rate: {success_rate:.1f}% ({passed}/{total})")
        
        # Recommendations
        report.append("\n💡 Recommendations:")
        if success_rate == 100:
            report.append("   ✅ All tests passed! The conversational search is working correctly.")
        else:
            failed_tests = [t for t in self.test_results if not t['passed']]
            report.append(f"   ⚠️  {len(failed_tests)} test(s) failed. Review errors above.")
        
        if search_times and max(search_times) > 1000:
            report.append("   ⚠️  Some searches took longer than 1 second. Consider optimization.")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)


async def run_tests_with_analysis():
    """Run tests and generate analysis."""
    analyzer = TestAnalyzer()
    service = ConversationService()
    conversation_id: Optional[str] = None
    
    print("\n" + "=" * 80)
    print("RUNNING CONVERSATIONAL SEARCH TESTS")
    print("=" * 80)
    
    # Test 1: Initial Search
    print("\n[Test 1] Initial Search: 'Find fitness influencers'")
    analyzer.record_message("user", "Find fitness influencers")
    
    try:
        request1 = ChatSearchRequest(query="Find fitness influencers", limit=5)
        response1 = await service.search_chat(request1)
        conversation_id = response1.conversation_id
        
        analyzer.record_message("assistant", f"Found {response1.total} influencers", {
            "total": response1.total,
            "conversation_id": conversation_id,
            "search_time_ms": response1.search_time_ms
        })
        
        analyzer.record_test_result("Initial Search", True, {
            "query": "Find fitness influencers",
            "conversation_id": conversation_id,
            "total_results": response1.total,
            "applied_filters": response1.applied_filters.model_dump(exclude_none=True) if response1.applied_filters else {},
            "refinement_summary": response1.refinement_summary,
            "suggestions": response1.suggestions or [],
            "search_time_ms": response1.search_time_ms
        })
        
        print(f"✅ Found {response1.total} influencers")
        
    except Exception as e:
        analyzer.record_test_result("Initial Search", False, {
            "query": "Find fitness influencers",
            "error": str(e)
        })
        print(f"❌ Failed: {e}")
        return analyzer.generate_analysis_report()
    
    if not conversation_id:
        print("❌ No conversation_id returned")
        return analyzer.generate_analysis_report()
    
    # Test 2: Refinement - Add City
    print("\n[Test 2] Refinement: 'Show me only those in Mumbai'")
    analyzer.record_message("user", "Show me only those in Mumbai")
    
    try:
        request2 = ChatSearchRequest(
            query="Show me only those in Mumbai",
            conversation_id=conversation_id,
            limit=5
        )
        response2 = await service.search_chat(request2)
        
        analyzer.record_message("assistant", f"Found {response2.total} influencers in Mumbai", {
            "total": response2.total,
            "search_time_ms": response2.search_time_ms
        })
        
        analyzer.record_test_result("Refinement - Add City", True, {
            "query": "Show me only those in Mumbai",
            "conversation_id": conversation_id,
            "total_results": response2.total,
            "applied_filters": response2.applied_filters.model_dump(exclude_none=True) if response2.applied_filters else {},
            "refinement_summary": response2.refinement_summary,
            "suggestions": response2.suggestions or [],
            "search_time_ms": response2.search_time_ms
        })
        
        print(f"✅ Found {response2.total} influencers in Mumbai")
        
    except Exception as e:
        analyzer.record_test_result("Refinement - Add City", False, {
            "query": "Show me only those in Mumbai",
            "error": str(e)
        })
        print(f"❌ Failed: {e}")
    
    # Test 3: Refinement - Add Follower Filter
    print("\n[Test 3] Refinement: 'With more than 100K followers'")
    analyzer.record_message("user", "With more than 100K followers")
    
    try:
        request3 = ChatSearchRequest(
            query="With more than 100K followers",
            conversation_id=conversation_id,
            limit=5
        )
        response3 = await service.search_chat(request3)
        
        analyzer.record_message("assistant", f"Found {response3.total} influencers", {
            "total": response3.total,
            "search_time_ms": response3.search_time_ms
        })
        
        analyzer.record_test_result("Refinement - Add Follower Filter", True, {
            "query": "With more than 100K followers",
            "conversation_id": conversation_id,
            "total_results": response3.total,
            "applied_filters": response3.applied_filters.model_dump(exclude_none=True) if response3.applied_filters else {},
            "refinement_summary": response3.refinement_summary,
            "suggestions": response3.suggestions or [],
            "search_time_ms": response3.search_time_ms
        })
        
        print(f"✅ Found {response3.total} influencers with >100K followers")
        
    except Exception as e:
        analyzer.record_test_result("Refinement - Add Follower Filter", False, {
            "query": "With more than 100K followers",
            "error": str(e)
        })
        print(f"❌ Failed: {e}")
    
    # Generate and print analysis
    print("\n" + "=" * 80)
    print("GENERATING ANALYSIS REPORT...")
    print("=" * 80)
    
    report = analyzer.generate_analysis_report()
    print(report)
    
    # Save to file
    with open("/tmp/conversational_test_analysis.txt", "w") as f:
        f.write(report)
    
    print("\n📄 Full analysis saved to: /tmp/conversational_test_analysis.txt")
    
    return report


if __name__ == "__main__":
    try:
        report = asyncio.run(run_tests_with_analysis())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
