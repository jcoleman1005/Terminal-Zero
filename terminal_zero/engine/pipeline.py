from dataclasses import dataclass, field
import shlex
from typing import Any, Dict, List, Optional, Tuple
from terminal_zero.core.events import Event, EventBus
from terminal_zero.core.vfs import VirtualFilesystem
from terminal_zero.core.state import CommandContext, CommandResult, TerminalState


def split_unquoted(text: str, delimiter: str) -> List[str]:
    """Splits a string by delimiter only when not enclosed in quotes."""
    parts = []
    current = []
    in_single = False
    in_double = False
    escape = False

    i = 0
    d_len = len(delimiter)
    while i < len(text):
        c = text[i]
        if escape:
            current.append(c)
            escape = False
            i += 1
            continue

        if c == "\\":
            escape = True
            current.append(c)
            i += 1
            continue

        if c == "'" and not in_double:
            in_single = not in_single
            current.append(c)
            i += 1
            continue

        if c == '"' and not in_single:
            in_double = not in_double
            current.append(c)
            i += 1
            continue

        if not in_single and not in_double and text[i:i + d_len] == delimiter:
            parts.append("".join(current).strip())
            current = []
            i += d_len
            continue

        current.append(c)
        i += 1

    if current or not parts:
        parts.append("".join(current).strip())

    return parts


@dataclass
class ParsedCommand:
    args: List[str] = field(default_factory=list)
    redirect_out: Optional[str] = None
    redirect_append: bool = False
    redirect_in: Optional[str] = None


