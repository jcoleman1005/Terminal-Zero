import sys
from typing import Any, Dict
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.patch_stdout import patch_stdout
from terminal_zero.core.state import CommandContext, CommandResult
from terminal_zero.engine.pipeline import PipelineEngine
from terminal_zero.engine.keybindings import VFSCompleter, build_key_bindings


def get_boot_screen(flags: Dict[str, bool]) -> str:
    m0 = "\033[1;32m[   OK   ]\033[0m" if flags.get("BUFFER_REPAIRED") else "\033[1;33m[DEGRADED]\033[0m"
    m1 = "\033[1;32m[   OK   ]\033[0m" if flags.get("BASHRC_RESTORED") else "\033[1;31m[ FAILED ]\033[0m"
    m2 = "\033[1;32m[   OK   ]\033[0m" if flags.get("LOGS_AUDITED") else "\033[1;33m[ ALERT  ]\033[0m"
    m5 = "\033[1;32m[   OK   ]\033[0m" if flags.get("MALWARE_TERMINATED") else "\033[1;31m[CRITICAL]\033[0m"
    m6 = "\033[1;32m[   OK   ]\033[0m" if flags.get("NETWORK_ONLINE") else "\033[1;31m[  DOWN  ]\033[0m"
    m7 = "\033[1;32m[   OK   ]\033[0m" if flags.get("PHOENIX_ONLINE") else "\033[1;33m[INACTIVE]\033[0m"

    m0_msg = "Up/Down arrow memory active" if flags.get("BUFFER_REPAIRED") else "Up/Down history recall offline"
    m1_msg = "User ~/.bashrc profile active" if flags.get("BASHRC_RESTORED") else "Shell profile missing (~/.bashrc)"
    m2_msg = "Incident breach triaged" if flags.get("LOGS_AUDITED") else "Intrusion traces detected in /var/log/"
    m5_msg = "Process supervisor nominal" if flags.get("MALWARE_TERMINATED") else "Rogue miner active @ 98% CPU (/tmp/sys_miner)"
    m6_msg = "Link state ONLINE (10.0.42.15)" if flags.get("NETWORK_ONLINE") else "Network interface apollo0 offline"
    m7_msg = "Restoration daemon listening on :8080" if flags.get("PHOENIX_ONLINE") else "Cluster restoration gateway offline"

    lines = [
        "================================================================================",
        "           APOLLO WORKSTATION OS v2.4 (x86_64-apollo-linux-gnu)",
        "================================================================================",
        "[ 0.001 ] Kernel initialized (Linux 5.15.0-apollo)",
        f"[ 0.042 ] Checking hardware ring buffers........ {m0} -> {m0_msg}",
        f"[ 0.088 ] Loading shell user environment........ {m1} -> {m1_msg}",
        f"[ 0.120 ] Security subsystem audit.............. {m2} -> {m2_msg}",
        f"[ 0.195 ] Process supervisor integrity.......... {m5} -> {m5_msg}",
        f"[ 0.240 ] Network link status (apollo0)......... {m6} -> {m6_msg}",
        f"[ 0.310 ] Cluster restoration gateway........... {m7} -> {m7_msg}",
        "================================================================================",
        "*** SYSTEM IN EMERGENCY RECOVERY MODE ***",
        "Operator: alice (tty1) | Host: apollo | Location: /home/alice",
        "",
        "ONBOARDING ACTIONS:",
        "  • Type 'ls' to look around your current directory.",
        "  • Type 'cat <filename>' (e.g. 'cat README.txt') to read file contents.",
        "  • Type 'exit' to disconnect from session.",
        "================================================================================\n",
    ]
    return "\n".join(lines)


class TerminalShell:
    def __init__(self, ctx: CommandContext, command_table: Dict[str, Any], **session_kwargs):
        self.ctx = ctx
        self.commands = command_table
        self.pipeline_engine = PipelineEngine(self.commands, self.ctx.bus)
        self.history = InMemoryHistory()
        self.completer = VFSCompleter(lambda: self.ctx)
        self.key_bindings = build_key_bindings(lambda: self.ctx)
        try:
            self.session = PromptSession(
                history=self.history,
                completer=self.completer,
                key_bindings=self.key_bindings,
                complete_while_typing=False,
                **session_kwargs
            )
        except Exception:
            from prompt_toolkit.input import DummyInput
            from prompt_toolkit.output import DummyOutput
            self.session = PromptSession(
                history=self.history,
                completer=self.completer,
                key_bindings=self.key_bindings,
                complete_while_typing=False,
                input=session_kwargs.get("input", DummyInput()),
                output=session_kwargs.get("output", DummyOutput())
            )

    def get_prompt(self) -> ANSI:
        user = self.ctx.state.env.get("USER", "alice")
        host = self.ctx.state.env.get("HOST", "apollo")
        cwd = self.ctx.state.cwd_str
        return ANSI(f"\033[1;32m{user}@{host}\033[0m:\033[1;34m{cwd}\033[0m$ ")

    def execute_command_line(self, raw_input: str) -> CommandResult:
        result = self.pipeline_engine.run(raw_input, self.ctx.state)
        if result.exit_code != 0 and result.stderr:
            self.ctx.state.last_stderr = result.stderr.strip()
        elif result.exit_code == 0:
            self.ctx.state.last_stderr = ""
        return result

    def execute_line(self, line: str):
        line = line.strip()
        if not line:
            return
        result = self.execute_command_line(line)
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)

    def run(self):
        print(get_boot_screen(self.ctx.state.system_flags))
        while True:
            try:
                with patch_stdout():
                    text = self.session.prompt(self.get_prompt())
                if text.strip() == "exit":
                    break
                self.execute_line(text)
            except EOFError:
                break
            except KeyboardInterrupt:
                continue
