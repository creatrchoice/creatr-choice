"""Test conversational search via API endpoints (faster, HTTP-based)."""
import asyncio
import httpx
import json
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, Any


BASE_URL = "http://localhost:8000"
TIMEOUT = 180.0  # 3 minutes for first request (category discovery can be slow)


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_message(role: str, content: str, metadata: Dict[str, Any] = None):
    """Print formatted message."""
    print(f"\n[{role.upper()}]")
    print(f"   Message: {content}")
    if metadata:
        print(f"   Metadata: {json.dumps(metadata, indent=6)}")


def print_response(response_data: Dict[str, Any], show_influencers: bool = False):
    """Print formatted API response."""
    print(f"\n📊 Response:")
    print(f"   Status: {response_data.get('status_code', 'N/A')}")
    if 'data' in response_data:
        data = response_data['data']
        print(f"   Total Results: {data.get('total', 0):,}")
        print(f"   Returned: {len(data.get('influencers', []))}")
        print(f"   Has More: {data.get('has_more', False)}")
        print(f"   Search Time: {data.get('search_time_ms', 0):.2f}ms")
        print(f"   Conversation ID: {data.get('conversation_id', 'N/A')}")
        
        if data.get('applied_filters'):
            print(f"\n   🔍 Applied Filters:")
            filters = data['applied_filters']
            for key, value in filters.items():
                if value:
                    print(f"      - {key}: {value}")
        
        if data.get('refinement_summary'):
            print(f"\n   📝 Refinement: {data['refinement_summary']}")
        
        if data.get('suggestions'):
            print(f"\n   💡 Suggestions:")
            for suggestion in data['suggestions']:
                print(f"      - {suggestion}")
        
        if show_influencers and data.get('influencers'):
            print(f"\n   👥 Sample Influencers (first 2):")
            for i, inf in enumerate(data['influencers'][:2], 1):
                print(f"\n      {i}. {inf.get('display_name', 'N/A')} (@{inf.get('username', 'N/A')})")
                print(f"         Platform: {inf.get('platform', 'N/A')}")
                print(f"         Followers: {inf.get('followers', 0):,}")
                if inf.get('average_views'):
                    print(f"         Avg Views: {inf['average_views']:,}")
                if inf.get('engagement_rate'):
                    print(f"         Engagement: {inf['engagement_rate']:.2f}%")
                if inf.get('profile_url'):
                    print(f"         Profile: {inf['profile_url']}")
                print(f"         Relevance: {inf.get('relevance_score', 0):.3f}")