class PipelineEngine:
    def __init__(self, commands: Dict[str, Any], bus: EventBus, state: Optional[TerminalState] = None, vfs: Optional[VirtualFilesystem] = None):
        self.commands = commands
        self.bus = bus
        self.state = state
        self.vfs = vfs or (state.vfs if state else None)

    def execute(self, raw_input: str) -> CommandResult:
        if self.state is None:
            raise ValueError("TerminalState must be provided to PipelineEngine to call execute()")
        return self.run(raw_input, self.state)

    def parse_stage(self, stage_text: str) -> Tuple[Optional[ParsedCommand], Optional[str]]:
        stage_text = stage_text.strip()
        if not stage_text:
            return None, "empty command"

        redirect_out = None
        append_mode = False

        # Look for unquoted >> or >
        redirect_parts = split_unquoted(stage_text, ">>")
        if len(redirect_parts) > 1:
            stage_cmd = redirect_parts[0]
            redirect_target = ">>".join(redirect_parts[1:]).strip()
            append_mode = True
        else:
            redirect_parts = split_unquoted(stage_text, ">")
            if len(redirect_parts) > 1:
                stage_cmd = redirect_parts[0]
                redirect_target = ">".join(redirect_parts[1:]).strip()
                append_mode = False
            else:
                stage_cmd = stage_text
                redirect_target = None

        if redirect_target:
            try:
                target_tokens = shlex.split(redirect_target)
                if not target_tokens:
                    return None, "syntax error near unexpected token 'newline'"
                redirect_out = target_tokens[0]
            except ValueError as e:
                return None, str(e)

        try:
            tokens = shlex.split(stage_cmd)
        except ValueError as e:
            return None, str(e)

        if not tokens:
            return None, "missing command"

        return ParsedCommand(args=tokens, redirect_out=redirect_out, redirect_append=append_mode), None

    def execute_binary_or_command(self, cmd_name: str, args: List[str], ctx: CommandContext) -> CommandResult:
        # Direct lookup in registered command table if not explicitly invoked by path
        if "/" not in cmd_name and cmd_name in self.commands:
            return self.commands[cmd_name](ctx, args)

        # Path-based command execution (e.g. ./recovery.sh or /mnt/recovery/bin/recovery.sh)
        if "/" in cmd_name:
            vfs_node, resolved_parts = ctx.vfs.get_node(ctx.state.current_path, cmd_name)
            if not vfs_node:
                return ctx.result_factory(stderr=f"bash: {cmd_name}: No such file or directory\n", exit_code=127)

            if vfs_node.is_dir():
                return ctx.result_factory(stderr=f"bash: {cmd_name}: Is a directory\n", exit_code=126)

            # Guard against executing text / log / config data files directly
            if any(cmd_name.endswith(ext) for ext in [".txt", ".log", ".conf", ".key", ".md", ".bash_history", ".bashrc"]):
                return ctx.result_factory(
                    stderr=f"bash: {cmd_name}: cannot execute binary file: Exec format error\n",
                    exit_code=126
                )

            # Verify executable permission bitmask: mode & 0o111
            mode = int(vfs_node.permissions, 8) if (vfs_node.permissions and vfs_node.permissions.isdigit()) else 0
            if not (mode & 0o111):
                return ctx.result_factory(stderr=f"bash: {cmd_name}: Permission denied\n", exit_code=126)

            base_name = cmd_name.split("/")[-1]
            if base_name == "recovery.sh":
                ctx.state.unlocked_ergonomics["ctrl_c"] = True
                ctx.state.unlocked_ergonomics["sigint"] = True
                ctx.state.unlocked_ergonomics["sigint_trap"] = True
                ctx.state.system_flags["SIGINT_UNLOCKED"] = True
                ctx.bus.publish(Event("flag_changed", {"flag": "SIGINT_UNLOCKED", "value": True}))
                msg = (
                    "[RECOVERY]: Kernel signal traps restored. Signal 2 (SIGINT / Ctrl+C) mapped to active console line discipline.\n"
                    "Foreground processes can now be safely interrupted.\n"
                )
                return ctx.result_factory(stdout=msg, exit_code=0)
            elif base_name in self.commands:
                return self.commands[base_name](ctx, args)
            elif base_name.endswith(".sh"):
                return ctx.result_factory(stdout=f"[EXEC]: Executed shell script '{cmd_name}'\n")
            else:
                return ctx.result_factory(
                    stderr=f"bash: {cmd_name}: cannot execute binary file: Exec format error\n",
                    exit_code=126
                )

        # Non-path command not directly in commands: Check $PATH directories
        path_env = ctx.state.env.get("PATH", "/bin:/usr/bin")
        for p_dir in path_env.split(":"):
            cand_node, cand_parts = ctx.vfs.get_node([], f"{p_dir}/{cmd_name}")
            if cand_node and cand_node.is_file():
                mode = int(cand_node.permissions, 8) if (cand_node.permissions and cand_node.permissions.isdigit()) else 0
                if not (mode & 0o111):
                    return ctx.result_factory(stderr=f"bash: {cmd_name}: Permission denied\n", exit_code=126)
                if cmd_name in self.commands:
                    return self.commands[cmd_name](ctx, args)

        return ctx.result_factory(stderr=f"bash: {cmd_name}: command not found\n", exit_code=127)

    def run(self, raw_input: str, state: TerminalState) -> CommandResult:
        line = raw_input.strip()
        if not line:
            return CommandResult()
        if line.startswith("#"):
            return CommandResult(stdout="", stderr="", exit_code=0)

        if line == "note" or line.startswith("note ") or line == "feedback" or line.startswith("feedback "):
            cmd_name = "note" if (line == "note" or line.startswith("note ")) else "feedback"
            raw_msg = line[len(cmd_name):].strip()
            args = [raw_msg] if raw_msg else []
            stage_ctx = CommandContext(
                vfs=state.vfs,
                state=state,
                bus=self.bus,
                stdin=""
            )
            if cmd_name in self.commands:
                return self.commands[cmd_name](stage_ctx, args)

        stages_text = split_unquoted(line, "|")
        current_stdin = ""
        last_result = CommandResult()
        first_cmd = stages_text[0].strip().split()[0] if stages_text else ""
        is_decrypt = first_cmd in ["decrypt", "osiris-diagnostics", "note", "feedback"]

        for idx, stage_text in enumerate(stages_text):
            parsed, err = self.parse_stage(stage_text)
            if err or not parsed:
                res = CommandResult(stderr=f"bash: syntax error: {err}\n", exit_code=2)
                state.last_stderr = res.stderr.strip()
                return res

            cmd_name = parsed.args[0]
            cmd_args = parsed.args[1:]

            stage_ctx = CommandContext(
                vfs=state.vfs,
                state=state,
                bus=self.bus,
                stdin=current_stdin
            )

            stage_result = self.execute_binary_or_command(cmd_name, cmd_args, stage_ctx)
            last_result = stage_result

            # If any stage fails, abort pipeline
            if stage_result.exit_code != 0:
                if stage_result.stderr:
                    state.last_stderr = stage_result.stderr.strip()
                return stage_result

            current_stdin = stage_result.stdout

            # Handle file redirection on stage
            if parsed.redirect_out:
                redirect_target = parsed.redirect_out
                parent_dir = redirect_target.rsplit("/", 1)[0] if "/" in redirect_target else "."
                if not parent_dir:
                    parent_dir = "/"
                
                parent_node, _ = state.vfs.get_node(state.current_path, parent_dir)
                if not parent_node or not parent_node.is_dir():
                    res = CommandResult(stderr=f"bash: {redirect_target}: No such file or directory\n", exit_code=1)
                    state.last_stderr = res.stderr.strip()
                    return res
                
                if parent_node.permissions == "000":
                    res = CommandResult(stderr=f"bash: {redirect_target}: Permission denied\n", exit_code=1)
                    state.last_stderr = res.stderr.strip()
                    return res

                success, w_err = state.vfs.write_file(
                    state.current_path,
                    redirect_target,
                    stage_result.stdout,
                    append=parsed.redirect_append,
                    owner=state.env.get("USER", "alice")
                )
                if not success:
                    res = CommandResult(stderr=f"bash: {redirect_target}: {w_err}\n", exit_code=1)
                    state.last_stderr = res.stderr.strip()
                    return res

                # Output was consumed by file redirection
                current_stdin = ""
                last_result = CommandResult(stdout="", stderr="", exit_code=0)

        if last_result.exit_code != 0 and last_result.stderr:
            state.last_stderr = last_result.stderr.strip()
        elif last_result.exit_code == 0 and not is_decrypt:
            state.last_stderr = ""

        return last_result
