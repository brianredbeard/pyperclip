# coding: utf-8
import string
import unittest
import random
import os
import platform
import io
import base64
from unittest.mock import patch, mock_open

#import sys
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyperclip import _executable_exists
from pyperclip import (init_osx_pbcopy_clipboard, init_osx_pyobjc_clipboard,
                                  init_dev_clipboard_clipboard,
                                  init_qt_clipboard,
                                  init_xclip_clipboard, init_xsel_clipboard,
                                  init_wl_clipboard,
                                  init_klipper_clipboard, init_no_clipboard,
                                  init_osc52_clipboard, init_osc5522_clipboard)
from pyperclip import init_windows_clipboard
from pyperclip import init_wsl_clipboard

from pyperclip import PyperclipException

random.seed(42) # Make the "random" tests reproducible.

class _TestClipboard(unittest.TestCase):
    clipboard = None
    supports_unicode = True

    @property
    def copy(self):
        return self.clipboard[0]

    @property
    def paste(self):
        return self.clipboard[1]

    def setUp(self):
        if not self.clipboard:
            self.skipTest("Clipboard not supported.")

    def test_copy_simple(self):
        self.copy("pyper\r\nclip")

    def test_copy_paste_simple(self):
        msg = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(1000))
        self.copy(msg)
        self.assertEqual(self.paste(), msg)

    def test_copy_paste_whitespace(self):
        msg = ''.join(random.choice(string.whitespace) for _ in range(1000))
        self.copy(msg)
        self.assertEqual(self.paste(), msg)

    def test_copy_blank(self):
        self.copy('TEST')
        self.copy('')
        self.assertEqual(self.paste(), '')

    def test_copy_unicode(self):
        if not self.supports_unicode:
            raise unittest.SkipTest()
        self.copy(u"ಠ_ಠ")

    def test_copy_unicode_emoji(self):
        if not self.supports_unicode:
            raise unittest.SkipTest()
        self.copy(u"🙆")

    def test_copy_paste_unicode(self):
        if not self.supports_unicode:
            raise unittest.SkipTest()
        msg = u"ಠ_ಠ"
        self.copy(msg)
        self.assertEqual(self.paste(), msg)

    def test_copy_paste_unicode_emoji(self):
        if not self.supports_unicode:
            raise unittest.SkipTest()
        msg = u"🙆"
        self.copy(msg)
        self.assertEqual(self.paste(), msg)

    def test_non_str(self):
        # Test copying an int.
        self.copy(42)
        self.assertEqual(self.paste(), '42')

        self.copy(-1)
        self.assertEqual(self.paste(), '-1')

        # Test copying a float.
        self.copy(3.141592)
        self.assertEqual(self.paste(), '3.141592')

        # Test copying bools.
        self.copy(True)
        self.assertEqual(self.paste(), 'True')

        self.copy(False)
        self.assertEqual(self.paste(), 'False')

        # Test copying None.
        self.copy(None)
        self.assertEqual(self.paste(), 'None')

        # Test copying a list.
        self.copy([2, 4, 6, 8])
        self.assertEqual(self.paste(), '[2, 4, 6, 8]')


class TestCygwin(_TestClipboard):
    if 'cygwin' in platform.system().lower():
        clipboard = init_dev_clipboard_clipboard()


class TestWindows(_TestClipboard):
    if os.name == 'nt' or platform.system() == 'Windows':
        clipboard = init_windows_clipboard()

class TestWSL(_TestClipboard):
    if platform.system() == 'Linux':
        with open('/proc/version', 'r') as f:
            if "Microsoft" in f.read():
                clipboard = init_wsl_clipboard()


class TestOSX(_TestClipboard):
    if os.name == 'mac' or platform.system() == 'Darwin':
        try:
            import Foundation  # check if pyobjc is installed
            import AppKit
        except ImportError:
            clipboard = init_osx_pbcopy_clipboard() # TODO
        else:
            clipboard = init_osx_pyobjc_clipboard()


class TestQt(_TestClipboard):
    if os.getenv("DISPLAY"):
        try:
            import PyQt5.QtWidgets
        except ImportError:
            pass
        else:
            clipboard = init_qt_clipboard()


class TestXClip(_TestClipboard):
    if _executable_exists("xclip"):
        clipboard = init_xclip_clipboard()


class TestXSel(_TestClipboard):
    if _executable_exists("xsel"):
        clipboard = init_xsel_clipboard()


class TestWlClipboard(_TestClipboard):
    if _executable_exists("wl-copy"):
        clipboard = init_wl_clipboard()


