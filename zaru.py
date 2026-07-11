#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Zaru v2.1.0 - Quantum Encryption Tool (XChaCha20-Poly1305)
Author: Tiana Lab
License: MIT
Python 3.13+ compatible
"""

import os
import sys
import hashlib
import zlib
import argparse
import base64
import subprocess
import logging
import tempfile
import shutil
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Union, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes

# ==================== CONSTANTS ====================
VERSION = "2.1.0"
TOOL_NAME = "zaru"
MIN_KEY_LENGTH = 12  # XChaCha20 توصیه می‌کنه حداقل ۱۲ کاراکتر
ALGORITHM = "XChaCha20-Poly1305"
UPDATE_CHECK_INTERVAL = 7 * 24 * 3600  # 7 days in seconds
CACHE_DIR = Path.home() / ".config" / "zaru"
CACHE_FILE = CACHE_DIR / "update_cache.json"
GITHUB_REPO = "PARSAJF807/zaru"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/zaru.py"

# ==================== LOGGING SETUP ====================
class LoggerSetup:
    """Centralized logging configuration"""
    @staticmethod
    def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(level)
        return logger

# ==================== BANNER GENERATOR ====================
class BannerGenerator:
    """Handles ASCII banner generation using toilet or fallback"""
    @staticmethod
    def generate() -> str:
        try:
            # Try to use toilet for fancy banner
            result = subprocess.check_output(
                ["toilet", "-f", "mono12", "-F", "metal", TOOL_NAME],
                stderr=subprocess.DEVNULL,
                text=True
            )
            banner = result
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback simple banner
            banner = f"""
