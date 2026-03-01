import threading
from unittest.mock import patch, MagicMock

from app.services.celery_service import CeleryService, RunMonitorDisplay


class TestCeleryServiceInit:
    @patch("app.services.celery_service.Celery")
    def test_creates_app(self, MockCelery):
        service = CeleryService("test", broker="amqp://localhost")
        MockCelery.assert_called_once_with("test", broker="amqp://localhost")

    @patch("app.services.celery_service.Celery")
    def test_config_module(self, MockCelery):
        service = CeleryService("test", config_module="celeryconfig")
        MockCelery.return_value.config_from_object.assert_called_once_with("celeryconfig")


class TestSendMessage:
    @patch("app.services.celery_service.Celery")
    def test_sends_task(self, MockCelery):
        service = CeleryService("test", broker="amqp://localhost")
        service.send_message({"data": 1}, "queue1", "tasks.run")
        service.celery_app.send_task.assert_called_once_with(
            "tasks.run", args=[{"data": 1}], queue="queue1"
        )


class TestIsQueueEmpty:
    @patch("app.services.celery_service.Celery")
    def test_empty(self, MockCelery):
        service = CeleryService("test")
        mock_conn = MagicMock()
        mock_channel = MagicMock()
        mock_channel.queue_declare.return_value.message_count = 0
        mock_conn.default_channel = mock_channel
        service.celery_app.connection_or_acquire.return_value.__enter__ = MagicMock(return_value=mock_conn)
        service.celery_app.connection_or_acquire.return_value.__exit__ = MagicMock(return_value=False)
        assert service.is_queue_empty("q") is True

    @patch("app.services.celery_service.Celery")
    def test_not_empty(self, MockCelery):
        service = CeleryService("test")
        mock_conn = MagicMock()
        mock_channel = MagicMock()
        mock_channel.queue_declare.return_value.message_count = 5
        mock_conn.default_channel = mock_channel
        service.celery_app.connection_or_acquire.return_value.__enter__ = MagicMock(return_value=mock_conn)
        service.celery_app.connection_or_acquire.return_value.__exit__ = MagicMock(return_value=False)
        assert service.is_queue_empty("q") is False


class TestAreTasksActive:
    @patch("app.services.celery_service.Celery")
    def test_active_on_queue(self, MockCelery):
        service = CeleryService("test")
        mock_inspector = MagicMock()
        mock_inspector.active.return_value = {
            "worker1": [{"delivery_info": {"routing_key": "my_queue"}}]
        }
        service.celery_app.control.inspect.return_value = mock_inspector
        assert service.are_tasks_active("my_queue") is True

    @patch("app.services.celery_service.Celery")
    def test_active_on_different_queue(self, MockCelery):
        service = CeleryService("test")
        mock_inspector = MagicMock()
        mock_inspector.active.return_value = {
            "worker1": [{"delivery_info": {"routing_key": "other_queue"}}]
        }
        service.celery_app.control.inspect.return_value = mock_inspector
        assert service.are_tasks_active("my_queue") is False

    @patch("app.services.celery_service.Celery")
    def test_no_workers(self, MockCelery):
        service = CeleryService("test")
        mock_inspector = MagicMock()
        mock_inspector.active.return_value = None
        service.celery_app.control.inspect.return_value = mock_inspector
        assert service.are_tasks_active("q") is False


class TestShutdownWorkersForQueue:
    @patch("app.services.celery_service.Celery")
    def test_shuts_down_correct_worker(self, MockCelery):
        service = CeleryService("test")
        mock_inspector = MagicMock()
        mock_inspector.active_queues.return_value = {
            "worker1": [{"name": "my_queue"}],
            "worker2": [{"name": "other_queue"}],
        }
        service.celery_app.control.inspect.return_value = mock_inspector
        service.shutdown_workers_for_queue("my_queue")
        service.celery_app.control.shutdown.assert_called_once_with(destination=["worker1"])

    @patch("app.services.celery_service.Celery")
    def test_no_active_queues(self, MockCelery):
        service = CeleryService("test")
        mock_inspector = MagicMock()
        mock_inspector.active_queues.return_value = None
        service.celery_app.control.inspect.return_value = mock_inspector
        service.shutdown_workers_for_queue("q")  # Should not raise


class TestRunMonitorDisplay:
    def test_singleton(self):
        # Reset singleton for test isolation
        RunMonitorDisplay._instance = None
        d1 = RunMonitorDisplay()
        d2 = RunMonitorDisplay()
        assert d1 is d2
        RunMonitorDisplay._instance = None  # cleanup
