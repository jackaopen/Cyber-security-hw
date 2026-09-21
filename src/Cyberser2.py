from pathlib import Path
import subprocess
import sys


SRC_DIR = Path(__file__).resolve().parent
REPO_DIR = SRC_DIR.parent

JOHN_SCRIPT = SRC_DIR / "office2john.py"
DOCX_DIR = SRC_DIR / "docx"
HASH_FILE = SRC_DIR / "docxhash.txt"
WORDLIST_DIR = SRC_DIR / "wordlists"
HASHCAT_DIR = REPO_DIR / "hashcat"
HASHCAT_EXE = HASHCAT_DIR / "hashcat.exe"

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


def run_hashcat(
    attack_mode: str,
    wordlists=None,
    rule_file: Path = None,
) -> int:
    base_command = [
        str(HASHCAT_EXE),
        "-m", HASH_MODE,
        str(HASH_FILE),
    ]

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
    print("2. Wordlist + rules")

    choice = input("Option: ").strip()

    if choice == "1":
        return "mask", None, None

    if choice != "2":
        print("Invalid option")
        return None, None, None

    wordlists = choose_wordlists()

    if wordlists is None:
        return None, None, None

    default_rule = HASHCAT_DIR / "rules" / "best64.rule"
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

    for hw in [0, 2, 3]:
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
