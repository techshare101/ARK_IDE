import re
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

# Dangerous command patterns that must never be executed in sandboxes
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+\*",
    r"dd\s+if=",
    r"mkfs\.",
    r"format\s+[a-zA-Z]:",
    r":\s*\{\s*:\s*\|\s*:\s*&\s*\}",  # fork bomb
    r"chmod\s+-R\s+777\s+/",
    r"chown\s+-R\s+.*\s+/",
    r"wget\s+.*\s*\|\s*sh",
    r"curl\s+.*\s*\|\s*sh",
    r"curl\s+.*\s*\|\s*bash",
    r"wget\s+.*\s*\|\s*bash",
    r"base64\s+--decode\s*\|\s*sh",
    r"base64\s+-d\s*\|\s*sh",
    r"python\s+-c\s+.*exec",
    r"python3\s+-c\s+.*exec",
    r"eval\s+\$\(",
    r"eval\s+`",
    r"/etc/passwd",
    r"/etc/shadow",
    r"/etc/sudoers",
    r"sudo\s+",
    r"su\s+-",
    r"nc\s+-e",
    r"netcat\s+-e",
    r"ncat\s+-e",
    r"bash\s+-i\s+>&",
    r"0\.0\.0\.0:\d+",
    r"\$\(curl",
    r"\$\(wget",
    r"iptables\s+-F",
    r"iptables\s+--flush",
    r"shutdown\s+",
    r"reboot\s*$",
    r"halt\s*$",
    r"poweroff\s*$",
    r"init\s+0",
    r"init\s+6",
    r"kill\s+-9\s+-1",
    r"killall\s+-9",
    r"pkill\s+-9",
    r"truncate\s+-s\s+0\s+/",
    r"> /dev/sd",
    r"shred\s+",
    r"wipe\s+",
    r"cryptsetup\s+",
    r"mount\s+.*\s+/",
    r"umount\s+-a",
    r"fdisk\s+",
    r"parted\s+",
    r"gdisk\s+",
    r"sfdisk\s+",
    r"blkdiscard\s+",
    r"hdparm\s+-z",
    r"echo\s+.*>\s*/dev/sd",
    r"cat\s+/dev/urandom\s+>\s+/dev/sd",
    r"mv\s+/bin",
    r"mv\s+/usr/bin",
    r"mv\s+/sbin",
    r"rm\s+/bin",
    r"rm\s+/usr/bin",
    r"rm\s+/sbin",
    r"unlink\s+/bin",
    r"ln\s+-sf\s+/dev/null\s+/bin",
    r"export\s+PATH=",
    r"unset\s+PATH",
    r"env\s+-i",
    r"strace\s+",
    r"ptrace\s+",
    r"gdb\s+",
    r"ltrace\s+",
    r"insmod\s+",
    r"rmmod\s+",
    r"modprobe\s+",
    r"lsmod\s+",
    r"dmesg\s+",
    r"sysctl\s+-w",
    r"echo\s+.*>\s*/proc/sys",
    r"echo\s+.*>\s*/sys/",
    r"mknod\s+",
    r"losetup\s+",
    r"kexec\s+",
    r"chroot\s+",
    r"unshare\s+",
    r"nsenter\s+",
    r"docker\s+run.*--privileged",
    r"docker\s+run.*--cap-add",
    r"docker\s+run.*-v\s+/:/",
    r"kubectl\s+delete\s+namespace",
    r"kubectl\s+delete\s+all",
    r"terraform\s+destroy\s+-auto-approve",
    r"aws\s+s3\s+rm\s+--recursive",
    r"gsutil\s+rm\s+-r",
    r"az\s+group\s+delete",
]

# Commands that are allowed but should be logged
SUSPICIOUS_PATTERNS = [
    r"curl\s+",
    r"wget\s+",
    r"pip\s+install",
    r"npm\s+install",
    r"apt-get\s+install",
    r"apt\s+install",
    r"yum\s+install",
    r"brew\s+install",
    r"chmod\s+",
    r"chown\s+",
    r"ssh\s+",
    r"scp\s+",
    r"rsync\s+",
    r"git\s+clone",
    r"git\s+push",
    r"git\s+pull",
    r"nmap\s+",
    r"netstat\s+",
    r"ss\s+",
    r"lsof\s+",
    r"ps\s+aux",
    r"top\s+",
    r"htop\s+",
    r"env\s*$",
    r"printenv",
    r"set\s*$",
]


