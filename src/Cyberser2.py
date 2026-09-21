from pathlib import Path
import subprocess
import sys


SRC_DIR = Path(__file__).resolve().parent
REPO_DIR = SRC_DIR.parent

JOHN_SCRIPT = SRC_DIR / "office2john.py"
DOCX_DIR = SRC_DIR / "docx"
HASH_FILE = SRC_DIR / "docxhash.txt"
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


def run_hashcat() -> int:
    command = [
        str(HASHCAT_EXE),
        "-m", HASH_MODE,
        str(HASH_FILE),
        "-a", "3",
        "-1", CHARSET,
        MASK,
        "--increment",
        "--increment-min", "6",
        "--increment-max", "8",
    ]

    return subprocess.run(command, cwd=HASHCAT_DIR).returncode


def main() -> None:
    if not JOHN_SCRIPT.exists():
        print(f"Missing file: {JOHN_SCRIPT}")
        return

    if not HASHCAT_EXE.exists():
        print(f"Missing file: {HASHCAT_EXE}")
        return

    for number in range(5):
        docx_file = DOCX_DIR / f"HW{number}.docx"

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

        exit_code = run_hashcat()
        print(f"Hashcat finished with exit code {exit_code}")


if __name__ == "__main__":
    main()
