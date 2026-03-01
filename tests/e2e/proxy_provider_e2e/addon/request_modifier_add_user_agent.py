def request_modifier_add_user_agent(flow):
    """Request modifier: overrides the User-Agent header."""
    flow.request.headers["User-Agent"] = "ArmadaProxyTest/1.0"
