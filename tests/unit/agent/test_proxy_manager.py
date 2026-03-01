import base64
from unittest.mock import patch, MagicMock
from billiard import Queue

from proxy_manager import (
    ProxyManager,
    ProxyAddOn,
    UpstreamProxyFetcher,
    _build_url_with_params,
)


class TestBuildUrlWithParams:
    def test_basic(self):
        url = _build_url_with_params("http://host/path", {"a": "1", "b": "2"})
        assert "a=1" in url
        assert "b=2" in url

    def test_falsy_values_ignored(self):
        url = _build_url_with_params("http://host/path", {"a": "1", "b": None, "c": ""})
        assert "a=1" in url
        assert "b" not in url
        assert "c=" not in url

    def test_preserves_existing_params(self):
        url = _build_url_with_params("http://host/path?existing=yes", {"new": "val"})
        assert "existing=yes" in url
        assert "new=val" in url

    def test_type_error_on_bad_url(self):
        import pytest
        with pytest.raises(TypeError):
            _build_url_with_params(123, {})

    def test_type_error_on_bad_params(self):
        import pytest
        with pytest.raises(TypeError):
            _build_url_with_params("http://host", "not_a_dict")


class TestProxyManagerInit:
    def test_defaults(self):
        pm = ProxyManager()
        assert pm.upstream_proxy_enabled == 0
        assert pm.upstream_proxy_broker_type == "provider"
        assert pm.modifiers_array == []
        assert pm.retrievers_array == []
        assert pm.modifiers_request_array == []
        assert pm.proxy_process is None
        assert pm.count_data_queue is None

    def test_parse_config(self):
        pm = ProxyManager({"upstream_proxy_enabled": 1, "upstream_proxy_broker_type": "direct"})
        assert pm.upstream_proxy_enabled == 1
        assert pm.upstream_proxy_broker_type == "direct"


class TestProxyManagerModifiers:
    def test_add_modifier(self):
        pm = ProxyManager()
        fn = lambda flow: None
        pm.add_modifier(fn)
        assert fn in pm.modifiers_array

    def test_add_request_modifier(self):
        pm = ProxyManager()
        fn = lambda flow: None
        pm.add_request_modifier(fn)
        assert fn in pm.modifiers_request_array

    def test_add_retriever(self):
        pm = ProxyManager()
        fn = lambda flow, q: None
        pm.add_retriever("my_queue", fn)
        assert len(pm.retrievers_array) == 1
        assert pm.retrievers_array[0]["queue_id"] == "my_queue"
        assert pm.retrievers_array[0]["retriever_function"] is fn
        assert pm.retrievers_array[0]["queue"] is not None


class TestProxyManagerQueues:
    def test_set_data_queue(self):
        pm = ProxyManager()
        q = pm.set_data_queue()
        assert pm.count_data_queue is q
        assert pm.count_data_queue is not None

    def test_get_data_count(self):
        pm = ProxyManager()
        pm.set_data_queue()
        pm.count_data_queue.put(100)
        pm.count_data_queue.put(250)
        result = pm.get_data_count()
        assert result == 250

    def test_retrieve(self):
        pm = ProxyManager()
        pm.add_retriever("q1", lambda f, q: None)
        pm.retrievers_array[0]["queue"].put("captured_data")
        result = pm.retrieve("q1")
        assert result == "captured_data"

    def test_retrieve_nonexistent_queue(self):
        pm = ProxyManager()
        result = pm.retrieve("nonexistent")
        assert result is None


class TestProxyAddOn:
    def test_auth_header_injected(self):
        addon = ProxyAddOn("http://user:pass@proxy:8080", Queue(), [], [], [])
        mock_flow = MagicMock()
        mock_flow.request.headers = {}
        addon.http_connect_upstream(mock_flow)
        auth = mock_flow.request.headers["proxy-authorization"]
        assert auth.startswith("Basic ")
        decoded = base64.b64decode(auth.split(" ")[1]).decode()
        assert decoded == "user:pass"

    def test_no_auth_without_credentials(self):
        addon = ProxyAddOn("http://proxy:8080", Queue(), [], [], [])
        mock_flow = MagicMock()
        mock_flow.request.headers = {}
        addon.http_connect_upstream(mock_flow)
        assert "proxy-authorization" not in mock_flow.request.headers

    def test_response_counts_data(self):
        q = Queue()
        addon = ProxyAddOn(None, q, [], [], [])
        mock_flow = MagicMock()
        mock_flow.response.headers.get.return_value = "500"
        addon.response(mock_flow)
        assert addon.total_data == 500
        assert q.get() == 500

    def test_response_runs_modifiers(self):
        called = []
        modifier = lambda flow: called.append(True)
        addon = ProxyAddOn(None, Queue(), [modifier], [], [])
        mock_flow = MagicMock()
        mock_flow.response.headers.get.return_value = None
        addon.response(mock_flow)
        assert len(called) == 1

    def test_response_runs_retrievers(self):
        q = Queue()
        retriever_calls = []
        retriever = {"queue_id": "r1", "queue": q, "retriever_function": lambda f, queue: retriever_calls.append(True)}
        addon = ProxyAddOn(None, Queue(), [], [retriever], [])
        mock_flow = MagicMock()
        mock_flow.response.headers.get.return_value = None
        addon.response(mock_flow)
        assert len(retriever_calls) == 1

    def test_request_runs_request_modifiers(self):
        called = []
        req_modifier = lambda flow: called.append(True)
        addon = ProxyAddOn(None, Queue(), [], [], [req_modifier])
        mock_flow = MagicMock()
        addon.request(mock_flow)
        assert len(called) == 1


