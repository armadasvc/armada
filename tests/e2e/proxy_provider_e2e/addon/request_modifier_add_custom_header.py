def request_modifier_add_custom_header(flow):
    """Request modifier: adds a custom header to every outgoing request."""
    flow.request.headers["X-Armada-Test"] = "proxy-e2e-header-value"
