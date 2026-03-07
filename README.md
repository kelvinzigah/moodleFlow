# moodleFlow
Moodle automation tool — fetches messages and forwards them to Telegram with AI parsing.

---

## Installing requirements

**Linux:**
```bash
cd "/home/kelvin/Documents/Coding Projects/moodleFlow"
venv/bin/python -m pip install -r requirements.txt
```

**Windows:**
```powershell
cd "c:/Users/KZIGAH/Desktop/Coding Projects/moodleFlow"
venv\Scripts\python -m pip install -r requirements.txt
```

---

## Installing a new package

**Linux:**
```bash
"/home/kelvin/Documents/Coding Projects/moodleFlow/venv/bin/python" -m pip install <package-name>
"/home/kelvin/Documents/Coding Projects/moodleFlow/venv/bin/python" -m pip freeze > "/home/kelvin/Documents/Coding Projects/moodleFlow/requirements.txt"
```

**Windows:**
```powershell
"c:/Users/KZIGAH/Desktop/Coding Projects/moodleFlow/venv/Scripts/python" -m pip install <package-name>
"c:/Users/KZIGAH/Desktop/Coding Projects/moodleFlow/venv/Scripts/python" -m pip freeze > "c:/Users/KZIGAH/Desktop/Coding Projects/moodleFlow/requirements.txt"
```

> Always use `python -m pip` instead of `pip` directly — the venv's pip script has a broken shebang on Linux that installs to the wrong directory.