╔═══════════════════════════════════════════════════════════╗
║   🔥 Zaru v{VERSION} - Quantum Encryption Tool            ║
║   🧠 XChaCha20-Poly1305 (Signal Protocol)               ║
║   🔐 Military-Grade Security                            ║
╚═══════════════════════════════════════════════════════════╝
"""
        return banner

# ==================== CUSTOM EXCEPTIONS ====================
class ZaruError(Exception):
    """Base exception for Zaru"""
    pass

class KeyValidationError(ZaruError):
    """Raised when key is invalid"""
    pass

class FileValidationError(ZaruError):
    """Raised when file is invalid"""
    pass

class EncryptionError(ZaruError):
    """Raised when encryption fails"""
    pass

class DecryptionError(ZaruError):
    """Raised when decryption fails"""
    pass

class UpdateError(ZaruError):
    """Raised when update process fails"""
    pass

# ==================== DATA CLASSES ====================
@dataclass
class EncryptionContext:
    """Context container for encryption process"""
    input_path: Path
    output_path: Path
    key: str
    debug: bool = False
    logger: Optional[logging.Logger] = None

@dataclass
class DecryptionContext:
    """Context container for decryption process"""
    input_path: Path
    output_path: Optional[Path] = None
    debug: bool = False
    logger: Optional[logging.Logger] = None

# ==================== KEY MANAGER ====================
class KeyManager:
    """Handles key validation and hashing"""
    @staticmethod
    def validate(raw_key: str) -> bytes:
        if len(raw_key) < MIN_KEY_LENGTH:
            raise KeyValidationError(
                f"Key must be at least {MIN_KEY_LENGTH} characters long."
            )
        if not any(c.isupper() for c in raw_key) or not any(c.islower() for c in raw_key):
            logging.getLogger(__name__).warning(
                "Key should contain both uppercase and lowercase letters for better security."
            )
        if not any(c.isdigit() for c in raw_key):
            logging.getLogger(__name__).warning(
                "Key should contain at least one digit for better security."
        )
        # برای XChaCha20 از SHA256 برای تبدیل کلید به ۳۲ بایت
        return hashlib.sha256(raw_key.encode()).digest()

# ==================== FILE HANDLER ====================
class FileHandler:
    """Handles file operations with validation"""
    @staticmethod
    def validate(path: Path) -> None:
        if not path.exists():
            raise FileValidationError(f"File '{path}' not found.")
        if path.stat().st_size == 0:
            raise FileValidationError(f"File '{path}' is empty.")
        if not path.is_file():
            raise FileValidationError(f"'{path}' is not a regular file.")

    @staticmethod
    def read_bytes(path: Path) -> bytes:
        FileHandler.validate(path)
        with open(path, "rb") as f:
            return f.read()

    @staticmethod
    def write_bytes(path: Path, data: bytes) -> None:
        with open(path, "wb") as f:
            f.write(data)

    @staticmethod
    def write_text(path: Path, content: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        # Set executable permissions on Unix
        if os.name != 'nt':
            os.chmod(path, 0o755)

# ==================== ENCRYPTOR (XChaCha20-Poly1305) ====================
class Encryptor:
    """Core encryption engine using XChaCha20-Poly1305"""
    def __init__(self, context: EncryptionContext):
        self.context = context
        self.logger = context.logger or logging.getLogger(__name__)

    def encrypt(self) -> Tuple[bytes, str, str]:
        """
        Encrypt the input file and return (encrypted_payload, key_hash_hex, algorithm_name)
        """
        try:
            # Read input
            self.logger.info(f"Reading input file: {self.context.input_path}")
            plain_data = FileHandler.read_bytes(self.context.input_path)
            self.logger.info(f"Original size: {len(plain_data)} bytes")

            # Compress
            self.logger.info("Compressing data with zlib (level 9)...")
            compressed = zlib.compress(plain_data, level=9)
            self.logger.info(f"Compressed size: {len(compressed)} bytes")

            # Derive key
            self.logger.info("Deriving encryption key (SHA256)...")
            key = KeyManager.validate(self.context.key)
            key_hash = hashlib.sha256(self.context.key.encode()).hexdigest()

            # Encrypt with XChaCha20-Poly1305
            self.logger.info(f"Encrypting with {ALGORITHM}...")
            nonce = get_random_bytes(24)  # XChaCha20 uses 24-byte nonce
            cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
            ciphertext, tag = cipher.encrypt_and_digest(compressed)
            payload = nonce + tag + ciphertext  # 24 + 16 + len(ciphertext)
            self.logger.info(f"Encrypted payload size: {len(payload)} bytes")

            return payload, key_hash, ALGORITHM

        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Encryption process failed: {e}")

# ==================== DECRYPTOR (XChaCha20-Poly1305) ====================
class Decryptor:
    """Decryption engine for XChaCha20-Poly1305"""
    def __init__(self, context: DecryptionContext):
        self.context = context
        self.logger = context.logger or logging.getLogger(__name__)

    def decrypt(self, encrypted_payload: bytes, key: str) -> bytes:
        """
        Decrypt payload and return decompressed original data
        """
        try:
            self.logger.info("Decrypting with XChaCha20-Poly1305...")
            
            # Derive key
            key_hash = hashlib.sha256(key.encode()).digest()
            
            # Split payload
            nonce = encrypted_payload[:24]      # 24 bytes
            tag = encrypted_payload[24:40]      # 16 bytes
            ciphertext = encrypted_payload[40:] # remaining
            
            # Decrypt
            cipher = ChaCha20_Poly1305.new(key=key_hash, nonce=nonce)
            decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            
            # Decompress
            self.logger.info("Decompressing data...")
            decompressed = zlib.decompress(decrypted)
            self.logger.info(f"Decompressed size: {len(decompressed)} bytes")
            
            return decompressed
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise DecryptionError(f"Decryption process failed: {e}")

# ==================== LOADER GENERATOR ====================
class LoaderGenerator:
    """Generates the self-decrypting loader script (multi-language support)"""
    @staticmethod
    def generate(payload: bytes, key_b64: str, debug: bool, input_ext: str) -> str:
        """Return the complete loader source code as string"""
        debug_flag = "True" if debug else "False"
        payload_hex = payload.hex()
        
        # Map extension to interpreter
        ext_map = {
            '.py': 'python3',
            '.js': 'node',
            '.php': 'php',
            '.c': 'gcc',
            '.cpp': 'g++',
            '.h': 'gcc',
            '.hpp': 'g++',
            '.sh': 'bash',
            '.rb': 'ruby',
            '.pl': 'perl',
            '.go': 'go run',
            '.rs': 'rustc',
            '.java': 'javac',
            '.lua': 'lua',
            '.ts': 'ts-node',
            '.html': 'open',  # On macOS/Linux
        }
        interpreter = ext_map.get(input_ext.lower(), 'python3')
        
        loader_template = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Zaru v2.0 Loader - XChaCha20-Poly1305 (Signal Protocol)
Auto-generated, do not edit manually
"""

import os
import sys
import hashlib
import zlib
import base64
import tempfile
import subprocess
import shutil
from Crypto.Cipher import ChaCha20_Poly1305

