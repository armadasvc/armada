import os
from ctx_agent_context import AgentContext
from ctx_job_context import JobContext


test_results = []

def quick_test(test_name, actual, expected):
    passed = actual == expected
    status = "PASS" if passed else "FAIL"
    test_results.append({"name": test_name, "status": status, "actual": actual, "expected": expected})
    print(f"[{status}] {test_name}: got '{actual}' | expected '{expected}'")


async def ctx_script(job_ctx: JobContext, agent_ctx: AgentContext):

    page = agent_ctx.page

    test_page = "file://" + os.path.join(os.getcwd(), "index.html")
    await page.goto(test_page)
    await page.wait_for_load_state("domcontentloaded")

    # ============================================================ #
    #                        fill (input text)
    # ============================================================ #
    await page.fill("#nom", "hello")
    nom_value = await page.input_value("#nom")
    quick_test("input_text", nom_value, "hello")

    # ============================================================ #
    #                        fill (second input)
    # ============================================================ #
    await page.fill("#nom2", "world")
    nom2_value = await page.input_value("#nom2")
    quick_test("input_text_2", nom2_value, "world")

    # ============================================================ #
    #                         query_selector_all (h1)
    # ============================================================ #
    h1_text = await page.locator("h1").first.inner_text()
    quick_test("extract_h1_title", h1_text, "Simple Form")

    # ============================================================ #
    #               select - by value
    # ============================================================ #
    await page.select_option("#pays", value="be")
    select_value = await page.input_value("#pays")
    quick_test("select_by_value", select_value, "be")

    # ============================================================ #
    #               select - by label (visible text)
    # ============================================================ #
    await page.select_option("#pays", label="Canada")
    select_value2 = await page.input_value("#pays")
    quick_test("select_by_text", select_value2, "ca")

    # ============================================================ #
    #               select - by index
    # ============================================================ #
    await page.select_option("#pays", index=1)
    select_value3 = await page.input_value("#pays")
    quick_test("select_by_index", select_value3, "fr")

    # ============================================================ #
    #                       click button
    # ============================================================ #
    await page.click("#btn_click")
    counter_text = await page.inner_text("#click_counter")
    quick_test("click_button", counter_text, "1")

    # ============================================================ #
    #                  click checkbox
    # ============================================================ #
    await page.click("#checkbox_test")
    is_checked = await page.is_checked("#checkbox_test")
    quick_test("click_checkbox", is_checked, True)

    # ============================================================ #
    #                    wait for element
    # ============================================================ #
    try:
        await page.wait_for_selector("#existing_element", timeout=5000)
        quick_test("wait_for_element", "found", "found")
    except Exception:
        quick_test("wait_for_element", "not_found", "found")

    # ============================================================ #
    #                    detect element presence
    # ============================================================ #
    existing_count = await page.locator("#existing_element").count()
    quick_test("detect_existing_element", existing_count > 0, True)

    missing_count = await page.locator("#nonexistent_element").count()
    quick_test("detect_missing_element", missing_count > 0, False)

    # ============================================================ #
    #                    evaluate (JS)
    # ============================================================ #
    js_result = await page.evaluate("1 + 1")
    quick_test("execute_js_eval", js_result, 2)

    js_title = await page.evaluate("document.title")
    quick_test("execute_js_title", js_title, "Simple Form")

    # ============================================================ #
    #                    file upload
    # ============================================================ #
    test_file = os.path.abspath("index.html")
    await page.set_input_files("#upload_area", test_file)
    upload_value = await page.input_value("#upload_area")
    quick_test("upload_file", upload_value.endswith("index.html"), True)

    # ============================================================ #
    #                    iframe interaction
    # ============================================================ #
    iframe_locator = page.frame_locator("#test_iframe")

    iframe_attr = await iframe_locator.locator("#iframe_text").get_attribute("data-custom")
    quick_test("iframe_scrape_attribute", iframe_attr, "iframe_value")

    iframe_html = await iframe_locator.locator(".iframe_span").inner_html()
    quick_test("iframe_scrape_html", "Span in iframe" in iframe_html, True)

    await iframe_locator.locator("#iframe_btn").click()
    iframe_counter = await iframe_locator.locator("#iframe_counter").inner_text()
    quick_test("iframe_click_button", iframe_counter, "1")

    await iframe_locator.locator("#iframe_input").fill("hi")
    iframe_input_value = await iframe_locator.locator("#iframe_input").input_value()
    quick_test("iframe_send_keys", iframe_input_value, "hi")

    # ============================================================ #
    #                    open new tab
    # ============================================================ #
    new_page = await agent_ctx.browser.new_page()
    await new_page.goto(test_page)
    await new_page.wait_for_load_state("domcontentloaded")
    tab_title = await new_page.title()
    quick_test("open_new_tab", tab_title, "Simple Form")
    await new_page.close()

    # ============================================================ #
    #                    cookie operations
    # ============================================================ #
    await page.goto("https://example.com")
    await agent_ctx.browser.contexts[0].add_cookies([
        {"name": "playwright_test", "value": "cookie_value_123", "url": "https://example.com"}
    ])
    cookies = await agent_ctx.browser.contexts[0].cookies()
    cookie_found = any(c["name"] == "playwright_test" and c["value"] == "cookie_value_123" for c in cookies)
    quick_test("cookie_set_and_get", cookie_found, True)

    # ============================================================ #
    #                     RESULTS SUMMARY
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
