import time
import os
from ctx_agent_context import AgentContext
from ctx_job_context import JobContext
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


test_results = []

def quick_test(test_name, actual, expected):
    passed = actual == expected
    status = "PASS" if passed else "FAIL"
    test_results.append({"name": test_name, "status": status, "actual": actual, "expected": expected})
    print(f"[{status}] {test_name}: got '{actual}' | expected '{expected}'")


async def ctx_script(job_ctx: JobContext, agent_ctx: AgentContext):

    driver = agent_ctx.driver
    wait = WebDriverWait(driver, 10)

    test_page = "file://" + os.path.join(os.getcwd(), "index.html")
    driver.get(test_page)
    time.sleep(1)

    # ============================================================ #
    #                        send_keys (input text)
    # ============================================================ #
    nom_input = wait.until(EC.presence_of_element_located((By.ID, "nom")))
    nom_input.clear()
    nom_input.send_keys("hello")
    quick_test("input_text", nom_input.get_attribute("value"), "hello")

    # ============================================================ #
    #                        send_keys (second input)
    # ============================================================ #
    nom2_input = driver.find_element(By.ID, "nom2")
    nom2_input.clear()
    nom2_input.send_keys("world")
    quick_test("input_text_2", nom2_input.get_attribute("value"), "world")

    # ============================================================ #
    #                         find_elements (h1)
    # ============================================================ #
    h1_elements = driver.find_elements(By.TAG_NAME, "h1")
    h1_text = h1_elements[0].text if h1_elements else ""
    quick_test("extract_h1_title", h1_text, "Simple Form")

    # ============================================================ #
    #               select - by value
    # ============================================================ #
    select_element = Select(driver.find_element(By.ID, "pays"))
    select_element.select_by_value("be")
    quick_test("select_by_value", select_element.first_selected_option.get_attribute("value"), "be")

    # ============================================================ #
    #               select - by visible text
    # ============================================================ #
    select_element.select_by_visible_text("Canada")
    quick_test("select_by_text", select_element.first_selected_option.get_attribute("value"), "ca")

    # ============================================================ #
    #               select - by index
    # ============================================================ #
    select_element.select_by_index(1)
    quick_test("select_by_index", select_element.first_selected_option.get_attribute("value"), "fr")

    # ============================================================ #
    #                       click button
    # ============================================================ #
    btn = driver.find_element(By.ID, "btn_click")
    btn.click()
    counter_text = driver.find_element(By.ID, "click_counter").text
    quick_test("click_button", counter_text, "1")

    # ============================================================ #
    #                  click checkbox
    # ============================================================ #
    checkbox = driver.find_element(By.ID, "checkbox_test")
    checkbox.click()
    quick_test("click_checkbox", checkbox.is_selected(), True)

    # ============================================================ #
    #                    wait for element
    # ============================================================ #
    try:
        wait.until(EC.presence_of_element_located((By.ID, "existing_element")))
        quick_test("wait_for_element", "found", "found")
    except Exception:
        quick_test("wait_for_element", "not_found", "found")

    # ============================================================ #
    #                    detect element presence
    # ============================================================ #
    existing = len(driver.find_elements(By.ID, "existing_element")) > 0
    quick_test("detect_existing_element", existing, True)

    missing = len(driver.find_elements(By.ID, "nonexistent_element")) > 0
    quick_test("detect_missing_element", missing, False)

    # ============================================================ #
    #                    execute_script (JS)
    # ============================================================ #
    js_result = driver.execute_script("return 1 + 1")
    quick_test("execute_js_eval", js_result, 2)

    js_title = driver.execute_script("return document.title")
    quick_test("execute_js_title", js_title, "Simple Form")

    # ============================================================ #
    #                    file upload
    # ============================================================ #
    upload_input = driver.find_element(By.ID, "upload_area")
    test_file = os.path.abspath("index.html")
    upload_input.send_keys(test_file)
    upload_value = upload_input.get_attribute("value")
    quick_test("upload_file", upload_value.endswith("index.html"), True)

    # ============================================================ #
    #                    iframe interaction
    # ============================================================ #
    iframe = driver.find_element(By.ID, "test_iframe")
    driver.switch_to.frame(iframe)

    iframe_text = driver.find_element(By.ID, "iframe_text")
    quick_test("iframe_scrape_attribute", iframe_text.get_attribute("data-custom"), "iframe_value")

    iframe_span = driver.find_element(By.CSS_SELECTOR, ".iframe_span")
    quick_test("iframe_scrape_html", "Span in iframe" in iframe_span.get_attribute("innerHTML"), True)

    iframe_btn = driver.find_element(By.ID, "iframe_btn")
    iframe_btn.click()
    iframe_counter = driver.find_element(By.ID, "iframe_counter")
    quick_test("iframe_click_button", iframe_counter.text, "1")

    iframe_input = driver.find_element(By.ID, "iframe_input")
    iframe_input.send_keys("hi")
    quick_test("iframe_send_keys", iframe_input.get_attribute("value"), "hi")

    driver.switch_to.default_content()

    # ============================================================ #
    #                    open new tab
    # ============================================================ #
    original_window = driver.current_window_handle
    driver.execute_script("window.open(arguments[0], '_blank');", test_page)
    time.sleep(1)
    new_handles = [h for h in driver.window_handles if h != original_window]
    driver.switch_to.window(new_handles[0])
    tab_title = driver.title
    quick_test("open_new_tab", tab_title, "Simple Form")
    driver.close()
    driver.switch_to.window(original_window)

    # ============================================================ #
    #                    cookie operations
    # ============================================================ #
    driver.get("https://example.com")
    driver.add_cookie({"name": "selenium_test", "value": "cookie_value_123"})
    cookies = driver.get_cookies()
    cookie_found = any(c["name"] == "selenium_test" and c["value"] == "cookie_value_123" for c in cookies)
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
