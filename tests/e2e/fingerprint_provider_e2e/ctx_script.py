import json
from ctx_agent_context import AgentContext
from ctx_job_context import JobContext


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
    print("FINGERPRINT PROVIDER E2E TEST SUITE")
    print("=" * 60)

    # ============================================================ #
    #  TEST 1: Basic fingerprint retrieval                          #
    #  Verify get_fingerprint() returns a non-empty response        #
    # ============================================================ #
    print("\n--- Test 1: Basic fingerprint retrieval ---")

    fingerprint = agent_ctx.fingerprint_manager.get_fingerprint()
    is_non_empty = fingerprint is not None and len(str(fingerprint)) > 0
    quick_test("basic_fingerprint_retrieval", is_non_empty, True)
    print(f"  Response length: {len(str(fingerprint))} chars")

    # ============================================================ #
    #  TEST 2: Fingerprint with desired User-Agent                  #
    #  Verify get_fingerprint() accepts additional_data parameter   #
    # ============================================================ #
    print("\n--- Test 2: Fingerprint with desired User-Agent ---")

    desired_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    fingerprint_with_ua = agent_ctx.fingerprint_manager.get_fingerprint(
        additional_data={"desired_ua": desired_ua}
    )
    has_response = fingerprint_with_ua is not None and len(str(fingerprint_with_ua)) > 0
    quick_test("fingerprint_with_desired_ua", has_response, True)
    print(f"  Response length: {len(str(fingerprint_with_ua))} chars")

    # ============================================================ #
    #  TEST 3: Fingerprint response is valid                        #
    #  Verify the response can be parsed / is a valid string        #
    # ============================================================ #
    print("\n--- Test 3: Fingerprint response validity ---")

    is_string = isinstance(fingerprint_with_ua, str)
    quick_test("fingerprint_is_string", is_string, True)

    # ============================================================ #
    #  TEST 4: Config values are applied                            #
    #  Verify the manager parsed the config correctly               #
    # ============================================================ #
    print("\n--- Test 5: Config parsing ---")

    fm = agent_ctx.fingerprint_manager
    quick_test("config_antibot_vendor", fm.antibot_vendor, "arkose")
    quick_test("config_website", fm.website, "X")
    print(f"  Collection date: {fm.collection_date_year}-{fm.collection_date_month}-{fm.collection_date_day}")

    # ============================================================ #
    #  TEST 5: Fingerprint with different User-Agent                #
    #  Verify different UA produces different fingerprint           #
    # ============================================================ #
    print("\n--- Test 6: Different User-Agent produces different fingerprint ---")

    ua_chrome = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    ua_firefox = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0"

    fp_chrome = agent_ctx.fingerprint_manager.get_fingerprint(
        additional_data={"desired_ua": ua_chrome}
    )
    fp_firefox = agent_ctx.fingerprint_manager.get_fingerprint(
        additional_data={"desired_ua": ua_firefox}
    )
    different_ua_different_fp = fp_chrome != fp_firefox
    quick_test("different_ua_different_fingerprint", different_ua_different_fp, True)

    # ============================================================ #
    #  TEST 6: Multiple sequential calls                            #
    #  Verify the service handles multiple rapid requests           #
    # ============================================================ #
    print("\n--- Test 7: Multiple sequential calls ---")

    all_ok = True
    for i in range(5):
        fp = agent_ctx.fingerprint_manager.get_fingerprint(
            additional_data={"desired_ua": ua_chrome}
        )
        if fp is None or len(str(fp)) == 0:
            all_ok = False
            break
    quick_test("multiple_sequential_calls", all_ok, True)

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