# ========== EMBEDDED DATA ==========
ENCRYPTED_PAYLOAD = bytes.fromhex("{payload_hex}")
KEY_B64 = "{key_b64}"          # Base64 encoded key (obfuscation)
DEBUG = {debug_flag}
EXT = "{input_ext}"
INTERPRETER = "{interpreter}"
# ===================================

def secure_cleanup():
    """Attempt to clear sensitive variables from memory"""
    try:
        import gc
        for var in ['nonce', 'tag', 'ciphertext', 'decrypted', 'decompressed', 'key_hash']:
            if var in locals():
                del var
        gc.collect()
    except Exception:
        pass

def get_interpreter_for_extension(ext):
    """Return the appropriate interpreter for the given file extension"""
    interpreters = {{
        '.py': 'python3',
        '.js': 'node',
        '.php': 'php',
        '.c': 'gcc',
        '.cpp': 'g++',
        '.sh': 'bash',
        '.rb': 'ruby',
        '.pl': 'perl',
        '.go': 'go run',
        '.rs': 'rustc',
        '.java': 'javac',
        '.lua': 'lua',
        '.ts': 'ts-node',
    }}
    return interpreters.get(ext.lower(), 'python3')

def decrypt_and_run():
    """Decrypt payload and execute in current context"""
    tmp_dir = None
    tmp_path = None
    
    try:
        # Decode key
        key_raw = base64.b64decode(KEY_B64)
        key_hash = hashlib.sha256(key_raw).digest()

        # Split payload
        nonce = ENCRYPTED_PAYLOAD[:24]      # XChaCha20 nonce = 24 bytes
        tag = ENCRYPTED_PAYLOAD[24:40]      # Poly1305 tag = 16 bytes
        ciphertext = ENCRYPTED_PAYLOAD[40:]

        # Decrypt
        cipher = ChaCha20_Poly1305.new(key=key_hash, nonce=nonce)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)

        # Decompress
        decompressed = zlib.decompress(decrypted)

        # Determine interpreter (override if needed)
        interpreter = INTERPRETER
        if not interpreter or interpreter == 'None':
            interpreter = get_interpreter_for_extension(EXT)

        # Write to temp file
        tmp_dir = tempfile.mkdtemp(prefix='zaru_')
        tmp_path = os.path.join(tmp_dir, f'payload{EXT}')
        
        with open(tmp_path, 'wb') as f:
            f.write(decompressed)

        # Make executable if needed
        if EXT in ['.sh', '.py', '.js', '.php', '.rb', '.pl']:
            os.chmod(tmp_path, 0o755)

        # Handle compiled languages
        compiled_path = None
        
        if EXT in ['.c', '.cpp']:
            # Compile C/C++
            output = os.path.join(tmp_dir, 'payload.out')
            compile_cmd = [interpreter, tmp_path, '-o', output]
            if EXT == '.cpp':
                compile_cmd = ['g++', tmp_path, '-o', output]
            else:
                compile_cmd = ['gcc', tmp_path, '-o', output]
            
            subprocess.check_call(compile_cmd)
            os.remove(tmp_path)
            tmp_path = output
            os.chmod(tmp_path, 0o755)
            interpreter = ''  # Execute directly
            
        elif EXT == '.java':
            # Compile Java
            subprocess.check_call(['javac', tmp_path])
            class_file = tmp_path.replace('.java', '.class')
            # Run Java
            class_dir = os.path.dirname(class_file)
            class_name = os.path.basename(class_file).replace('.class', '')
            subprocess.check_call(['java', '-cp', class_dir, class_name])
            # Cleanup
            os.unlink(tmp_path)
            os.unlink(class_file)
            tmp_path = None
            return
            
        elif EXT == '.html':
            # Open in browser
            if sys.platform == 'darwin':
                subprocess.check_call(['open', tmp_path])
            elif sys.platform.startswith('linux'):
                subprocess.check_call(['xdg-open', tmp_path])
            elif sys.platform == 'win32':
                os.startfile(tmp_path)
            else:
                print(f"Unknown platform, file saved at: {tmp_path}")
            return

        # Execute
        if interpreter and tmp_path:
            subprocess.check_call([interpreter, tmp_path])
        elif tmp_path:
            subprocess.check_call([tmp_path])
        
        # Cleanup
        secure_cleanup()

    except Exception as e:
        if DEBUG:
            import traceback
            traceback.print_exc()
        else:
            # Silent exit
            pass
    
    finally:
        # Cleanup temp files
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass
        if tmp_dir and os.path.exists(tmp_dir):
            try:
                shutil.rmtree(tmp_dir)
            except:
                pass

