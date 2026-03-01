import json


def retriever_capture_headers(flow, queue):
    """Data retriever: captures the response body from httpbin.org/headers."""
    if flow.response and "httpbin.org/headers" in flow.request.pretty_url:
        try:
            body = json.loads(flow.response.get_text())
            queue.put(body)
        except Exception:
            pass
