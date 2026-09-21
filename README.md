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

The script processes `HW0.docx`, `HW2.docx`, and `HW3.docx`.

### Attack modes

1. **Mask only:** tests passwords of length 6–8 using lowercase English letters and digits.
2. **Wordlist + rules:** select one bundled wordlist, all bundled wordlists, or enter a custom path. The default rule file is `hashcat/rules/best64.rule`.

The bundled password lists come from the MIT-licensed [SecLists project](https://github.com/danielmiessler/SecLists).