if __name__ == "__main__":
    # Hide console on Windows (optional)
    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.kernel32.FreeConsole()
        except Exception:
            pass

    decrypt_and_run()
'''
        return loader_template

# ==================== UPDATE MANAGER ====================
class UpdateManager:
    """Handles automatic update checking and installation"""
    
    @staticmethod
    def _ensure_cache_dir():
        """Create cache directory if it doesn't exist"""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _load_cache() -> Dict[str, Any]:
        """Load update cache from disk"""
        UpdateManager._ensure_cache_dir()
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    @staticmethod
    def _save_cache(cache: Dict[str, Any]):
        """Save update cache to disk"""
        UpdateManager._ensure_cache_dir()
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache, f, indent=2)
        except IOError:
            pass  # Silently ignore cache write errors
    
    @staticmethod
    def _parse_version(version_str: str) -> Tuple[int, ...]:
        """Parse version string into tuple of ints, e.g. '2.1.0' -> (2,1,0)"""
        # Remove leading 'v' if present
        if version_str.startswith('v'):
            version_str = version_str[1:]
        parts = version_str.split('.')
        # Convert to int, fill missing with 0
        return tuple(int(p) for p in parts[:3])  # Only major.minor.patch
    
    @staticmethod
    def _is_newer(version1: str, version2: str) -> bool:
        """Return True if version1 is newer than version2"""
        try:
            v1 = UpdateManager._parse_version(version1)
            v2 = UpdateManager._parse_version(version2)
            return v1 > v2
        except Exception:
            # Fallback to string comparison if parsing fails
            return version1 > version2
    
    @staticmethod
    def _get_latest_release_info() -> Optional[Tuple[str, str]]:
        """
        Fetch latest release info from GitHub API.
        Returns (tag_name, download_url) or None on failure.
        """
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                tag = data.get('tag_name', '')
                # Try to find zaru.py asset
                download_url = None
                for asset in data.get('assets', []):
                    if asset.get('name') == 'zaru.py':
                        download_url = asset.get('browser_download_url')
                        break
                # Fallback to raw URL if asset not found
                if not download_url:
                    download_url = RAW_URL
                return tag, download_url
        except Exception as e:
            # Network or parsing errors
            logging.getLogger(__name__).debug(f"Update check failed: {e}")
            return None
    
    @staticmethod
    def _download_file(url: str, dest: Path) -> bool:
        """Download a file from URL to destination path"""
        try:
            urllib.request.urlretrieve(url, dest)
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Download failed: {e}")
            return False
    
    @staticmethod
    def _install_update(download_path: Path) -> bool:
        """
        Replace current executable with downloaded file.
        Returns True on success.
        """
        try:
            # Get current script path
            current_path = Path(sys.argv[0]).resolve()
            # If running as a script, current_path is the file itself.
            # If running as a module, current_path might be the python interpreter.
            # For our case, we assume it's the script.
            
            # Make sure we have write permission to the directory
            if not os.access(current_path.parent, os.W_OK):
                raise UpdateError(f"Directory {current_path.parent} is not writable. Try with sudo.")
            
            # Backup old file (optional)
            backup_path = current_path.with_suffix(current_path.suffix + '.bak')
            shutil.copy2(current_path, backup_path)
            
            # Replace current file with new one
            shutil.move(str(download_path), str(current_path))
            os.chmod(current_path, 0o755)  # Make executable
            
            # Remove backup on success (optional)
            # os.remove(backup_path)
            
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Installation failed: {e}")
            return False
    
    @classmethod
    def check_and_update(cls, logger: Optional[logging.Logger] = None):
        """
        Main entry point: check for updates and handle user interaction.
        """
        if logger is None:
            logger = logging.getLogger(__name__)
        
        # Load cache
        cache = cls._load_cache()
        now = time.time()
        last_check = cache.get('last_check', 0)
        
        # If less than 7 days since last check, skip
        if now - last_check < UPDATE_CHECK_INTERVAL:
            return
        
        logger.info("Checking for updates...")
        
        # Fetch latest release info
        info = cls._get_latest_release_info()
        if not info:
            # Failed to check, update last_check to avoid frequent retries on failure
            cache['last_check'] = now
            cls._save_cache(cache)
            logger.warning("Unable to check for updates (network error).")
            return
        
        latest_tag, download_url = info
        if not latest_tag or not download_url:
            cache['last_check'] = now
            cls._save_cache(cache)
            logger.warning("No release information found.")
            return
        
        # Compare versions
        current_version = VERSION
        if not cls._is_newer(latest_tag, current_version):
            # No update available
            logger.info(f"Already up to date (v{current_version})")
            cache['last_check'] = now
            cls._save_cache(cache)
            return
        
        # Update available
        logger.info(f"New version available: {latest_tag} (current: {current_version})")
        
        # Ask user
        try:
            response = input(f"Would you like to update Zaru to {latest_tag}? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            response = 'n'
        
        if response != 'y':
            logger.info("Update skipped.")
            # Set last_check to now so we won't ask again for a week
            cache['last_check'] = now
            cls._save_cache(cache)
            return
        
        # Proceed with download
        logger.info("Downloading update...")
        temp_dir = tempfile.mkdtemp(prefix='zaru_update_')
        temp_file = Path(temp_dir) / 'zaru_new.py'
        
        success = cls._download_file(download_url, temp_file)
        if not success:
            logger.error("Download failed. Update aborted.")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return
        
        # Verify the downloaded file (basic check: contains "Zaru")
        try:
            content = temp_file.read_text(encoding='utf-8')
            if "Zaru" not in content or "VERSION" not in content:
                raise UpdateError("Downloaded file does not appear to be a valid Zaru script.")
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return
        
        # Install
        logger.info("Installing update...")
        if cls._install_update(temp_file):
            logger.info("✅ Update installed successfully!")
            # Update cache to prevent re-prompting immediately
            cache['last_check'] = now
            cls._save_cache(cache)
            # Clean up temp dir
            shutil.rmtree(temp_dir, ignore_errors=True)
            # Suggest restart
            print("Please restart Zaru to apply the update.")
            sys.exit(0)  # Exit to allow restart
        else:
            logger.error("Installation failed. Old version preserved.")
            shutil.rmtree(temp_dir, ignore_errors=True)

# ==================== MAIN CONTROLLER ====================
class ZaruController:
    """Main orchestration class"""
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.logger = LoggerSetup.get_logger("Zaru", logging.DEBUG if args.debug else logging.INFO)
        self.context = None

    def run(self) -> None:
        """Execute the entire workflow"""
        try:
            self._print_banner()
            self._validate_arguments()
            self._prepare_context()
            self._encrypt_and_generate()
            self._finalize()
        except ZaruError as e:
            self.logger.error(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if self.args.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)

    def _print_banner(self) -> None:
        banner = BannerGenerator.generate()
        print(banner)

    def _validate_arguments(self) -> None:
        if not self.args.key:
            raise KeyValidationError("Key is required (use -k).")
        if not self.args.input:
            raise FileValidationError("Input file is required (use -i).")
        if not self.args.output:
            raise FileValidationError("Output file is required (use -o).")

        # Check for overwriting critical files (warning only)
        if self.args.output in ["zaru.py", "maker.py", "real_code.py"]:
            self.logger.warning(f"Output file '{self.args.output}' may overwrite important file.")

    def _prepare_context(self) -> None:
        input_path = Path(self.args.input)
        output_path = Path(self.args.output)
        self.context = EncryptionContext(
            input_path=input_path,
            output_path=output_path,
            key=self.args.key,
            debug=self.args.debug,
            logger=self.logger
        )

    def _encrypt_and_generate(self) -> None:
        # Encrypt
        encryptor = Encryptor(self.context)
        payload, key_hash, algorithm = encryptor.encrypt()

        # Encode key in base64 for embedding
        key_b64 = base64.b64encode(self.context.key.encode()).decode()

        # Get input file extension for multi-language support
        input_ext = self.context.input_path.suffix

        # Generate loader
        loader_code = LoaderGenerator.generate(payload, key_b64, self.context.debug, input_ext)

        # Write output
        output_path = self.context.output_path
        FileHandler.write_text(output_path, loader_code)
        self.logger.info(f"Loader successfully written to '{output_path}'")

        # Store key hash for reference (user can verify)
        self.logger.info(f"Key SHA256 hash: {key_hash} (for verification)")
        self.logger.info(f"Algorithm: {algorithm}")

    def _finalize(self) -> None:
        print("\n" + "="*50)
        print(f"✅ Zaru v{VERSION} completed successfully.")
        print(f"📦 Output file: {self.context.output_path}")
        print(f"🔐 Algorithm: {ALGORITHM}")
        if self.args.debug:
            print("🔍 Debug mode: ON (errors will be shown in loader)")
        else:
            print("🔒 Stealth mode: ON (errors hidden in loader)")
        print("="*50)

# ==================== DECRYPTION UTILITY ====================
class DecryptionUtility:
    """Standalone decryption utility for Zaru v2.0 files"""
    
    @staticmethod
    def decrypt_file(input_path: Path, output_path: Optional[Path], key: str, debug: bool = False) -> None:
        """Decrypt a Zaru v2.0 loader file back to original code"""
        logger = LoggerSetup.get_logger("Decrypt", logging.DEBUG if debug else logging.INFO)
        
        try:
            # Read the loader file (we need to extract the payload and key from it)
            logger.info(f"Reading loader file: {input_path}")
            content = FileHandler.read_bytes(input_path)
            
            # We need to parse the loader to extract ENCRYPTED_PAYLOAD and KEY_B64
            # This is a bit hacky but works for auto-generated loaders
            import re
            
            # Read as text
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Extract ENCRYPTED_PAYLOAD
            payload_match = re.search(r'ENCRYPTED_PAYLOAD = bytes\.fromhex\("([a-fA-F0-9]+)"\)', text)
            if not payload_match:
                raise DecryptionError("Could not find encrypted payload in file.")
            
            encrypted_hex = payload_match.group(1)
            encrypted_bytes = bytes.fromhex(encrypted_hex)
            logger.info(f"Extracted payload: {len(encrypted_bytes)} bytes")
            
            # Decrypt
            decryptor = Decryptor(DecryptionContext(
                input_path=input_path,
                output_path=output_path,
                debug=debug,
                logger=logger
            ))
            
            decrypted_data = decryptor.decrypt(encrypted_bytes, key)
            
            # Write output
            if output_path is None:
                # Generate output filename
                output_path = input_path.parent / f"decrypted_{input_path.stem}.py"
            
            FileHandler.write_bytes(output_path, decrypted_data)
            logger.info(f"✅ Decrypted successfully: {output_path}")
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            if debug:
                import traceback
                traceback.print_exc()
            raise

# ==================== ARGUMENT PARSER ====================
def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zaru",
        description=f"Zaru v{VERSION} - Quantum Encryption Tool with {ALGORITHM}",
        add_help=False,
        epilog=f"Version {VERSION} | Algorithm: {ALGORITHM}"
    )
    
    # Main arguments
    parser.add_argument(
        "-k", "--key",
        required=False,
        help="Encryption/Decryption key (minimum 12 characters)"
    )
    parser.add_argument(
        "-i", "--input",
        required=False,
        help="Input file (original code for encryption, or loader for decryption)"
    )
    parser.add_argument(
        "-o", "--output",
        required=False,
        help="Output file (encrypted loader or decrypted code)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (shows errors)"
    )
    parser.add_argument(
        "--decrypt",
        action="store_true",
        help="Decrypt a loader file back to original code"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Zaru v{VERSION}",
        help="Show version and exit"
    )
    parser.add_argument(
        "-h", "--help",
        action="help",
        help="Show this help message and exit"
    )
    return parser

# ==================== MAIN ENTRY POINT ====================
def main() -> None:
    parser = create_parser()
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # ===== DECRYPTION MODE =====
    if args.decrypt:
        if not args.key:
            print("Error: -k (key) is required for decryption.", file=sys.stderr)
            sys.exit(1)
        if not args.input:
            print("Error: -i (input loader file) is required for decryption.", file=sys.stderr)
            sys.exit(1)
        
        input_path = Path(args.input)
        output_path = Path(args.output) if args.output else None
        
        try:
            DecryptionUtility.decrypt_file(input_path, output_path, args.key, args.debug)
        except Exception as e:
            print(f"Decryption failed: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # ===== ENCRYPTION MODE =====
    if not args.key or not args.input or not args.output:
        print("Error: -k, -i, -o are required for encryption.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # --- Check for updates (only in encryption mode) ---
    # This will run before encryption, but after argument validation.
    # It will not run if --decrypt is used.
    UpdateManager.check_and_update()

    controller = ZaruController(args)
    controller.run()

if __name__ == "__main__":
    main()
