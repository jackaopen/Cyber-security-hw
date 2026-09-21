from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


SRC_DIR = Path(__file__).resolve().parent
REPO_DIR = SRC_DIR.parent

JOHN_SCRIPT = SRC_DIR / "office2john.py"
DOCX_DIR = SRC_DIR / "docx"
HASH_FILE = SRC_DIR / "docxhash.txt"
WORDLIST_DIR = SRC_DIR / "wordlists"
DEFAULT_VOCAB = WORDLIST_DIR / "english-scowl60.txt"
TARGET_LENGTHS = (7, 6, 8)
# Deliberately conservative: exclude letter names and obscure two-letter entries.
COMMON_TWO_LETTER_WORDS = frozenset(
    "am an as at be by do go he hi if in is it me my no of oh on or ox so to up us we".split()
)
HASHCAT_DIR = REPO_DIR / "hashcat"
HASHCAT_EXE = HASHCAT_DIR / "hashcat.exe"

HASHCAT_DEVICE = "1"  # This laptop: CUDA RTX 5090; verify with hashcat -I on other PCs.
HASH_MODE = "9600"  # Microsoft Office 2013
CHARSET = "?l?d"     # lowercase letters and digits
MASK = "?1" * 8      # maximum length: 8


def extract_hash(docx_file: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(JOHN_SCRIPT), str(docx_file)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "office2john failed")

    output = result.stdout.strip()

    if ":" not in output:
        raise RuntimeError("No Office hash was found")

    # office2john returns: filename:$office$*...
    return output.split(":", 1)[1]


def collect_words(wordlists):
    """Keep 2-7 letter entries; two-letter entries must be common words."""
    words = set()
    for wordlist in wordlists:
        with wordlist.open("rb") as source:
            for line in source:
                word = line.rstrip(b"\r\n").lower()
                if 2 <= len(word) <= 7 and all(97 <= c <= 122 for c in word):
                    text = word.decode("ascii")
                    if len(text) > 2 or text in COMMON_TWO_LETTER_WORDS:
                        words.add(text)
    return words


def run_word_digits(base_command, wordlists):
    words = collect_words(wordlists)
    if not words:
        print("No eligible English words of length 2-7 in the selected wordlists")
        return 1

    candidate_count = sum(
        10 ** (total - len(word))
        for total in TARGET_LENGTHS for word in words if len(word) < total
    )
    print(f"English word + trailing digits: {len(words):,} words, "
          f"{candidate_count:,} candidates; total length order 7, 6, 8")

    with TemporaryDirectory(prefix="cyberser-words-") as directory:
        rule = Path(directory) / "append.rule"
        rule.write_text("".join(f"${digit}\n" for digit in range(10)), encoding="ascii")
        groups = {}
        for length in range(2, 8):
            selected = sorted(word for word in words if len(word) == length)
            if selected:
                word_file = Path(directory) / f"words-{length}.txt"
                word_file.write_text("\n".join(selected) + "\n", encoding="ascii")
                groups[length] = word_file
        # Complete every seven-character candidate before starting six or eight.
        # Within a total length, try fewer trailing digits first.
        for total in TARGET_LENGTHS:
            for length in sorted(groups, reverse=True):
                digits = total - length
                if digits < 1:
                    continue
                command = base_command + [
                    "-a", "0", str(groups[length]), "--slow-candidates",
                    *[argument for _ in range(digits)
                      for argument in ("-r", str(rule))],
                ]
                print(f"Total {total}: {length}-letter word + {digits} digits (host candidates)")
                exit_code = subprocess.run(command, cwd=HASHCAT_DIR).returncode
                if exit_code != 1:
                    return exit_code
    return 1