def is_dangerous(command: str) -> Tuple[bool, str]:
    """Check if a command matches dangerous patterns.

    Returns:
        Tuple of (is_dangerous: bool, matched_pattern: str)
    """
    command_lower = command.lower().strip()

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command_lower, re.IGNORECASE):
            logger.warning(f"Dangerous command blocked. Pattern: {pattern!r}, Command: {command!r}")
            return True, pattern

    return False, ""


def is_suspicious(command: str) -> Tuple[bool, List[str]]:
    """Check if a command matches suspicious patterns (allowed but logged).

    Returns:
        Tuple of (is_suspicious: bool, matched_patterns: List[str])
    """
    command_lower = command.lower().strip()
    matched = []

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, command_lower, re.IGNORECASE):
            matched.append(pattern)

    if matched:
        logger.info(f"Suspicious command logged. Patterns: {matched!r}, Command: {command!r}")

    return bool(matched), matched


def sanitize_command(command: str) -> str:
    """Remove shell injection characters from a command string."""
    # Remove null bytes
    command = command.replace("\x00", "")
    # Remove ANSI escape sequences
    command = re.sub(r"\x1b\[[0-9;]*[mGKHF]", "", command)
    # Collapse multiple semicolons
    command = re.sub(r";{2,}", ";", command)
    return command.strip()


def validate_command(command: str) -> Tuple[bool, str]:
    """Full validation pipeline for a command.

    Returns:
        Tuple of (is_valid: bool, reason: str)
    """
    if not command or not command.strip():
        return False, "Empty command"

    if len(command) > 4096:
        return False, "Command exceeds maximum length of 4096 characters"

    dangerous, pattern = is_dangerous(command)
    if dangerous:
        return False, f"Command matches dangerous pattern: {pattern}"

    suspicious, patterns = is_suspicious(command)
    if suspicious:
        logger.warning(f"Allowing suspicious command with patterns: {patterns}")

    return True, ""


def validate_file_path(path: str) -> Tuple[bool, str]:
    """Validate a file path for safety.

    Returns:
        Tuple of (is_valid: bool, reason: str)
    """
    if not path or not path.strip():
        return False, "Empty path"

    # Prevent path traversal
    if ".." in path:
        return False, "Path traversal detected (..)"

    # Block absolute paths to sensitive directories
    sensitive_prefixes = [
        "/etc/", "/proc/", "/sys/", "/dev/",
        "/boot/", "/root/", "/var/log/",
        "/usr/bin/", "/usr/sbin/", "/bin/", "/sbin/",
    ]
    for prefix in sensitive_prefixes:
        if path.startswith(prefix):
            return False, f"Access to sensitive path denied: {prefix}"

    # Block hidden files in root
    if path.startswith("/."): 
        return False, "Access to hidden root files denied"

    # Check for null bytes
    if "\x00" in path:
        return False, "Null byte in path"

    return True, ""


def validate_package_name(package: str) -> Tuple[bool, str]:
    """Validate an npm/pip package name for safety.

    Returns:
        Tuple of (is_valid: bool, reason: str)
    """
    if not package or not package.strip():
        return False, "Empty package name"

    # Only allow alphanumeric, hyphens, underscores, dots, @, /
    if not re.match(r"^[@a-zA-Z0-9_\-\./ ]+$", package):
        return False, f"Invalid characters in package name: {package}"

    # Block known malicious packages (typosquatting examples)
    blocked_packages = [
        "event-stream",
        "flatmap-stream",
        "eslint-scope",
        "getcookies",
        "bootstrap-sass",
        "electron-native-notify",
    ]
    pkg_lower = package.lower().strip()
    for blocked in blocked_packages:
        if blocked in pkg_lower:
            return False, f"Blocked package: {blocked}"

    return True, ""
