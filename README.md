# Cyber Security Homework

Cyber-security homework files and DOCX password-recovery experiments.

> Use these tools only with files you own or have permission to test.

## Project Structure

```text
.
├── README.md
├── src/
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

`Cyberser2.py` will be added after its code review.

## Requirements

- Python 3
- `olefile`: `pip install olefile`
- Hashcat for Windows, extracted into `hashcat/`

## DOCX Password-Recovery Flow

1. Extract the Office password hash:

```powershell
python src\office2john.py src\docx\HW0.docx > src\docxhash.txt
```

2. Run Hashcat from the repository root:

```powershell
.\hashcat\hashcat.exe -m 9600 src\docxhash.txt -a 3 ?1?1?1?1?1?1 --custom-charset1=?l?d
```

The example mask tests six-character passwords containing lowercase English letters and digits. Change the mask only for your own authorized files.
