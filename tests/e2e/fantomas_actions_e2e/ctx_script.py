import asyncio
from ctx_agent_context import AgentContext
from ctx_job_context import JobContext
import time
import os

test_results = []

def quick_test(test_name, actual, expected):
    passed = actual == expected
    status = "PASS" if passed else "FAIL"
    test_results.append({"name": test_name, "status": status, "actual": actual, "expected": expected})
    print(f"[{status}] {test_name}: got '{actual}' | expected '{expected}'")


async def ctx_script(job_ctx: JobContext, agent_ctx: AgentContext):

    tab = await agent_ctx.browser.get("file://"+os.getcwd()+"/index.html")
    time.sleep(1)

    # ============================================================ #
    #                        xupload_file
    # ============================================================ #
    await tab.xupload_file(['input[type="file"]',0],os.getcwd()+"/to_be_uploaded.txt")
    raw_upload_file_value = await tab.xinject_js('document.querySelector("input#upload_area").value')
    upload_file_value = raw_upload_file_value[0].value[12:]
    quick_test("uploading a file",upload_file_value,"to_be_uploaded.txt")

    # ============================================================ #
    #                        xsend_native
    # ============================================================ #
    await tab.xsend_native(["#nom",0],[0,0],"hello")
    box_raw_value = await tab.xinject_js('document.querySelector("input#nom").value')
    box_value = box_raw_value[0].value
    quick_test("input_native",box_value,"hello")

    # ============================================================ #
    #                         xsend_xdo
    # ============================================================ #
    await tab.xsend_xdo(["#nom2",0],[0,0],"hello")
    box2_raw_value = await tab.xinject_js('document.querySelector("input#nom2").value')
    box2_value = box2_raw_value[0].value
    quick_test("input_xdo",box2_value,"hello")

    # ============================================================ #
    #                         find_all
    # ============================================================ #
    h1_titles = await tab.find_all("h1")
    h1_title = h1_titles[0].text
    quick_test("extract_h1_title",h1_title,"Simple Form")

    # ============================================================ #
    #               xselect_native - select by value
    # ============================================================ #
    await tab.xselect_native(["#pays",0],[0,0],option_value="be")
    select_raw_value = await tab.xinject_js('document.querySelector("select#pays").value')
    select_value = select_raw_value[0].value
    quick_test("select_native_by_value",select_value,"be")
    time.sleep(1)

    # ============================================================ #
    #               xselect_native - select by text
    # ============================================================ #
    await tab.xselect_native(["#pays",0],[0,0],option_text="Canada")
    select_raw_value2 = await tab.xinject_js('document.querySelector("select#pays").value')
    select_value2 = select_raw_value2[0].value
    quick_test("select_native_by_text",select_value2,"ca")
    time.sleep(1)

    # ============================================================ #
    #               xselect_native - select by index
    # ============================================================ #
    await tab.xselect_native(["#pays",0],[0,0],option_index=1)
    select_raw_value3 = await tab.xinject_js('document.querySelector("select#pays").value')
    select_value3 = select_raw_value3[0].value
    quick_test("select_native_by_index",select_value3,"fr")

    # ============================================================ #
    #                       xclick_native
    # ============================================================ #
    await tab.xclick_native(["#btn_click",0],[0,0])
    click_raw_value = await tab.xinject_js('document.querySelector("#click_counter").innerText')
    click_value = click_raw_value[0].value
    quick_test("xclick_native",click_value,"1")

    # ============================================================ #
    #              xclick_native - checkbox toggle
    # ============================================================ #
    await tab.xclick_native(["#checkbox_test",0],[0,0])
    checkbox_raw_value = await tab.xinject_js('document.querySelector("#checkbox_test").checked')
    checkbox_value = checkbox_raw_value[0].value
    quick_test("xclick_native_checkbox",checkbox_value,True)

    # ============================================================ #
    #                         xwaiter
    # ============================================================ #
    try:
        await tab.xwaiter(css_selector="#existing_element", timeout_delay=5, sleep_list=[0,0])
        quick_test("xwaiter_existing_element","found","found")
    except Exception:
        quick_test("xwaiter_existing_element","not_found","found")

    # ============================================================ #
    #                        xdetector
    # ============================================================ #
    detector_result = await tab.xdetector(css_selector="#existing_element", sleep_list=[0,0])
    quick_test("xdetector_existing",detector_result,True)

    detector_result_missing = await tab.xdetector(css_selector="#nonexistent_element", sleep_list=[0,0])
    quick_test("xdetector_missing",detector_result_missing,False)

    # ============================================================ #
    #                       xinject_js
    # ============================================================ #
    js_result = await tab.xinject_js('1 + 1')
    quick_test("xinject_js_eval",js_result[0].value,2)

    js_title = await tab.xinject_js('document.title')
    quick_test("xinject_js_title",js_title[0].value,"Simple Form")

    # ============================================================ #
    #                     xtemporary_zoom
    # ============================================================ #
    await tab.xtemporary_zoom(0.3)
    zoom_raw = await tab.xinject_js('document.body.style.zoom')
    quick_test("xtemporary_zoom",zoom_raw[0].value,"0.3")
    await tab.xtemporary_zoom(1)

    # ============================================================ #
    #            xscrape_attribute_in_iframe
    # ============================================================ #
    iframe_attr = await tab.xscrape_attribute_in_iframe(
        iframe_number=0,
        selector_list=["#iframe_text",0],
        targetted_attribute="data-custom"
    )
    quick_test("xscrape_attribute_in_iframe",iframe_attr,"iframe_value")

    # ============================================================ #
    #              xscrape_html_in_iframe
    # ============================================================ #
    iframe_html = await tab.xscrape_html_in_iframe(
        iframe_number=0,
        selector_list=[".iframe_span",0]
    )
    quick_test("xscrape_html_in_iframe","Span in iframe" in iframe_html,True)

    # ============================================================ #
    #                       xclick_xdo
    # ============================================================ #
    await tab.xclick_xdo(["#btn_click_xdo",0],[0,0])
    click_xdo_raw = await tab.xinject_js('document.querySelector("#click_counter_xdo").innerText')
    click_xdo_value = click_xdo_raw[0].value
    quick_test("xclick_xdo",click_xdo_value,"1")

    # ============================================================ #
    #                    xmove_xdo_iframe
    # ============================================================ #
    cursor_before_iframe = tab.cursor_position[:]
    print(cursor_before_iframe)
    await tab.xmove_xdo_iframe(["#iframe_move_target",0], iframe_number=0)
    cursor_after_iframe = tab.cursor_position
    quick_test("xmove_xdo_iframe_cursor_moved", cursor_after_iframe != cursor_before_iframe, True)

    # ============================================================ #
    #                       xmove_xdo
    # ============================================================ #
    cursor_before_move = tab.cursor_position[:]
    await tab.xmove_xdo(["#move_target",0])
    cursor_after_move = tab.cursor_position
    quick_test("xmove_xdo_cursor_moved", cursor_after_move != cursor_before_move, True)

    # ============================================================ #
    #                    xmove_xdo_iframe
    # ============================================================ #
    cursor_before_iframe = tab.cursor_position[:]
    await tab.xmove_xdo_iframe(["#iframe_move_target",0], iframe_number=0)
    cursor_after_iframe = tab.cursor_position
    quick_test("xmove_xdo_iframe_cursor_moved", cursor_after_iframe != cursor_before_iframe, True)

    # ============================================================ #
    #                       xmove_native
    # ============================================================ #
    cursor_before_native = tab.cursor_position[:]
    await tab.xmove_native(["#nom", 0])
    cursor_after_native = tab.cursor_position
    quick_test("xmove_native_cursor_moved", cursor_after_native != cursor_before_native, True)

    # ============================================================ #
    #                     xclick_iframe_xdo
    # ============================================================ #
    await tab.xclick_iframe_xdo(iframe_number=0, selector_list=["#iframe_btn", 0], sleep_list=[0, 0])
    iframe_click_raw = await tab.xinject_js('document.querySelector("#test_iframe").contentDocument.querySelector("#iframe_counter").innerText')
    iframe_click_value = iframe_click_raw[0].value
    quick_test("xclick_iframe_xdo", iframe_click_value, "1")

    # ============================================================ #
    #                     xsend_iframe_xdo
    # ============================================================ #
    await tab.xsend_iframe_xdo(iframe_number=0, selector_list=["#iframe_input", 0], sleep_list=[0, 0], text="hi")
    iframe_input_raw = await tab.xinject_js('document.querySelector("#test_iframe").contentDocument.querySelector("#iframe_input").value')
    iframe_input_value = iframe_input_raw[0].value
    quick_test("xsend_iframe_xdo", iframe_input_value, "hi")

    # ============================================================ #
    #                    cookie set mechanism
    # ============================================================ #
    await agent_ctx.browser.cookies.set_all([
        {"name": "fantomas_test", "value": "cookie_value_123", "url": "https://example.com"}
    ])
    all_cookies = await agent_ctx.browser.cookies.get_all()
    cookie_found = any(c.name == "fantomas_test" and c.value == "cookie_value_123" for c in all_cookies)
    quick_test("cookie_set_and_get", cookie_found, True)

    # ============================================================ #
    #                       open_new_tab
    # ============================================================ #
    tab2 = await agent_ctx.browser.open_new_tab("file://"+os.getcwd()+"/index.html")
    time.sleep(1)
    tab2_title = await tab2.xinject_js('document.title')
    quick_test("open_new_tab", tab2_title[0].value, "Simple Form")
    await tab2.close()
    time.sleep(0.5)

    # ============================================================ #
    #                      open_new_window
    # ============================================================ #
    tab3 = await agent_ctx.browser.open_new_window("file://"+os.getcwd()+"/index.html")
    time.sleep(1)
    tab3_title = await tab3.xinject_js('document.title')
    quick_test("open_new_window", tab3_title[0].value, "Simple Form")
    await tab3.close()
    time.sleep(0.5)

    # ============================================================ #
    #                     RESULTS SUMMARY
    # ============================================================ #
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    passed = sum(1 for t in test_results if t["status"] == "PASS")
    failed = sum(1 for t in test_results if t["status"] == "FAIL")
    print(f"Total: {len(test_results)} | Passed: {passed} | Failed: {failed}")
    if failed > 0:
        print("\nFailed tests:")
        for t in test_results:
            if t["status"] == "FAIL":
                print(f"  - {t['name']}: got '{t['actual']}' | expected '{t['expected']}'")
    print("="*60)