async def check_server_health(client: httpx.AsyncClient) -> bool:
    """Check if server is running and healthy."""
    try:
        # Try health endpoint first (lightweight)
        response = await client.get(f"{BASE_URL}/health", timeout=10.0)
        if response.status_code == 200:
            print("✅ Server is running and responding")
            return True
    except httpx.ConnectError:
        print(f"❌ Server is not running at {BASE_URL}")
        print("   Please start the server: uvicorn main:app --reload")
        return False
    except httpx.TimeoutException:
        print(f"⚠️  Server is running but not responding (timeout)")
        print("   The server may be stuck or overloaded")
        print("   Try restarting: pkill -f uvicorn && uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"⚠️  Could not verify server: {type(e).__name__}: {str(e)}")
        return False
    return False


async def test_api_endpoint():
    """Test conversational search via API endpoint."""
    print_section("CONVERSATIONAL SEARCH API TEST")
    print(f"Testing endpoint: {BASE_URL}/api/v1/influencers/search/chat")
    print(f"Timeout: {TIMEOUT}s per request")
    
    conversation_id: Optional[str] = None
    test_results = []
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Check server health first
        print("\n🔍 Checking if server is running...")
        if not await check_server_health(client):
            return []
        
        print("\n⏳ Starting tests...")
        print("   Note: First request may take 30-60s (category discovery + NLP analysis)")
        
        # Test 1: Initial Search
        print_section("Test 1: Initial Search")
        print_message("user", "Find fitness influencers")
        print(f"\n⏳ Sending request (timeout: {TIMEOUT}s)...")
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/influencers/search/chat",
                json={
                    "query": "Find fitness influencers",
                    "limit": 5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                conversation_id = data.get("conversation_id")
                
                print_message("assistant", f"Found {data.get('total', 0)} influencers", {
                    "conversation_id": conversation_id,
                    "total": data.get('total', 0),
                    "search_time_ms": data.get('search_time_ms', 0)
                })
                
                print_response({
                    "status_code": response.status_code,
                    "data": data
                }, show_influencers=True)
                
                test_results.append({
                    "test": "Initial Search",
                    "passed": True,
                    "conversation_id": conversation_id,
                    "total_results": data.get('total', 0)
                })
                
                print("\n✅ Test 1 PASSED")
            else:
                print(f"\n❌ Test 1 FAILED: Status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error: {response.text[:500]}")
                test_results.append({
                    "test": "Initial Search",
                    "passed": False,
                    "error": f"Status {response.status_code}"
                })
                return test_results
                
        except httpx.ConnectError as e:
            print(f"\n❌ Test 1 FAILED: Could not connect to {BASE_URL}")
            print(f"   Error: {str(e)}")
            print("   Make sure the server is running: uvicorn main:app --reload")
            test_results.append({
                "test": "Initial Search",
                "passed": False,
                "error": f"Connection failed: {str(e)}"
            })
            return test_results
        except httpx.TimeoutException as e:
            print(f"\n❌ Test 1 FAILED: Request timed out after {TIMEOUT}s")
            print(f"   Error: {str(e)}")
            print("\n   Possible causes:")
            print("   1. Azure OpenAI is slow to respond (check API key/endpoint)")
            print("   2. Azure AI Search is slow (check search service)")
            print("   3. Category discovery is taking too long (first request only)")
            print("   4. Network connectivity issues")
            print(f"\n   💡 Tip: Check server logs for more details")
            test_results.append({
                "test": "Initial Search",
                "passed": False,
                "error": f"Timeout after {TIMEOUT}s"
            })
            return test_results
        except Exception as e:
            print(f"\n❌ Test 1 FAILED: {type(e).__name__}: {str(e)}")
            print(f"   Traceback:")
            traceback.print_exc()
            test_results.append({
                "test": "Initial Search",
                "passed": False,
                "error": f"{type(e).__name__}: {str(e)}"
            })
            return test_results
        
        if not conversation_id:
            print("\n❌ No conversation_id returned")
            return test_results
        
        # Test 2: Refinement - Add City
        print_section("Test 2: Refinement - Add City Filter")
        print_message("user", "Show me only those in Mumbai")
        print(f"\n⏳ Sending request (should be faster, timeout: {TIMEOUT}s)...")
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/influencers/search/chat",
                json={
                    "query": "Show me only those in Mumbai",
                    "conversation_id": conversation_id,
                    "limit": 5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print_message("assistant", f"Found {data.get('total', 0)} influencers in Mumbai", {
                    "total": data.get('total', 0),
                    "search_time_ms": data.get('search_time_ms', 0)
                })
                
                print_response({
                    "status_code": response.status_code,
                    "data": data
                }, show_influencers=True)
                
                # Verify city filter
                city_applied = data.get('applied_filters', {}).get('city') == "Mumbai"
                test_results.append({
                    "test": "Refinement - Add City",
                    "passed": city_applied,
                    "total_results": data.get('total', 0),
                    "city_filter": data.get('applied_filters', {}).get('city')
                })
                
                if city_applied:
                    print("\n✅ Test 2 PASSED - City filter applied")
                else:
                    print(f"\n⚠️  Test 2 WARNING - City filter: {data.get('applied_filters', {}).get('city')}")
            else:
                print(f"\n❌ Test 2 FAILED: Status {response.status_code}")
                print(f"   Error: {response.text[:500]}")
                test_results.append({
                    "test": "Refinement - Add City",
                    "passed": False,
                    "error": f"Status {response.status_code}"
                })
        except httpx.TimeoutException:
            print(f"\n❌ Test 2 FAILED: Request timed out")
            test_results.append({
                "test": "Refinement - Add City",
                "passed": False,
                "error": "Timeout"
            })
        except Exception as e:
            print(f"\n❌ Test 2 FAILED: {type(e).__name__}: {str(e)}")
            test_results.append({
                "test": "Refinement - Add City",
                "passed": False,
                "error": str(e)
            })
        
        # Test 3: Refinement - Add Follower Filter
        print_section("Test 3: Refinement - Add Follower Filter")
        print_message("user", "With more than 100K followers")
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/influencers/search/chat",
                json={
                    "query": "With more than 100K followers",
                    "conversation_id": conversation_id,
                    "limit": 5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print_message("assistant", f"Found {data.get('total', 0)} influencers", {
                    "total": data.get('total', 0)
                })
                
                print_response({
                    "status_code": response.status_code,
                    "data": data
                })
                
                # Verify follower filter
                min_followers = data.get('applied_filters', {}).get('min_followers')
                follower_filter_applied = min_followers and min_followers >= 100000
                
                test_results.append({
                    "test": "Refinement - Add Follower Filter",
                    "passed": follower_filter_applied,
                    "min_followers": min_followers
                })
                
                if follower_filter_applied:
                    print("\n✅ Test 3 PASSED - Follower filter applied")
                else:
                    print(f"\n⚠️  Test 3 WARNING - Min followers: {min_followers}")
            else:
                print(f"\n❌ Test 3 FAILED: Status {response.status_code}")
                test_results.append({
                    "test": "Refinement - Add Follower Filter",
                    "passed": False,
                    "error": f"Status {response.status_code}"
                })
        except Exception as e:
            print(f"\n❌ Test 3 FAILED: {type(e).__name__}: {str(e)}")
            test_results.append({
                "test": "Refinement - Add Follower Filter",
                "passed": False,
                "error": str(e)
            })
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for t in test_results if t.get('passed', False))
    total = len(test_results)
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    print(f"\n📋 Test Details:")
    for result in test_results:
        status = "✅" if result.get('passed', False) else "❌"
        print(f"   {status} {result['test']}")
        if not result.get('passed', False) and 'error' in result:
            print(f"      Error: {result['error']}")
    
    # Conversation Flow Analysis
    print_section("CONVERSATION FLOW ANALYSIS")
    print("\n💬 Messages Sent:")
    print("   1. User: 'Find fitness influencers'")
    print("   2. User: 'Show me only those in Mumbai'")
    print("   3. User: 'With more than 100K followers'")
    
    print("\n🔄 Conversation ID: " + (conversation_id or "Not generated"))
    
    if passed == total and total > 0:
        print("\n✅ All tests PASSED!")
        print("🎉 Conversational search API is working correctly!")
    elif total > 0:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\n💡 Troubleshooting:")
        print("   - Check server logs for errors")
        print("   - Verify Azure services are configured correctly")
        print("   - Check .env file has correct credentials")
    else:
        print("\n❌ No tests completed")
    
    print("=" * 80)
    
    return test_results


async def main():
    """Main test function."""
    print("\n" + "=" * 80)
    print("CONVERSATIONAL SEARCH - API ENDPOINT TEST")
    print("=" * 80)
    print("\nThis test makes HTTP requests to the API endpoint.")
    print("Make sure the server is running: uvicorn main:app --reload")
    print("\nStarting tests...")
    
    try:
        results = await test_api_endpoint()
        return results
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return []
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        traceback.print_exc()
        return []


if __name__ == "__main__":
    results = asyncio.run(main())
    sys.exit(0 if all(r.get('passed', False) for r in results) else 1)