class TestKlipper(_TestClipboard):
    if _executable_exists("klipper") and _executable_exists("qdbus"):
        clipboard = init_klipper_clipboard()


class TestOSC52(unittest.TestCase):
    copy, paste = map(staticmethod, init_osc52_clipboard())

    @patch('builtins.open', new_callable=mock_open)
    def test_copy_simple(self, mock_open_file):
        # Test basic copy functionality.
        self.copy("abc")
        expected = b'\x1b]52;c;YWJj\x07'
        mock_open_file.assert_called_once_with('/dev/tty', 'wb')
        mock_open_file().write.assert_called_once_with(expected)
        mock_open_file().flush.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    def test_copy_unicode(self, mock_open_file):
        # Test that Unicode characters are handled correctly.
        self.copy("ಠ_ಠ")
        expected = b'\x1b]52;c;4LKgX+CyoA==\x07'
        mock_open_file.assert_called_once_with('/dev/tty', 'wb')
        mock_open_file().write.assert_called_once_with(expected)

    @patch('builtins.open', new_callable=mock_open)
    def test_copy_blank(self, mock_open_file):
        # Test that blank strings are handled correctly.
        self.copy("")
        expected = b'\x1b]52;c;\x07'
        mock_open_file.assert_called_once_with('/dev/tty', 'wb')
        mock_open_file().write.assert_called_once_with(expected)

    @patch('builtins.open', new_callable=mock_open)
    def test_non_str(self, mock_open_file):
        # Test that non-string data is converted to a string.
        self.copy(123)
        expected = b'\x1b]52;c;MTIz\x07'
        mock_open_file.assert_called_once_with('/dev/tty', 'wb')
        mock_open_file().write.assert_called_once_with(expected)

    @patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,321,0"}, clear=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_copy_tmux(self, mock_open_file):
        # Verify correct tmux passthrough wrapping.
        self.copy("tmux-test")
        expected = b'\x1bPtmux;\x1b]52;c;dG11eC10ZXN0\x07\x1b\\'
        mock_open_file.assert_called_once_with('/dev/tty', 'wb')
        mock_open_file().write.assert_called_once_with(expected)

    @patch.dict(os.environ, {"TERM": "screen.xterm-256color"}, clear=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_copy_screen(self, mock_open_file):
        # Verify correct screen passthrough wrapping.
        self.copy("screen-test")
        expected = b'\x1bP\x1b]52;c;c2NyZWVuLXRlc3Q=\x07\x1b\\'
        mock_open_file.assert_called_once_with('/dev/tty', 'wb')
        mock_open_file().write.assert_called_once_with(expected)

    @patch('builtins.open', new_callable=mock_open)
    def test_copy_primary(self, mock_open_file):
        # Test copying to the primary selection.
        self.copy("primary-test", primary=True)
        expected = b'\x1b]52;p;cHJpbWFyeS10ZXN0\x07'
        mock_open_file.assert_called_once_with('/dev/tty', 'wb')
        mock_open_file().write.assert_called_once_with(expected)

    @patch('builtins.open', new_callable=mock_open)
    def test_large_payload(self, mock_open_file):
        # Ensure that large payloads are handled correctly without chunking.
        large_text = "A" * 5000
        self.copy(large_text)
        b64_text = base64.b64encode(large_text.encode('utf-8'))
        expected = b'\x1b]52;c;' + b64_text + b'\x07'
        mock_open_file().write.assert_called_once_with(expected)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.open', side_effect=OSError)
    def test_copy_fallback_to_stdout(self, mock_open, mock_stdout):
        # The buffer attribute is used, so we need to mock it.
        mock_stdout.buffer = io.BytesIO()
        self.copy("fallback")
        expected = b'\x1b]52;c;ZmFsbGJhY2s=\x07'
        mock_stdout.buffer.seek(0)
        self.assertEqual(mock_stdout.buffer.read(), expected)

    def test_paste(self):
        # Test that paste is not supported and raises an exception.
        with self.assertRaises(PyperclipException):
            self.paste()


class TestOSC5522(unittest.TestCase):
    copy, paste = map(staticmethod, init_osc5522_clipboard())

    @patch('builtins.open', new_callable=mock_open)
    def test_copy_simple(self, mock_open_file):
        # Test basic copy functionality.
        self.copy("abc")

        calls = mock_open_file().write.call_args_list
        self.assertEqual(len(calls), 3)

        expected_start = b'\x1b]5522;type=write\x1b\\'
        expected_data = b'\x1b]5522;type=wdata:mime=text/plain;YWJj\x1b\\'
        expected_end = b'\x1b]5522;type=wdata\x1b\\'

        self.assertEqual(calls[0].args[0], expected_start)
        self.assertEqual(calls[1].args[0], expected_data)
        self.assertEqual(calls[2].args[0], expected_end)

    @patch('builtins.open', new_callable=mock_open)
    def test_copy_chunking(self, mock_open_file):
        # Test that large data is correctly split into chunks.
        long_text = "A" * 5000
        self.copy(long_text)

        calls = mock_open_file().write.call_args_list
        self.assertEqual(len(calls), 4) # start, data chunk 1, data chunk 2, end

        # Check start and end
        self.assertEqual(calls[0].args[0], b'\x1b]5522;type=write\x1b\\')
        self.assertEqual(calls[3].args[0], b'\x1b]5522;type=wdata\x1b\\')

        # Check data chunks
        chunk1 = long_text.encode('utf-8')[:4096]
        b64_chunk1 = base64.b64encode(chunk1)
        expected_data1 = b'\x1b]5522;type=wdata:mime=text/plain;' + b64_chunk1 + b'\x1b\\'
        self.assertEqual(calls[1].args[0], expected_data1)

        chunk2 = long_text.encode('utf-8')[4096:]
        b64_chunk2 = base64.b64encode(chunk2)
        expected_data2 = b'\x1b]5522;type=wdata:mime=text/plain;' + b64_chunk2 + b'\x1b\\'
        self.assertEqual(calls[2].args[0], expected_data2)

    @patch('builtins.open', new_callable=mock_open)
    def test_copy_blank(self, mock_open_file):
        # Test that blank strings are handled correctly.
        self.copy("")
        calls = mock_open_file().write.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0].args[0], b'\x1b]5522;type=write\x1b\\')
        self.assertEqual(calls[1].args[0], b'\x1b]5522;type=wdata:mime=text/plain;\x1b\\')
        self.assertEqual(calls[2].args[0], b'\x1b]5522;type=wdata\x1b\\')

    @patch('builtins.open', new_callable=mock_open)
    def test_copy_primary(self, mock_open_file):
        # Test copying to the primary selection.
        self.copy("primary-test", primary=True)
        calls = mock_open_file().write.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0].args[0], b'\x1b]5522;type=write:loc=primary\x1b\\')

    @patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,321,0"}, clear=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_copy_tmux(self, mock_open_file):
        # Verify correct tmux passthrough wrapping.
        self.copy("tmux-test")
        calls = mock_open_file().write.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0].args[0], b'\x1bPtmux;\x1b]5522;type=write\x1b\\')
        self.assertEqual(calls[1].args[0], b'\x1bPtmux;\x1b]5522;type=wdata:mime=text/plain;dG11eC10ZXN0\x1b\\')
        self.assertEqual(calls[2].args[0], b'\x1bPtmux;\x1b]5522;type=wdata\x1b\\')

    @patch.dict(os.environ, {"TERM": "screen.xterm-256color"}, clear=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_copy_screen(self, mock_open_file):
        # Verify correct screen passthrough wrapping.
        self.copy("screen-test")
        calls = mock_open_file().write.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0].args[0], b'\x1bP\x1b]5522;type=write\x1b\\')
        self.assertEqual(calls[1].args[0], b'\x1bP\x1b]5522;type=wdata:mime=text/plain;c2NyZWVuLXRlc3Q=\x1b\\')
        self.assertEqual(calls[2].args[0], b'\x1bP\x1b]5522;type=wdata\x1b\\')

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.open', side_effect=OSError)
    def test_copy_fallback_to_stdout(self, mock_open, mock_stdout):
        # The buffer attribute is used, so we need to mock it.
        mock_stdout.buffer = io.BytesIO()
        self.copy("fallback")
        expected = b'\x1b]5522;type=write\x1b\\\x1b]5522;type=wdata:mime=text/plain;ZmFsbGJhY2s=\x1b\\\x1b]5522;type=wdata\x1b\\'
        mock_stdout.buffer.seek(0)
        self.assertEqual(mock_stdout.buffer.read(), expected)

    def test_paste(self):
        # Test that paste is not supported and raises an exception.
        with self.assertRaises(PyperclipException):
            self.paste()


class TestNoClipboard(unittest.TestCase):
    copy, paste = init_no_clipboard()

    def test_copy(self):
        with self.assertRaises(RuntimeError):
            self.copy("foo")

    def test_paste(self):
        with self.assertRaises(RuntimeError):
            self.paste()


if __name__ == '__main__':
    unittest.main()
