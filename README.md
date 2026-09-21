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
│   └── docx/
│       ├── HW0.docx
│       ├── HW1.docx
│       ├── HW2.docx
│       ├── HW3.docx
│       └── HW4.docx
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

The script loops through `HW0.docx` to `HW4.docx`. For each file, it:

1. Runs `office2john.py`.
2. Writes the extracted Office hash to `src/docxhash.txt`.
3. Runs Hashcat in Office 2013 mode (`-m 9600`).
4. Tests passwords of length 6–8 containing only lowercase English letters and digits.

The Hashcat mask uses `?l?d` as its custom character set and the increment range `6` through `8`.