class TestUpstreamProxyFetcher:
    @patch("proxy_manager.requests.get")
    def test_provider_mode(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"proxy_url": "http://fetched:8080"}
        fetcher = UpstreamProxyFetcher("http://provider-host", "provider", {})
        result = fetcher.fetch_proxy()
        assert result["proxy_url"] == "http://fetched:8080"

    @patch("proxy_manager.requests.get")
    def test_provider_mode_failure(self, mock_get):
        mock_get.return_value.status_code = 500
        fetcher = UpstreamProxyFetcher("http://provider-host", "provider", {})
        import pytest
        with pytest.raises(Exception, match="status code 500"):
            fetcher.fetch_proxy()

    def test_direct_mode(self):
        fetcher = UpstreamProxyFetcher("http://direct-proxy:8080", "direct", {})
        result = fetcher.fetch_proxy()
        assert result["proxy_url"] == "http://direct-proxy:8080"


class TestProxyAddOnEdgeCases:
    def test_response_no_content_length_header(self):
        """When Content-Length is absent, total_data should not change."""
        q = Queue()
        addon = ProxyAddOn(None, q, [], [], [])
        mock_flow = MagicMock()
        mock_flow.response.headers.get.return_value = None
        addon.response(mock_flow)
        assert addon.total_data == 0
        assert q.empty()

    def test_response_content_length_zero(self):
        """Content-Length: 0 should be counted as 0 and put in queue."""
        q = Queue()
        addon = ProxyAddOn(None, q, [], [], [])
        mock_flow = MagicMock()
        mock_flow.response.headers.get.return_value = "0"
        addon.response(mock_flow)
        assert addon.total_data == 0
        assert q.get() == 0

    def test_response_cumulative_data_count(self):
        """Multiple responses should accumulate total_data correctly."""
        q = Queue()
        addon = ProxyAddOn(None, q, [], [], [])
        for size in ["100", "200", "300"]:
            mock_flow = MagicMock()
            mock_flow.response.headers.get.return_value = size
            addon.response(mock_flow)
        assert addon.total_data == 600
        # Queue receives cumulative totals: 100, 300, 600
        vals = [q.get(timeout=1) for _ in range(3)]
        assert vals == [100, 300, 600]

    def test_multiple_modifiers_all_called(self):
        """All modifiers should be called, in order."""
        call_order = []
        m1 = lambda flow: call_order.append("m1")
        m2 = lambda flow: call_order.append("m2")
        m3 = lambda flow: call_order.append("m3")
        addon = ProxyAddOn(None, Queue(), [m1, m2, m3], [], [])
        mock_flow = MagicMock()
        mock_flow.response.headers.get.return_value = None
        addon.response(mock_flow)
        assert call_order == ["m1", "m2", "m3"]

    def test_modifier_exception_stops_chain(self):
        """If a modifier raises, subsequent modifiers should NOT be called
        (current implementation has no try/except, so it propagates)."""
        called = []
        def bad_modifier(flow):
            raise ValueError("boom")
        m2 = lambda flow: called.append("m2")
        addon = ProxyAddOn(None, Queue(), [bad_modifier, m2], [], [])
        mock_flow = MagicMock()
        mock_flow.response.headers.get.return_value = None
        import pytest
        with pytest.raises(ValueError, match="boom"):
            addon.response(mock_flow)
        assert "m2" not in called  # m2 never ran

    def test_auth_with_special_chars_in_password(self):
        """Proxy credentials with special characters should be encoded correctly."""
        addon = ProxyAddOn("http://user%40name:p%40ss%3Aword@proxy:8080", Queue(), [], [], [])
        mock_flow = MagicMock()
        mock_flow.request.headers = {}
        addon.http_connect_upstream(mock_flow)
        auth = mock_flow.request.headers["proxy-authorization"]
        decoded = base64.b64decode(auth.split(" ")[1]).decode()
        assert ":" in decoded  # Should contain user:pass format


class TestProxyManagerEdgeCases:
    def test_retrieve_latest_value_from_queue(self):
        """retrieve() should return the LAST element in the queue, not the first."""
        pm = ProxyManager()
        pm.add_retriever("q1", lambda f, q: None)
        pm.retrievers_array[0]["queue"].put("first")
        pm.retrievers_array[0]["queue"].put("second")
        pm.retrievers_array[0]["queue"].put("third")
        result = pm.retrieve("q1")
        assert result == "third"

    def test_multiple_retrievers_independent(self):
        """Multiple retrievers should have independent queues."""
        pm = ProxyManager()
        pm.add_retriever("q1", lambda f, q: None)
        pm.add_retriever("q2", lambda f, q: None)
        pm.retrievers_array[0]["queue"].put("data_q1")
        pm.retrievers_array[1]["queue"].put("data_q2")
        assert pm.retrieve("q1") == "data_q1"
        assert pm.retrieve("q2") == "data_q2"

    def test_fetch_upstream_proxy_builds_correct_url(self):
        """fetch_upstream_proxy should forward config_proxy params to the provider URL."""
        pm = ProxyManager({
            "upstream_proxy_enabled": 1,
            "upstream_proxy_broker_type": "provider",
            "proxy_type": "residential",
        })
        with patch("proxy_manager.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"proxy_url": "http://p:8080"}
            pm.fetch_upstream_proxy()
            called_url = mock_get.call_args[0][0]
            assert "proxy_type=residential" in called_url

    def test_switch_upstream_proxy_terminates_and_relaunches(self):
        """switch_upstream_proxy should call exit then launch."""
        pm = ProxyManager()
        pm.proxy_process = MagicMock()
        with patch.object(pm, "launch_proxy") as mock_launch:
            pm.switch_upstream_proxy()
            pm.proxy_process.terminate.assert_called_once()
            mock_launch.assert_called_once()
