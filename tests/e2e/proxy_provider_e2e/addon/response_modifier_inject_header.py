def response_modifier_inject_header(flow):
    """Response modifier: injects a custom header into every response."""
    if flow.response:
        flow.response.headers["X-Armada-Modified"] = "true"
        if "httpbin.org" in flow.request.pretty_url:
            print(f"  [Response Modifier] URL: {flow.request.pretty_url}")
            print(f"  [Response Modifier] Response headers after injection:")
            for k, v in flow.response.headers.items():
                print(f"    {k}: {v}")
