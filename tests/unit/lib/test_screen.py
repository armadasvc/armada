import io
from unittest.mock import patch, MagicMock

from fantomas.screen import Screen


class TestScreenInit:
    def test_defaults(self):
        screen = Screen()
        assert screen.visible == 1
        assert screen.height == 1200
        assert screen.width == 800
        assert screen.display is None

    def test_overrides(self):
        screen = Screen({"screen_visible": 0, "screen_height": 1920, "screen_width": 1080})
        assert screen.visible == 0
        assert screen.height == 1920
        assert screen.width == 1080

    def test_no_parse_without_params(self):
        screen = Screen()
        assert screen.screen_params is None


class TestLaunchScreen:
    @patch("fantomas.screen.Display")
    def test_display_started(self, MockDisplay):
        screen = Screen()
        screen.launch_screen()
        MockDisplay.assert_called_once_with(visible=1, size=(800, 1200))
        MockDisplay.return_value.start.assert_called_once()

    @patch("fantomas.screen.Display")
    def test_returns_self(self, MockDisplay):
        screen = Screen()
        result = screen.launch_screen()
        assert result is screen

    @patch("fantomas.screen.Display")
    def test_custom_params(self, MockDisplay):
        screen = Screen({"screen_visible": 0, "screen_width": 1920, "screen_height": 1080})
        screen.launch_screen()
        MockDisplay.assert_called_once_with(visible=0, size=(1920, 1080))


class TestStopScreen:
    @patch("fantomas.screen.Display")
    def test_display_stopped(self, MockDisplay):
        screen = Screen()
        screen.launch_screen()
        screen.stop_screen()
        MockDisplay.return_value.stop.assert_called_once()


class TestScreenshotScreen:
    @patch("fantomas.screen.subprocess.run")
    def test_returns_bytesio(self, mock_run):
        mock_run.return_value.stdout = b"\x89PNG\r\n\x1a\nfake_png_data"
        screen = Screen()
        result = screen.screenshot_screen()
        assert isinstance(result, io.BytesIO)
        assert result.tell() == 0
        assert result.read() == b"\x89PNG\r\n\x1a\nfake_png_data"

    @patch("fantomas.screen.subprocess.run")
    def test_empty_stdout_raises(self, mock_run):
        mock_run.return_value.stdout = b""
        screen = Screen()
        import pytest
        with pytest.raises(ValueError, match="Empty Screenshot"):
            screen.screenshot_screen()

    @patch("fantomas.screen.subprocess.run")
    def test_calls_import_command(self, mock_run):
        mock_run.return_value.stdout = b"data"
        screen = Screen()
        screen.screenshot_screen()
        mock_run.assert_called_once_with(
            ["import", "-window", "root", "png:-"],
            stdout=-1,  # subprocess.PIPE
            stderr=-3,  # subprocess.DEVNULL
        )
