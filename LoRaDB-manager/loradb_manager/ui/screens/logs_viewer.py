"""Logs viewer screen for real-time container log streaming."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, RichLog, Button, Select, SelectionList
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
import asyncio

from ...core.instance_manager import InstanceManager
from ...core.instance import InstanceMetadata
from ...config import Config


class LogsViewerScreen(Screen):
    """Screen for viewing real-time container logs."""

    BINDINGS = [
        Binding("escape", "close", "Close", priority=True),
        Binding("c", "clear_logs", "Clear"),
    ]

    def __init__(self, instance: InstanceMetadata, instance_manager: InstanceManager):
        """
        Initialize logs viewer.

        Args:
            instance: Instance to view logs for
            instance_manager: InstanceManager instance
        """
        super().__init__()
        self.instance = instance
        self.instance_manager = instance_manager
        self.following = True
        self.current_container = f"loradb-{instance.instance_id}"
        self._log_worker = None

    def compose(self) -> ComposeResult:
        """Compose logs viewer UI."""
        yield Container(
            Vertical(
                Static(f"Logs: {self.instance.name}", classes="screen-title"),

                # Container selector
                Horizontal(
                    Static("Container: ", classes="label"),
                    Select(
                        options=[
                            ("LoRaDB", f"loradb-{self.instance.instance_id}"),
                            ("UI Backend", f"loradb-ui-backend-{self.instance.instance_id}"),
                            ("UI Frontend", f"loradb-ui-frontend-{self.instance.instance_id}"),
                        ],
                        value=self.current_container,
                        id="container-select"
                    ),
                    Button("Refresh", id="btn-refresh"),
                    Button("Clear", id="btn-clear"),
                    Button("Close", id="btn-close", variant="primary"),
                    classes="log-controls"
                ),

                # Log display
                RichLog(id="log-display", highlight=True, markup=True),

                # Status bar
                Static(f"Following: {self.following} | Container: {self.current_container}", id="follow-status"),

                id="logs-container"
            )
        )

    def on_mount(self):
        """Start log streaming when mounted."""
        self._start_log_stream()

    def on_unmount(self):
        """Clean up when screen is unmounted."""
        if self._log_worker and self._log_worker.is_running:
            self._log_worker.cancel()

    def on_select_changed(self, event):
        """Handle container selection change."""
        if event.select.id == "container-select":
            self.current_container = event.value
            self._start_log_stream()
            self._update_status()

    def on_button_pressed(self, event):
        """Handle button presses."""
        if event.button.id == "btn-refresh":
            self._start_log_stream()
        elif event.button.id == "btn-clear":
            self.action_clear_logs()
        elif event.button.id == "btn-close":
            self.action_close()

    def action_close(self):
        """Close logs viewer."""
        self.app.pop_screen()

    def action_clear_logs(self):
        """Clear log display."""
        log_display = self.query_one("#log-display", RichLog)
        log_display.clear()

    def _start_log_stream(self):
        """Start streaming logs from selected container."""
        # Cancel previous worker if running
        if self._log_worker and self._log_worker.is_running:
            self._log_worker.cancel()

        self.action_clear_logs()

        # Start worker to stream logs
        self._log_worker = self.run_worker(
            self._stream_logs_worker(self.current_container),
            exclusive=False
        )

    async def _stream_logs_worker(self, container_name: str):
        """
        Background worker to stream logs without blocking UI.

        Args:
            container_name: Name of container to stream from
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        import queue
        import threading

        log_display = self.query_one("#log-display", RichLog)

        # Use a queue to communicate between thread and async worker
        log_queue = queue.Queue()
        stop_event = threading.Event()

        def blocking_log_reader():
            """Run blocking log streaming in a separate thread."""
            try:
                for line in self.instance_manager.docker_manager.stream_logs(
                    container_name, tail=Config.LOG_TAIL_LINES
                ):
                    if stop_event.is_set():
                        break
                    log_queue.put(line)
            except Exception as e:
                log_queue.put(f"[red]Error streaming logs: {e}[/red]")
            finally:
                log_queue.put(None)  # Sentinel to signal end

        # Start the blocking reader in a thread
        reader_thread = threading.Thread(target=blocking_log_reader, daemon=True)
        reader_thread.start()

        try:
            # Process log lines from the queue
            while self.is_mounted and self.following:
                # Check queue without blocking (non-blocking get with try/except)
                try:
                    # Use get_nowait to avoid blocking, then sleep to yield control
                    line = log_queue.get_nowait()

                    if line is None:  # Sentinel value
                        break

                    log_display.write(line.rstrip())

                except queue.Empty:
                    # No data yet, yield control and continue
                    await asyncio.sleep(0.05)
                    continue

        except Exception as e:
            log_display.write(f"[red]Worker error: {e}[/red]")
        finally:
            # Signal the reader thread to stop
            stop_event.set()

    def _update_status(self):
        """Update status bar."""
        status = self.query_one("#follow-status", Static)
        status.update(f"Following: {self.following} | Container: {self.current_container}")
