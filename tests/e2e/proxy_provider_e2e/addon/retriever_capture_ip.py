import json


def retriever_capture_ip(flow, queue):
    """Data retriever: captures IP from httpbin.org/ip responses."""
    if flow.response and "httpbin.org/ip" in flow.request.pretty_url:
        try:
            body = json.loads(flow.response.get_text())
            queue.put(body)
        except Exception:
            pass
