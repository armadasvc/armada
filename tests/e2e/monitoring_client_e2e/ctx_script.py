import uuid
import os
import requests
from ctx_agent_context import AgentContext
from ctx_job_context import JobContext


# ================================================================== #
#                         TEST HELPER                                 #
# ================================================================== #

test_results = []

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


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
    print("MONITORING CLIENT E2E TEST SUITE")
    print("=" * 60)

    mc = job_ctx.monitoring_client
    run_uuid = job_ctx.job_message["run_id"]

    # ============================================================ #
    #  TEST 1: Run and Job were created (by ctx_job_context)        #
    #  Verify the run exists in the backend                         #
    # ============================================================ #
    print("\n--- Test 1: Run creation ---")

    resp = requests.get(f"{BACKEND_URL}/api/runs/", params={"page": 1, "page_size": 100})
    runs = resp.json().get("runs", [])
    run_exists = any(r["run_uuid"] == run_uuid for r in runs)
    quick_test("run_created_in_backend", run_exists, True)
    print(f"  run_uuid: {run_uuid}")

    # ============================================================ #
    #  TEST 2: Job was created with status "Running"                #
    # ============================================================ #
    print("\n--- Test 2: Job creation ---")

    resp = requests.get(f"{BACKEND_URL}/api/jobs/", params={"run_uuid": run_uuid})
    jobs = resp.json().get("jobs", [])
    has_job = len(jobs) > 0
    quick_test("job_created_in_backend", has_job, True)
    if has_job:
        job_uuid = jobs[0]["job_uuid"]
        job_status = jobs[0]["job_status"]
        quick_test("job_initial_status_running", job_status, "Running")
        print(f"  job_uuid: {job_uuid}")
    else:
        job_uuid = None

    # ============================================================ #
    #  TEST 3: Record success event                                 #
    #  Call record_success_event() and verify it appears            #
    # ============================================================ #
    print("\n--- Test 3: Record success event ---")

    mc.record_success_event("E2E test - step 1 completed")
    print("  Sent: 'E2E test - step 1 completed'")

    if job_uuid:
        resp = requests.get(f"{BACKEND_URL}/api/events/", params={"job_uuid": job_uuid})
        events = resp.json()
        has_event = any(e["event_content"] == "E2E test - step 1 completed" for e in events)
        quick_test("success_event_recorded", has_event, True)
        if has_event:
            event = next(e for e in events if e["event_content"] == "E2E test - step 1 completed")
            quick_test("success_event_status", event["event_status"], "Success")

    # ============================================================ #
    #  TEST 4: Record multiple success events                       #
    #  Verify all events appear in order                            #
    # ============================================================ #
    print("\n--- Test 4: Multiple success events ---")

    mc.record_success_event("E2E test - step 2 completed")
    mc.record_success_event("E2E test - step 3 completed")
    print("  Sent: 'E2E test - step 2 completed'")
    print("  Sent: 'E2E test - step 3 completed'")

    if job_uuid:
        resp = requests.get(f"{BACKEND_URL}/api/events/", params={"job_uuid": job_uuid})
        events = resp.json()
        event_count = len(events)
        quick_test("multiple_events_count", event_count >= 3, True)
        print(f"  Total events for this job: {event_count}")
        for e in events:
            print(f"    [{e['event_status']}] {e['event_content']}")

    # ============================================================ #
    #  TEST 5: Record final success event                           #
    #  Verify event is created AND job status changes to "Success"  #
    # ============================================================ #
    print("\n--- Test 5: Record final success event ---")

    mc.record_finalsuccess_event("E2E test - all steps completed")
    print("  Sent: 'E2E test - all steps completed'")

    if job_uuid:
        # Check event
        resp = requests.get(f"{BACKEND_URL}/api/events/", params={"job_uuid": job_uuid})
        events = resp.json()
        has_final = any(e["event_content"] == "E2E test - all steps completed" for e in events)
        quick_test("final_success_event_recorded", has_final, True)

        # Check job status changed to Success
        resp = requests.get(f"{BACKEND_URL}/api/jobs/", params={"run_uuid": run_uuid})
        jobs = resp.json().get("jobs", [])
        if jobs:
            quick_test("job_status_after_finalsuccess", jobs[0]["job_status"], "Success")

    # ============================================================ #
    #  TEST 6: Create a second job and test failure flow            #
    #  New MonitoringClient instance for failure scenario            #
    # ============================================================ #
    print("\n--- Test 6: Record failed event (new job) ---")

    from src.monitoring_client import MonitoringClient  # type: ignore
    job_uuid_2 = str(uuid.uuid4())
    pod_index = os.getenv("POD_INDEX", 100)
    mc2 = MonitoringClient(run_uuid, pod_index, job_uuid_2).create_job()

    mc2.record_success_event("E2E test - attempting risky operation")
    mc2.record_failed_event("E2E test - operation failed")
    print(f"  Created second job: {job_uuid_2}")
    print("  Sent success event then failed event")

    resp = requests.get(f"{BACKEND_URL}/api/events/", params={"job_uuid": job_uuid_2})
    events_2 = resp.json()
    has_failed = any(e["event_status"] == "Failed" for e in events_2)
    quick_test("failed_event_recorded", has_failed, True)

    # Check job status changed to Failed
    resp = requests.get(f"{BACKEND_URL}/api/jobs/", params={"run_uuid": run_uuid})
    jobs_all = resp.json().get("jobs", [])
    job_2_entry = next((j for j in jobs_all if j["job_uuid"] == job_uuid_2), None)
    if job_2_entry:
        quick_test("job_status_after_failure", job_2_entry["job_status"], "Failed")

    print(f"\n  All events for failed job ({job_uuid_2}):")
    for e in events_2:
        print(f"    [{e['event_status']}] {e['event_content']}")

    # ============================================================ #
    #  TEST 7: Verify all jobs for the run                          #
    #  List all jobs and their statuses                             #
    # ============================================================ #
    print("\n--- Test 7: Run summary ---")

    resp = requests.get(f"{BACKEND_URL}/api/jobs/", params={"run_uuid": run_uuid, "page_size": 100})
    all_jobs = resp.json().get("jobs", [])
    quick_test("total_jobs_for_run", len(all_jobs) >= 2, True)

    print(f"\n  All jobs for run {run_uuid}:")
    for j in all_jobs:
        print(f"    [{j['job_status']}] job={j['job_uuid']}")

    # ============================================================ #
    #  CLEANUP: Delete the test run (cascades to jobs and events)   #
    # ============================================================ #
    print("\n--- Cleanup ---")
    resp = requests.delete(f"{BACKEND_URL}/api/runs/{run_uuid}")
    print(f"  Deleted run {run_uuid}: {resp.json()}")

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
