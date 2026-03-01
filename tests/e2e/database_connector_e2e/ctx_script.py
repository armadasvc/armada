import uuid
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
    print("DATABASE CONNECTOR E2E TEST SUITE")
    print("=" * 60)

    db = agent_ctx.database
    test_table = "armada_e2e_test"
    test_uuid = str(uuid.uuid4())

    # ============================================================ #
    #  TEST 1: Connector is enabled                                 #
    # ============================================================ #
    print("\n--- Test 1: Connector enabled ---")

    quick_test("connector_enabled", db.enabled, 1)

    # ============================================================ #
    #  TEST 2: SELECT query (select_from_db)                        #
    #  Verify basic read operation works                            #
    # ============================================================ #
    print("\n--- Test 2: SELECT query ---")

    rows = db.select_from_db("SELECT 1 AS test_value")
    has_result = rows is not None and len(rows) > 0
    quick_test("select_returns_rows", has_result, True)
    if has_result:
        print(f"  Result: {rows[0]}")

    # ============================================================ #
    #  TEST 3: SELECT with parameters                               #
    #  Verify parameterized queries work                            #
    # ============================================================ #
    print("\n--- Test 3: SELECT with parameters ---")

    rows_param = db.select_from_db("SELECT %s AS echo_value", "hello_armada")
    has_param_result = rows_param is not None and len(rows_param) > 0
    quick_test("select_with_params", has_param_result, True)
    if has_param_result:
        echo_value = rows_param[0][0]
        quick_test("param_value_echoed", echo_value, "hello_armada")
        print(f"  Echoed: {echo_value}")

    # ============================================================ #
    #  TEST 4: CREATE temp table + INSERT (post_to_db)              #
    #  Verify write operations work                                 #
    # ============================================================ #
    print("\n--- Test 4: INSERT via post_to_db ---")

    # Create a temp table for this test run
    db.post_to_db(
        f"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{test_table}' AND xtype='U') "
        f"CREATE TABLE {test_table} (id VARCHAR(255), value VARCHAR(255))"
    )
    print(f"  Table '{test_table}' ensured.")

    db.post_to_db(
        f"INSERT INTO {test_table} (id, value) VALUES (%s, %s)",
        test_uuid, "e2e_test_value"
    )
    print(f"  Inserted row with id={test_uuid}")

    # Read back the inserted row
    rows_inserted = db.select_from_db(
        f"SELECT value FROM {test_table} WHERE id = %s", test_uuid
    )
    has_inserted = rows_inserted is not None and len(rows_inserted) > 0
    quick_test("insert_and_read_back", has_inserted, True)
    if has_inserted:
        quick_test("inserted_value_matches", rows_inserted[0][0], "e2e_test_value")

    # ============================================================ #
    #  TEST 5: SELECT with multiple parameters                      #
    # ============================================================ #
    print("\n--- Test 5: Multiple parameters ---")

    rows_multi = db.select_from_db(
        "SELECT %s AS a, %s AS b, %s AS c", "alpha", "beta", "gamma"
    )
    has_multi = rows_multi is not None and len(rows_multi) > 0
    quick_test("multi_param_returns_rows", has_multi, True)
    if has_multi:
        a, b, c = rows_multi[0]
        quick_test("multi_param_a", a, "alpha")
        quick_test("multi_param_b", b, "beta")
        quick_test("multi_param_c", c, "gamma")

    # ============================================================ #
    #  TEST 6: SELECT with autocommit (select_with_commit_from_db)  #
    # ============================================================ #
    print("\n--- Test 6: SELECT with autocommit ---")

    rows_commit = db.select_with_commit_from_db("SELECT 42 AS answer")
    has_commit = rows_commit is not None and len(rows_commit) > 0
    quick_test("select_with_commit_returns_rows", has_commit, True)
    if has_commit:
        quick_test("select_with_commit_value", rows_commit[0][0], 42)

    # ============================================================ #
    #  TEST 7: UPDATE via post_to_db                                #
    # ============================================================ #
    print("\n--- Test 7: UPDATE via post_to_db ---")

    db.post_to_db(
        f"UPDATE {test_table} SET value = %s WHERE id = %s",
        "updated_value", test_uuid
    )
    rows_updated = db.select_from_db(
        f"SELECT value FROM {test_table} WHERE id = %s", test_uuid
    )
    has_updated = rows_updated is not None and len(rows_updated) > 0
    quick_test("update_read_back", has_updated, True)
    if has_updated:
        quick_test("updated_value_matches", rows_updated[0][0], "updated_value")

    # ============================================================ #
    #  TEST 8: DELETE via post_to_db                                #
    # ============================================================ #
    print("\n--- Test 8: DELETE via post_to_db ---")

    db.post_to_db(
        f"DELETE FROM {test_table} WHERE id = %s", test_uuid
    )
    rows_deleted = db.select_from_db(
        f"SELECT value FROM {test_table} WHERE id = %s", test_uuid
    )
    is_deleted = rows_deleted is not None and len(rows_deleted) == 0
    quick_test("row_deleted", is_deleted, True)

    # ============================================================ #
    #  TEST 9: Disabled connector returns None                      #
    # ============================================================ #
    print("\n--- Test 9: Disabled connector ---")

    db.enabled = 0
    disabled_result = db.select_from_db("SELECT 1")
    quick_test("disabled_returns_none", disabled_result, None)
    db.enabled = 1  # Re-enable

    # ============================================================ #
    #  CLEANUP: Drop test table                                     #
    # ============================================================ #
    print("\n--- Cleanup ---")
    db.post_to_db(f"DROP TABLE IF EXISTS {test_table}")
    print(f"  Table '{test_table}' dropped.")

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
