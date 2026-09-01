import sys
from typing import Any, Dict
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.patch_stdout import patch_stdout
from terminal_zero.core.state import CommandContext, CommandResult
from terminal_zero.engine.pipeline import PipelineEngine
from terminal_zero.engine.keybindings import VFSCompleter, build_key_bindings


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
        print("=== APOLLO WORKSTATION TERMINAL [RECOVERY MODE] ===")
        print("System degraded. Type 'help' for guidance or inspect 'README.txt'.")
        print("Type 'exit' to disconnect.\n")
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
