# Cyber Security Homework

Cyber-security homework files and DOCX password-recovery experiments.

> Use these tools only with files you own or have permission to test.

## Project Structure

```text
.
├── README.md
├── src/
│   ├── Cyberser2.py
│   ├── office2john.py
│   ├── docxhash.txt
│   ├── docx/
│   │   ├── HW0.docx
│   │   ├── HW1.docx
│   │   ├── HW2.docx
│   │   ├── HW3.docx
│   │   └── HW4.docx
│   └── wordlists/
│       ├── Pwdb_top-1000000.txt
│       ├── darkweb2017_top-10000.txt
│       └── myspace.txt
└── hashcat/
    └── Hashcat executable and dependencies go here
```

## Requirements

- Python 3
- `olefile`: `pip install olefile`
- Hashcat for Windows, extracted into `hashcat/`

## Run

From the repository root:

```powershell
python src\Cyberser2.py
```

The script processes `HW2.docx` and `HW3.docx`.

The entire `hashcat/` installation, `src/docx/` input folder, and generated `src/docxhash.txt` are local-only and ignored by Git. Supply your authorized DOCX files in `src/docx/` and extract Hashcat into `hashcat/` before running. Wordlists, their licenses, and the script are versioned.

### Attack modes

1. **Mask only:** tests passwords of length 6–8 using lowercase English letters and digits, in any order.
2. **English vocabulary + trailing digits (default):** press Enter at the mode prompt. Uses `src/wordlists/english-scowl60.txt`, a SCOWL ordinary-word vocabulary including US/UK spellings and inflections (see `SCOWL-SOURCE.md` and `SCOWL-LICENSE.md`). It does not use the password lists as vocabulary. Entries are lowercase ASCII words of length 2–7. Single letters are excluded; two-letter entries use a conservative common-word allowlist (e.g. `go`, `in`, `to`, excluding `ab`). Three-letter and longer entries remain dictionary-derived; this finite dictionary does not cover every English word.
   Search order is total length **7, then 6, then 8**, finishing each total length before the next. Each word receives exactly enough trailing digits to reach the target length, with at least one digit. Leading zeroes are included. For `cat`: `cat0000`–`cat9999`, then `cat000`–`cat999`, then `cat00000`–`cat99999`. Within each total length, longer words/fewer digits are searched first. No digit prefixes or interleaved forms are generated.
   Pins `-d 1` to the verified CUDA RTX 5090 Laptop on this machine (check `hashcat -I` and update `HASHCAT_DEVICE` on other machines). Uses mode 0 with stacked append-digit rules and `--slow-candidates` for host-generated GPU batches. Temporary wordlists/rules are removed on normal exit. Finding a password stops that document's remaining work; the script then continues with the next configured document. Existing running processes must be restarted by the user to load changes.
3. **Wordlist + custom rules:** preserves the existing wordlist/rule workflow; its default rule is `hashcat/rules/best66.rule`. The 6–8-character constraint applies to mode 2, not custom rules.

Verify without cracking documents:

```powershell
python -m unittest discover -s tests -v
```

The bundled password lists come from the MIT-licensed [SecLists project](https://github.com/danielmiessler/SecLists).
