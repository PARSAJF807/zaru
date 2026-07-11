# 🔐 zaru - Cli Encryption Tool

[![Version](https://img.shields.io/badge/version-2.1.1-blue.svg)](https://github.com/PARSAJF807/zaru/releases)
[![Python](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Algorithm](https://img.shields.io/badge/algorithm-XChaCha20--Poly1305-orange.svg)](https://en.wikipedia.org/wiki/ChaCha20)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Termux%20%7C%20Windows-lightgrey.svg)]()
[![Made with](https://img.shields.io/badge/made%20with-Python-red.svg)](https://www.python.org/)

---

## 📖 Overview

**Zaru** is a powerful command-line tool that encrypts your source code (Python, JavaScript, PHP, C, C++, Java, Go, Rust, Ruby, Perl, Bash, Lua, TypeScript, HTML) into a **self-decrypting loader** using the **XChaCha20-Poly1305** algorithm — the same encryption used in **Signal**, **WhatsApp**, and **Google** products.

With Zaru, you can:
- 🔒 **Obfuscate** your code with military-grade encryption
- 🚀 **Distribute** your application as a single encrypted loader
- 🧩 **Support** multiple programming languages
- 🕵️ **Hide errors** in production (stealth mode)
- 🔍 **Debug** with verbose error output

---

## ✨ Features

- ✅ **XChaCha20-Poly1305** encryption (Quantum-resistant)
- ✅ **24-byte nonce** for enhanced security
- ✅ **Multi-language support** (15+ languages)
- ✅ **Self-decrypting loader** (no external dependencies at runtime)
- ✅ **Stealth mode** (hides errors by default)
- ✅ **Debug mode** for development
- ✅ **Decryption utility** to recover original code
- ✅ **Automatic file compression** (zlib level 9)
- ✅ **Cross-platform** (Linux, Termux, Windows)
- ✅ **ASCII banner** with `toilet` support (fallback included)

---

## 🔧 Installation

### 📦 Method 1: Quick Install (Recommended)

```bash
git clone https://github.com/PARSAJF807/zaru.git && cd zaru && mv zaru.py ~/bin/zaru && chmod +x ~/bin/zaru && zaru -h
```
## 📦 Method 2: Manual (Just run directly)

```bash
git clone https://github.com/PARSAJF807/zaru.git
cd zaru
python zaru.py -h
```

---

🚀 Usage

Encrypt a file

```bash
zaru -k "YourSuperSecretKey123!" -i input_file.py -o loader.py
```

Encrypt with debug mode (show errors in loader)

```bash
zaru -k "YourSuperSecretKey123!" -i input_file.py -o loader.py --debug
```

Decrypt a loader file back to original

```bash
zaru --decrypt -k "YourSuperSecretKey123!" -i loader.py -o original.py
```

Decrypt without specifying output (auto-generated name)

```bash
zaru --decrypt -k "YourSuperSecretKey123!" -i loader.py
```

Show help

```bash
zaru -h
```

---

🧪 Examples

Python

```bash
zaru -k "MySecretKey2025" -i app.py -o secure_app.py
python secure_app.py  # Runs the decrypted code
```

JavaScript (Node.js)

```bash
zaru -k "MySecretKey2025" -i script.js -o loader.js
node loader.js
```

C Program

```bash
zaru -k "MySecretKey2025" -i program.c -o loader
./loader  # Compiled and executed
```

PHP

```bash
zaru -k "MySecretKey2025" -i index.php -o loader.php
php loader.php
```

HTML (Opens in browser)

```bash
zaru -k "MySecretKey2025" -i index.html -o loader.html
# The loader will automatically open in your default browser
```

---

## 🛠️ Command-line Options

Option Description
-k, --key Encryption/Decryption key (minimum 12 characters)
-i, --input Input file (source code or loader)
-o, --output Output file (loader or decrypted code)
--debug Enable debug mode (shows errors in loader)
--decrypt Decrypt a loader file back to original code
-v, --version Show version information
-h, --help Show help message

---

## 🔐 Security Notes

· Key Storage: The key is stored in the loader as base64. This provides obfuscation, not real security. For production-grade protection:

  · ✅ Use a remote licensing server to validate keys (API)
  
  · ✅ Bind the key to hardware (MAC address, CPU ID)
  
  · ✅ Use PyArmor or Nuitka for additional obfuscation
  
  · ✅ Never store sensitive keys in plain text
  
· Algorithm: XChaCha20-Poly1305 is quantum-resistant and considered military-grade encryption.
· Key Requirements:
  · Minimum 12 characters
  · Mix of uppercase, lowercase, numbers, and symbols
  · Example: MyS3cr3tK3y!@#2025

---

## 📦 Requirements

· Python 3.13 or higher
· pycryptodome library

Install dependencies

```bash
pip install pycryptodome

OR

pip -r requirements.txt
```

---

## 🌍 Supported Languages

Extension Language Interpreter
.py Python python3
.js JavaScript node
.php PHP php
.c C gcc
.cpp C++ g++
.sh Bash bash
.rb Ruby ruby
.pl Perl perl
.go Go go run
.rs Rust rustc
.java Java javac
.lua Lua lua
.ts TypeScript ts-node
.html HTML (opens in browser)

---

## 🧪 Testing

To verify your installation:

```bash
# Create a test file
echo 'print("Hello from Zaru!")' > test.py

# Encrypt it
zaru -k "TestKey123456" -i test.py -o loader.py

# Run the loader
python loader.py
# Output: Hello from Zaru!

# Decrypt it back
zaru --decrypt -k "TestKey123456" -i loader.py -o recovered.py

# Compare
diff test.py recovered.py  # Should show no differences
```

---

## 🤝 Feedback & Improvements

Found a bug or have an idea to make Zaru better? I'd love to hear from you!

**Ways to contribute:**
- 🐛 **Bug Reports:** Open an issue on GitHub with details about the problem
- 💡 **Feature Ideas:** Share your suggestions in GitHub Discussions ("I welcome your ideas and suggestions, and I will implement them whenever possible.")
- 🔒 **Security Issues:** Please report problems, bugs, etc. via the general report.

**Note:** This project is released under the MIT License and forking is allowed. However, to get the latest updates, bug fixes, and official support, it is recommended to always use the main repository. Forked versions may be outdated or contain unverified changes that may compromise your security and your system.

---

### 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## ⚠️ Disclaimer

This tool is for educational and obfuscation purposes only. It does not provide 100% security against determined reverse engineering. For sensitive applications, use a combination of obfuscation, hardware binding, and server-side validation.

---

### 📞 Support

· Issues: GitHub Issues
· Discussions: GitHub Discussions
· Email: parsajf@example.com

---

### Made with ❤️ #zaru
