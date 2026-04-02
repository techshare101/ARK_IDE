from typing import Dict, Any, Tuple
import re

class CommandGuardrail:
    """Guard against dangerous commands"""
    
    BLOCKED_COMMANDS = [
        r"rm\s+-rf\s+/",
        r"rm\s+-rf\s+\*",
        r"shutdown",
        r"reboot",
        r"mkfs",
        r"dd\s+if=.*of=/dev/",
        r":(){:|:&};:",  # fork bomb
        r"chmod\s+-R\s+777\s+/",
        r"chown\s+-R.*:.*\/",
    ]
    
    HIGH_RISK_COMMANDS = [
        r"rm\s+-rf",
        r"sudo\s+rm",
        r"docker\s+rm",
        r"git\s+reset\s+--hard",
        r"git\s+clean\s+-fd",
        r"npm\s+install\s+-g",
        r"pip\s+install\s+--upgrade",
    ]
    
    @classmethod
    def check_command(cls, command: str) -> Tuple[bool, str, str]:
        """
        Check if command is safe
        Returns: (is_safe, risk_level, reason)
        """
        # Check blocked commands
        for pattern in cls.BLOCKED_COMMANDS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, "blocked", f"Blocked dangerous command pattern: {pattern}"
        
        # Check high-risk commands (require approval)
        for pattern in cls.HIGH_RISK_COMMANDS:
            if re.search(pattern, command, re.IGNORECASE):
                return True, "high_risk", f"High-risk command detected: {pattern}"
        
        return True, "safe", "Command is safe"
    
    @classmethod
    def sanitize_command(cls, command: str) -> str:
        """Remove potentially dangerous elements from command"""
        # Remove pipes to /dev/null that might hide errors
        command = re.sub(r'\s*>\s*/dev/null\s*2>&1', '', command)
        # Remove background execution for safety
        command = re.sub(r'\s*&\s*$', '', command)
        return command.strip()

command_guardrail = CommandGuardrail()
