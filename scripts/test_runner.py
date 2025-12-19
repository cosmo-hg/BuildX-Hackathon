import requests
import time
import json

BASE_URL = "http://localhost:8080"
GA4_PROPERTY_ID = "YOUR_GA4_PROPERTY_ID" # Will use placeholder if not set, handled by agent config

test_cases = [
    # Tier 1
    {
        "tier": "Tier 1: Daily Metrics Breakdown",
        "query": "Give me a daily breakdown of page views, users, and sessions for the /pricing page over the last 14 days. Summarize any noticeable trends.",
        "propertyId": GA4_PROPERTY_ID
    },
    {
        "tier": "Tier 1: Traffic Source Analysis",
        "query": "What are the top 5 traffic sources driving users to the pricing page in the last 30 days?",
        "propertyId": GA4_PROPERTY_ID
    },
    {
        "tier": "Tier 1: Calculated Insight",
        "query": "Calculate the average daily page views for the homepage over the last 30 days. Compare it to the previous 30-day period and explain whether traffic is increasing or decreasing.",
        "propertyId": GA4_PROPERTY_ID
    },
    
    # Tier 2
    {
        "tier": "Tier 2: Conditional Filtering",
        "query": "Which URLs do not use HTTPS and have title tags longer than 60 characters?",
        "propertyId": None
    },
    {
        "tier": "Tier 2: Indexability Overview",
        "query": "Group all pages by indexability status and provide a count for each group with a brief explanation.",
        "propertyId": None
    },
    {
        "tier": "Tier 2: Calculated SEO Insight",
        "query": "Calculate the percentage of indexable pages on the site. Based on this number, assess whether the site’s technical SEO health is good, average, or poor.",
        "propertyId": None
    },

    # Tier 3
    {
        "tier": "Tier 3: Analytics + SEO Fusion",
        "query": "What are the top 10 pages by page views in the last 14 days, and what are their corresponding title tags?",
        "propertyId": GA4_PROPERTY_ID
    },
    {
        "tier": "Tier 3: High Traffic, High Risk Pages",
        "query": "Which pages are in the top 20% by views but have missing or duplicate meta descriptions? Explain the SEO risk.",
        "propertyId": GA4_PROPERTY_ID
    },
    {
        "tier": "Tier 3: Cross-Agent JSON Output",
        "query": "Return the top 5 pages by views along with their title tags and indexability status in JSON format.",
        "propertyId": GA4_PROPERTY_ID
    }
]

def run_tests():
    print(f"Running comprehensive test suite against {BASE_URL}...")
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"TEST COMPONENT: {test['tier']}")
        print(f"QUERY: {test['query']}")
        print(f"{'-'*60}")
        
        payload = {"query": test["query"]}
        if test["propertyId"]:
            payload["propertyId"] = test["propertyId"]

        try:
            start = time.time()
            response = requests.post(f"{BASE_URL}/query", json=payload)
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ STATUS: 200 OK ({duration:.2f}s)")
                print(f"AGENT: {data.get('agent_used')}")
                print(f"ANSWER:\n{data.get('answer')}")
                # Optional: print data snippet if needed
                # print(f"RAW DATA: {json.dumps(data.get('data'), indent=2)[:500]}...")
            else:
                print(f"❌ STATUS: {response.status_code}")
                print(f"ERROR: {response.text}")
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
        
        # Small delay to avoid hitting rate limits too hard with sequential queries
        time.sleep(1)

if __name__ == "__main__":
    run_tests()
