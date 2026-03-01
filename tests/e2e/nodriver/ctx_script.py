import os
import time
from ctx_agent_context import AgentContext
from ctx_job_context import JobContext
from nodriver import cdp


test_results = []

def quick_test(test_name, actual, expected):
    passed = actual == expected
    status = "PASS" if passed else "FAIL"
    test_results.append({"name": test_name, "status": status, "actual": actual, "expected": expected})
    print(f"[{status}] {test_name}: got '{actual}' | expected '{expected}'")


async def ctx_script(job_ctx: JobContext, agent_ctx: AgentContext):

    test_page = "file://" + os.path.join(os.getcwd(), "index.html")
    tab = await agent_ctx.browser.get(test_page)
    time.sleep(1)

    # ============================================================ #
    #                        send_keys (input text)
    # ============================================================ #
    nom_input = await tab.select("#nom")
    await nom_input.send_keys("hello")
    raw_value = await tab.evaluate('document.querySelector("#nom").value')
    quick_test("input_text", raw_value, "hello")

    # ============================================================ #
    #                        send_keys (second input)
    # ============================================================ #
    nom2_input = await tab.select("#nom2")
    await nom2_input.send_keys("world")
    raw_value2 = await tab.evaluate('document.querySelector("#nom2").value')
    quick_test("input_text_2", raw_value2, "world")

    # ============================================================ #
    #                         find_all (h1)
    # ============================================================ #
    h1_elements = await tab.find_all("h1")
    h1_text = h1_elements[0].text if h1_elements else ""
    quick_test("extract_h1_title", h1_text, "Simple Form")

    # ============================================================ #
    #               select - by value
    # ============================================================ #
    await tab.evaluate('document.querySelector("#pays").value = "be"')
    await tab.evaluate('document.querySelector("#pays").dispatchEvent(new Event("change"))')
    select_value = await tab.evaluate('document.querySelector("#pays").value')
    quick_test("select_by_value", select_value, "be")

    # ============================================================ #
    #               select - by visible text
    # ============================================================ #
    await tab.evaluate('''
        var sel = document.querySelector("#pays");
        for (var i = 0; i < sel.options.length; i++) {
            if (sel.options[i].text === "Canada") { sel.selectedIndex = i; break; }
        }
        sel.dispatchEvent(new Event("change"));
    ''')
    select_value2 = await tab.evaluate('document.querySelector("#pays").value')
    quick_test("select_by_text", select_value2, "ca")

    # ============================================================ #
    #               select - by index
    # ============================================================ #
    await tab.evaluate('document.querySelector("#pays").selectedIndex = 1; document.querySelector("#pays").dispatchEvent(new Event("change"))')
    select_value3 = await tab.evaluate('document.querySelector("#pays").value')
    quick_test("select_by_index", select_value3, "fr")

    # ============================================================ #
    #                       click button
    # ============================================================ #
    btn = await tab.select("#btn_click")
    await btn.click()
    counter_text = await tab.evaluate('document.querySelector("#click_counter").innerText')
    quick_test("click_button", counter_text, "1")

    # ============================================================ #
    #                  click checkbox
    # ============================================================ #
    checkbox = await tab.select("#checkbox_test")
    await checkbox.click()
    is_checked = await tab.evaluate('document.querySelector("#checkbox_test").checked')
    quick_test("click_checkbox", is_checked, True)

    # ============================================================ #
    #                    wait for element
    # ============================================================ #
    try:
        await tab.find("#existing_element", timeout=5)
        quick_test("wait_for_element", "found", "found")
    except Exception:
        quick_test("wait_for_element", "not_found", "found")

    # ============================================================ #
    #                    detect element presence
    # ============================================================ #
    existing = await tab.evaluate('document.querySelector("#existing_element") !== null')
    quick_test("detect_existing_element", existing, True)

    missing = await tab.evaluate('document.querySelector("#nonexistent_element") !== null')
    quick_test("detect_missing_element", missing, False)

    # ============================================================ #
    #                    evaluate (JS)
    # ============================================================ #
    js_result = await tab.evaluate("1 + 1")
    quick_test("execute_js_eval", js_result, 2)

    js_title = await tab.evaluate("document.title")
    quick_test("execute_js_title", js_title, "Simple Form")

    # ============================================================ #
    #                    file upload
    # ============================================================ #
    test_file = os.path.abspath("index.html")
    upload_node = await tab.select("#upload_area")
    await upload_node.send_file(test_file)
    upload_value = await tab.evaluate('document.querySelector("#upload_area").value')
    quick_test("upload_file", upload_value.endswith("index.html"), True)

    # ============================================================ #
    #                    iframe interaction
    # ============================================================ #
    iframe_attr = await tab.evaluate('document.querySelector("#test_iframe").contentDocument.querySelector("#iframe_text").getAttribute("data-custom")')
    quick_test("iframe_scrape_attribute", iframe_attr, "iframe_value")

    iframe_html = await tab.evaluate('document.querySelector("#test_iframe").contentDocument.querySelector(".iframe_span").innerHTML')
    quick_test("iframe_scrape_html", "Span in iframe" in iframe_html, True)

    await tab.evaluate('document.querySelector("#test_iframe").contentDocument.querySelector("#iframe_btn").click()')
    iframe_counter = await tab.evaluate('document.querySelector("#test_iframe").contentDocument.querySelector("#iframe_counter").innerText')
    quick_test("iframe_click_button", iframe_counter, "1")

    await tab.evaluate('''
        var input = document.querySelector("#test_iframe").contentDocument.querySelector("#iframe_input");
        input.value = "hi";
        input.dispatchEvent(new Event("input"));
    ''')
    iframe_input_value = await tab.evaluate('document.querySelector("#test_iframe").contentDocument.querySelector("#iframe_input").value')
    quick_test("iframe_send_keys", iframe_input_value, "hi")

    # ============================================================ #
    #                    open new tab
    # ============================================================ #
    tab2 = await agent_ctx.browser.get(test_page, new_tab=True)
    time.sleep(1)
    tab2_title = await tab2.evaluate("document.title")
    quick_test("open_new_tab", tab2_title, "Simple Form")
    await tab2.close()
    time.sleep(0.5)

    # ============================================================ #
    #                    cookie operations
    # ============================================================ #
    await tab.evaluate('document.cookie = "nodriver_test=cookie_value_123; path=/"')
    cookie_str = await tab.evaluate('document.cookie')
    cookie_found = "nodriver_test=cookie_value_123" in cookie_str
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
