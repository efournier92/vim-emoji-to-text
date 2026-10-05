"""Encoding guard: a non-UTF-8 Vim must not throw over the data module.

The map only makes sense in a UTF-8 buffer, so the engine should decline
cleanly instead of failing with E721 when it sources data.vim under a
non-UTF-8 `&encoding`. Neovim is always UTF-8, so this exercises Vim.

    python3 test/test_encoding.py
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class EncodingTest(unittest.TestCase):
    def test_non_utf8_encoding_declines_without_error(self):
        vim = shutil.which("vim")
        if not vim:
            self.skipTest("vim not available")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "buffer.txt"
            target.write_text("plain text\n", encoding="utf-8")
            command = [
                vim,
                "-Nu",
                "NONE",
                "-N",
                "-es",
                "--cmd",
                "set rtp+=%s" % ROOT,
                "--cmd",
                "set encoding=latin1",
                "-c",
                "runtime plugin/emoji_to_text.vim",
                "-c",
                "EmojiToText",
                "-c",
                "qa!",
                str(target),
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertNotIn("E721", output)
            self.assertEqual(target.read_text(encoding="utf-8"), "plain text\n")


if __name__ == "__main__":
    unittest.main()