def run_hashcat(
    attack_mode: str,
    wordlists=None,
    rule_file: Path = None,
) -> int:
    base_command = [
        str(HASHCAT_EXE),
        "-m", HASH_MODE,
        "-d", HASHCAT_DEVICE,
        str(HASH_FILE),
    ]

    if attack_mode == "word_digits":
        return run_word_digits(base_command, wordlists)

    if attack_mode == "mask":
        command = base_command + [
            "-a", "3",
            "-1", CHARSET,
            MASK,
            "--increment",
            "--increment-min", "6",
            "--increment-max", "8",
        ]
        return subprocess.run(command, cwd=HASHCAT_DIR).returncode

    for wordlist in wordlists:
        print(f"Using wordlist: {wordlist.name}")

        command = base_command + [
            "-a", "0",
            str(wordlist),
            "-r", str(rule_file),
        ]

        exit_code = subprocess.run(
            command,
            cwd=HASHCAT_DIR,
        ).returncode

        # Hashcat exit code 0 means the hash was cracked.
        if exit_code == 0:
            return 0

        # Exit code 1 means this wordlist was exhausted.
        if exit_code != 1:
            return exit_code

    return 1


def choose_wordlists():
    included = sorted(WORDLIST_DIR.glob("*.txt"))

    if not included:
        print(f"No wordlists found in {WORDLIST_DIR}")
        return None

    print("\nAvailable wordlists:")
    print("0. All included wordlists")

    for number, wordlist in enumerate(included, start=1):
        print(f"{number}. {wordlist.name}")

    choice = input(
        "Choose a number, press Enter for all, "
        "or enter a custom path: "
    ).strip().strip('"')

    if choice in ("", "0"):
        return included

    if choice.isdigit():
        number = int(choice)

        if 1 <= number <= len(included):
            return [included[number - 1]]

        print("Invalid wordlist number")
        return None

    custom_wordlist = Path(choice).expanduser().resolve()

    if not custom_wordlist.is_file():
        print(f"Missing wordlist: {custom_wordlist}")
        return None

    return [custom_wordlist]


def choose_attack():
    print("\nChoose attack mode:")
    print("1. Mask only (6-8 lowercase letters or digits)")
    print("2. English word + trailing digits (7, then 6, then 8 total; default)")
    print("3. Wordlist + custom rules")

    choice = input("Option [2]: ").strip() or "2"

    if choice == "1":
        return "mask", None, None

    if choice not in ("2", "3"):
        print("Invalid option")
        return None, None, None

    if choice == "2":
        if not DEFAULT_VOCAB.is_file():
            print(f"Missing English vocabulary: {DEFAULT_VOCAB}")
            return None, None, None
        print(f"Using English vocabulary: {DEFAULT_VOCAB.name}")
        return "word_digits", [DEFAULT_VOCAB], None

    wordlists = choose_wordlists()
    if wordlists is None:
        return None, None, None

    default_rule = HASHCAT_DIR / "rules" / "best66.rule"
    rule_text = input(f"Rule file [{default_rule}]: ").strip().strip('"')
    rule_file = (
        Path(rule_text).expanduser().resolve()
        if rule_text
        else default_rule
    )

    if not rule_file.is_file():
        print(f"Missing rule file: {rule_file}")
        return None, None, None

    return "rules", wordlists, rule_file


def main() -> None:
    if not JOHN_SCRIPT.exists():
        print(f"Missing file: {JOHN_SCRIPT}")
        return

    if not HASHCAT_EXE.exists():
        print(f"Missing file: {HASHCAT_EXE}")
        return

    attack_mode, wordlists, rule_file = choose_attack()

    if attack_mode is None:
        return

    for hw in [2, 3]:
        docx_file = DOCX_DIR / f"HW{hw}.docx"

        if not docx_file.exists():
            print(f"Skip: {docx_file.name} was not found")
            continue

        print(f"\nProcessing {docx_file.name}...")

        try:
            office_hash = extract_hash(docx_file)
        except RuntimeError as error:
            print(f"Failed: {error}")
            continue

        HASH_FILE.write_text(office_hash + "\n", encoding="utf-8")
        print(f"Hash written to {HASH_FILE.name}")

        exit_code = run_hashcat(
            attack_mode,
            wordlists,
            rule_file,
        )
        print(f"Hashcat finished with exit code {exit_code}")


if __name__ == "__main__":
    main()
