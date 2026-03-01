import json
import time
from ctx_agent_context import AgentContext
from ctx_job_context import JobContext

from addon.request_modifier_add_custom_header import request_modifier_add_custom_header
from addon.request_modifier_add_user_agent import request_modifier_add_user_agent
from addon.response_modifier_inject_header import response_modifier_inject_header
from addon.retriever_capture_headers import retriever_capture_headers
from addon.retriever_capture_ip import retriever_capture_ip


# ================================================================== #
#                         TEST HELPER                                 #
# ================================================================== #

test_results = []


def quick_test(test_name, actual, expected):
    passed = actual == expected
    status = "PASS" if passed else "FAIL"
    test_results.append({
        "name": test_name,
        "status": status,
        "actual": actual,
        "expected": expected
    })
    print(f"  [{status}] {test_name}: got '{actual}' | expected '{expected}'")


# ================================================================== #
#                         MAIN TEST SUITE                             #
# ================================================================== #

async def ctx_script(job_ctx: JobContext, agent_ctx: AgentContext):

    print("=" * 60)
    print("PROXY FEATURE E2E TEST SUITE")
    print("=" * 60)

    # ============================================================ #
    #  PHASE 1: Register modifiers & retrievers, then launch proxy  #
    # ============================================================ #

    # Request modifiers
    agent_ctx.proxy_manager.add_request_modifier(request_modifier_add_custom_header)
    agent_ctx.proxy_manager.add_request_modifier(request_modifier_add_user_agent)

    # Response modifier
    agent_ctx.proxy_manager.add_modifier(response_modifier_inject_header)

    # Data retrievers
    agent_ctx.proxy_manager.add_retriever("captured_headers", retriever_capture_headers)
    agent_ctx.proxy_manager.add_retriever("captured_ip", retriever_capture_ip)

    # Launch proxy with all addons registered
    agent_ctx.launch_proxy()
    time.sleep(1)

    # ============================================================ #
    #  TEST 1: Basic proxy + upstream IP                            #
    #  Verify traffic goes through mitmproxy and upstream proxy     #
    # ============================================================ #
    print("\n--- Test 1: Basic proxy operation + upstream IP ---")

    tab = await agent_ctx.browser.get("https://httpbin.org/ip")
    time.sleep(2)

    page_text = await tab.xinject_js("document.body.innerText")
    body_text = page_text[0].value

    try:
        ip_json = json.loads(body_text)
        ip_before = ip_json.get("origin", "")
    except Exception:
        ip_before = ""

    has_origin = bool(ip_before)
    quick_test("basic_proxy_operation", has_origin, True)
    print(f"  IP via upstream proxy: {ip_before}")

    # ============================================================ #
    #  TEST 2: Request modifiers - custom header injection          #
    #  httpbin.org/headers echoes back all request headers          #
    # ============================================================ #
    print("\n--- Test 2: Request modifiers (custom headers) ---")

    tab = await agent_ctx.browser.get("https://httpbin.org/headers")
    time.sleep(2)

    headers_text = await tab.xinject_js("document.body.innerText")
    headers_body = headers_text[0].value

    try:
        headers_json = json.loads(headers_body)
        received_headers = headers_json.get("headers", {})
    except Exception:
        received_headers = {}

    # 2a: Custom header injected by request_modifier_add_custom_header
    custom_header_value = received_headers.get("X-Armada-Test", "")
    quick_test("request_modifier_custom_header", custom_header_value, "proxy-e2e-header-value")

    # 2b: User-Agent overridden by request_modifier_add_user_agent
    ua_value = received_headers.get("User-Agent", "")
    quick_test("request_modifier_user_agent", ua_value, "ArmadaProxyTest/1.0")

    # ============================================================ #
    #  TEST 3: Data retrievers                                      #
    #  Verify data was captured into named queues                   #
    # ============================================================ #
    print("\n--- Test 3: Data retrievers ---")

    retrieved_headers = agent_ctx.proxy_manager.retrieve("captured_headers")
    has_headers_key = isinstance(retrieved_headers, dict) and "headers" in retrieved_headers
    quick_test("data_retriever_captured_headers", has_headers_key, True)

    retrieved_ip = agent_ctx.proxy_manager.retrieve("captured_ip")
    has_origin_key = isinstance(retrieved_ip, dict) and "origin" in retrieved_ip
    quick_test("data_retriever_captured_ip", has_origin_key, True)

    # ============================================================ #
    #  TEST 4: Data counting (get_data_count)                       #
    #  Cumulative bytes transferred should be > 0                   #
    # ============================================================ #
    print("\n--- Test 4: Data counting ---")

    data_count = agent_ctx.proxy_manager.get_data_count()
    count_is_positive = isinstance(data_count, int) and data_count > 0
    quick_test("data_count_positive", count_is_positive, True)
    print(f"  Cumulative data transferred: {data_count} bytes")

    # ============================================================ #
    #  TEST 5: Response modifier                                    #
    #  Verify X-Armada-Modified header is injected in responses     #
    #  The modifier prints response headers to console (see output) #
    # ============================================================ #
    print("\n--- Test 5: Response modifier ---")
    print("  Navigating to httpbin.org/get to trigger response modifier...")

    tab = await agent_ctx.browser.get("https://httpbin.org/get")
    time.sleep(2)

    # The response modifier prints all response headers for httpbin requests
    # including the injected "X-Armada-Modified: true" (visible in console above)
    modifier_registered = response_modifier_inject_header in agent_ctx.proxy_manager.modifiers_array
    quick_test("response_modifier_registered", modifier_registered, True)

    # ============================================================ #
    #  TEST 6: Proxy switching mid-run + IP change verification     #
    #  Switch upstream proxy, verify IP changes and addons persist  #
    # ============================================================ #
    print("\n--- Test 6: Proxy switching mid-run ---")
    print(f"  IP before switch: {ip_before}")

    # Switch proxy (kills mitmproxy subprocess, fetches new upstream, relaunches)
    agent_ctx.proxy_manager.switch_upstream_proxy()
    time.sleep(1.5)

    # Get new IP after switch
    tab = await agent_ctx.browser.get("https://httpbin.org/ip")
    time.sleep(2)

    page_text_after = await tab.xinject_js("document.body.innerText")
    body_text_after = page_text_after[0].value

    try:
        ip_json_after = json.loads(body_text_after)
        ip_after = ip_json_after.get("origin", "")
    except Exception:
        ip_after = ""

    print(f"  IP after switch: {ip_after}")

    # 6a: Proxy is still functional after switch
    has_ip_after = bool(ip_after)
    quick_test("proxy_switch_functional", has_ip_after, True)

    # 6b: IP changed after switch (new upstream proxy)
    ip_changed = ip_before != ip_after and bool(ip_after)
    quick_test("proxy_switch_ip_changed", ip_changed, True)

    # 6c: Request modifiers persist after switch
    tab = await agent_ctx.browser.get("https://httpbin.org/headers")
    time.sleep(2)

    headers_text_after = await tab.xinject_js("document.body.innerText")
    headers_body_after = headers_text_after[0].value

    try:
        headers_json_after = json.loads(headers_body_after)
        received_headers_after = headers_json_after.get("headers", {})
    except Exception:
        received_headers_after = {}

    custom_header_after = received_headers_after.get("X-Armada-Test", "")
    quick_test("proxy_switch_modifiers_persist", custom_header_after, "proxy-e2e-header-value")

    ua_after = received_headers_after.get("User-Agent", "")
    quick_test("proxy_switch_user_agent_persists", ua_after, "ArmadaProxyTest/1.0")

    # 6d: Data counting works on new proxy instance
    data_count_after = agent_ctx.proxy_manager.get_data_count()
    count_after_positive = isinstance(data_count_after, int) and data_count_after > 0
    quick_test("proxy_switch_data_count_works", count_after_positive, True)
    print(f"  Data count after switch: {data_count_after}")

    # ============================================================ #
    #                      RESULTS SUMMARY                          #
    # ============================================================ #
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    passed = sum(1 for t in test_results if t["status"] == "PASS")
    failed = sum(1 for t in test_results if t["status"] == "FAIL")
    print(f"Total: {len(test_results)} | Passed: {passed} | Failed: {failed}")
    if failed > 0:
        print("\nFailed tests:")
        for t in test_results:
            if t["status"] == "FAIL":
                print(f"  - {t['name']}: got '{t['actual']}' | expected '{t['expected']}'")
    print("=" * 60)
