import sys
import time
import threading
from celery import Celery


class RunMonitorDisplay:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._runs = {}
                    cls._instance._display_lock = threading.Lock()
                    cls._instance._prev_line_count = 0
        return cls._instance

    def update_run(self, run_id: str, elapsed_sec: int) -> None:
        with self._display_lock:
            self._runs[run_id] = elapsed_sec
            self._refresh()

    def remove_run(self, run_id: str, message: str) -> None:
        with self._display_lock:
            self._runs.pop(run_id, None)
            self._clear_previous()
            self._prev_line_count = 0
            self._refresh()

    def _clear_previous(self) -> None:
        if self._prev_line_count > 0:
            sys.stdout.write(f"\033[{self._prev_line_count}A")
            sys.stdout.write(f"\033[J")

    def _refresh(self) -> None:
        self._clear_previous()
        lines = []
        for run_id, sec in self._runs.items():
            lines.append(f"[{run_id}] Active since: {sec} sec")
        output = "\n".join(lines)
        if output:
            sys.stdout.write(output + "\n")
        sys.stdout.flush()
        self._prev_line_count = len(lines)


class CeleryService:
    def __init__(self, app_name: str, broker: str | None = None, config_module: str | None = None):
        self.celery_app = Celery(app_name, broker=broker)
        if config_module:
            self.celery_app.config_from_object(config_module)

    def send_message(self, message: dict, queue_name: str, task_name: str) -> None:
        self.celery_app.send_task(task_name, args=[message], queue=queue_name) #ICI

    def is_queue_empty(self, queue_name: str) -> bool:
        with self.celery_app.connection_or_acquire() as conn:
            queue_info = conn.default_channel.queue_declare(queue=queue_name, passive=True)
            return queue_info.message_count == 0

    def are_tasks_active(self, queue_name: str) -> bool:
        inspector = self.celery_app.control.inspect()
        active_tasks = inspector.active()

        if not active_tasks:
            return False

        for worker, tasks in active_tasks.items():
            for task in tasks:
                if task["delivery_info"]["routing_key"] == queue_name:
                    return True
        return False

    def shutdown_workers_for_queue(self, queue_name: str) -> None:
        inspector = self.celery_app.control.inspect()
        active_queues = inspector.active_queues()

        if not active_queues:
            return

        for worker, queues in active_queues.items():
            for queue in queues:
                if queue["name"] == queue_name:
                    self.celery_app.control.shutdown(destination=[worker])

    def monitor_queue(self, queue_name: str, check_interval: int = 15) -> None:
        display = RunMonitorDisplay()
        time.sleep(10)
        elapsed = 0
        display.update_run(queue_name, elapsed)
        while True:
            if self.is_queue_empty(queue_name) and not self.are_tasks_active(queue_name):
                display.remove_run(queue_name, f"[{queue_name}] Completed. Stopping workers...")
                self.shutdown_workers_for_queue(queue_name)
                break
            time.sleep(check_interval)
            elapsed += check_interval
            display.update_run(queue_name, elapsed)

    def start_monitoring_in_thread(self, queue_name: str) -> threading.Thread:
        thread = threading.Thread(target=self.monitor_queue, args=(queue_name,))
        thread.daemon = True
        thread.name = queue_name
        thread.start()
        return thread
