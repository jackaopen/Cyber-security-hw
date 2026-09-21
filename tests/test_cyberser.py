import contextlib
import importlib.util
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "src" / "Cyberser2.py"
spec = importlib.util.spec_from_file_location("cyberser", SCRIPT)
cyberser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cyberser)


class WordDigitsTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.wordlist = Path(self.temp.name) / "words.txt"
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def test_normalization_and_filtering(self):
        self.wordlist.write_bytes(b"Hello\r\nhello\nCAT\na\nabcdefg\nabcdefgh\ncat123\n123\nhi!\n hi\n\xff\n")
        self.assertEqual(cyberser.collect_words([self.wordlist, self.wordlist]),
                         {"hello", "cat", "abcdefg"})

    def test_single_letters_and_nonword_pairs_are_excluded(self):
        self.wordlist.write_text("a\nb\ni\nz\nab\naa\nzz\nGO\nin\nto\ncat\n")
        self.assertEqual(cyberser.collect_words([self.wordlist]), {"go", "in", "to", "cat"})
        vocabulary = cyberser.DEFAULT_VOCAB.read_text(encoding="ascii").splitlines()
        self.assertTrue(all(2 <= len(word) <= 7 for word in vocabulary))
        self.assertEqual({word for word in vocabulary if len(word) == 2},
                         cyberser.COMMON_TWO_LETTER_WORDS)

    def test_all_length_splits_and_seven_first_suffix_only(self):
        self.wordlist.write_text("go\ncat\nking\nphone\nlittle\nanother\n")
        seen = set()
        totals = []
        temporary_files = []

        def exhausted(command, **kwargs):
            mode = command[command.index("-a") + 1]
            first = command.index("-a") + 2
            word_file = Path(command[first])
            word = word_file.read_text().strip()
            self.assertEqual(mode, "0")
            self.assertIn("--slow-candidates", command)
            low = high = command.count("-r")
            rule_lines = Path(command[command.index("-r") + 1]).read_text().splitlines()
            operator = rule_lines[0][0]
            self.assertEqual(operator, "$")
            self.assertEqual(command[command.index("-d") + 1], "1")
            for index, arg in enumerate(command):
                if arg == "-r":
                    self.assertEqual(Path(command[index + 1]).read_text().splitlines(),
                                     [operator + str(digit) for digit in range(10)])
            mode = "6" if operator == "$" else "7"  # Logical suffix/prefix direction.
            self.assertEqual(kwargs["cwd"], cyberser.HASHCAT_DIR)
            temporary_files.append(word_file)
            for digits in range(low, high + 1):
                seen.add((mode, len(word), digits))
                totals.append(len(word) + digits)
            return SimpleNamespace(returncode=1)

        with patch.object(cyberser.subprocess, "run", side_effect=exhausted) as run:
            self.assertEqual(cyberser.run_hashcat("word_digits", [self.wordlist]), 1)
        expected = {(mode, letters, digits) for mode in ("6",)
                    for letters in range(2, 8) for digits in range(1, 8)
                    if 6 <= letters + digits <= 8}
        self.assertEqual(seen, expected)
        self.assertEqual(run.call_count, 15)
        self.assertEqual(totals, [7] * 5 + [6] * 4 + [8] * 6)
        self.assertTrue(all(not path.exists() for path in temporary_files))

    def test_success_and_errors_stop_remaining_work(self):
        self.wordlist.write_text("hello\ncat\n")
        for code in (0, 2, -1):
            with self.subTest(code=code), patch.object(
                cyberser.subprocess, "run", return_value=SimpleNamespace(returncode=code)
            ) as run:
                self.assertEqual(cyberser.run_hashcat("word_digits", [self.wordlist]), code)
                run.assert_called_once()

    def test_empty_filtered_dictionary_does_not_start_hashcat(self):
        self.wordlist.write_text("123456\nabcdefgh\n")
        with patch.object(cyberser.subprocess, "run") as run:
            self.assertEqual(cyberser.run_hashcat("word_digits", [self.wordlist]), 1)
            run.assert_not_called()

    def test_enter_uses_real_vocabulary_without_password_list_prompt(self):
        with patch("builtins.input", return_value="") as prompt:
            self.assertEqual(cyberser.choose_attack(),
                             ("word_digits", [cyberser.DEFAULT_VOCAB], None))
            prompt.assert_called_once()
        vocabulary = cyberser.collect_words([cyberser.DEFAULT_VOCAB])
        self.assertTrue({"cat", "king", "phone", "hello"} <= vocabulary)
        self.assertFalse({"asdfjkl", "zzzzzzz", "aaaaa"} & vocabulary)

    def test_missing_vocabulary_does_not_fall_back_to_password_lists(self):
        with patch.object(cyberser, "DEFAULT_VOCAB", Path(self.temp.name) / "missing.txt"), \
                patch("builtins.input", return_value=""):
            self.assertEqual(cyberser.choose_attack(), (None, None, None))

    def test_cat_uses_four_then_three_then_five_trailing_digits(self):
        self.wordlist.write_text("cat\n")
        with patch.object(cyberser.subprocess, "run", return_value=SimpleNamespace(returncode=1)) as run:
            cyberser.run_hashcat("word_digits", [self.wordlist])
        self.assertEqual([call.args[0].count("-r") for call in run.call_args_list], [4, 3, 5])

    def test_existing_modes_remain_available(self):
        with patch("builtins.input", return_value="1"):
            self.assertEqual(cyberser.choose_attack(), ("mask", None, None))
        rule = Path(self.temp.name) / "custom.rule"
        rule.write_text(":\n")
        with patch.object(cyberser, "choose_wordlists", return_value=[self.wordlist]), \
                patch("builtins.input", side_effect=["3", str(rule)]):
            self.assertEqual(cyberser.choose_attack(), ("rules", [self.wordlist], rule))


if __name__ == "__main__":
    unittest.main()
