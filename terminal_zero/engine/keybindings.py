import sys
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from terminal_zero.core.state import CommandContext


class VFSCompleter(Completer):
    def __init__(self, get_context):
        self.get_context = get_context

    def get_completions(self, document, complete_event):
        ctx: CommandContext = self.get_context()
        if not (ctx.state.unlocked_ergonomics.get("tab_completion", False) or ctx.state.unlocked_ergonomics.get("autocomplete", False)):
            return

        text = document.text_before_cursor
        tokens = text.split()
        word = document.get_word_before_cursor()

        # Command completion (first token)
        if len(tokens) == 0 or (len(tokens) == 1 and not text.endswith(" ")):
            path_var = ctx.state.env.get("PATH", "/bin:/usr/bin")
            for bin_dir in path_var.split(":"):
                node, _ = ctx.vfs.get_node([], bin_dir)
                if node and node.is_dir():
                    for name in node.children.keys():
                        if name.lower().startswith(word.lower()):
                            yield Completion(name, start_position=-len(word))

            # Also complete local CWD entries for first token
            dir_node, _ = ctx.vfs.get_node(ctx.state.current_path, ".")
            if dir_node and dir_node.is_dir():
                for child_name, child_node in dir_node.children.items():
                    if child_name.lower().startswith(word.lower()):
                        display_name = child_name + ("/" if child_node.is_dir() else "")
                        yield Completion(display_name, start_position=-len(word))
            return

        # Path / Argument completion
        target_path = word if word else "."
        if "/" in target_path:
            parent_path, prefix = target_path.rsplit("/", 1)
            search_dir = "/" if parent_path == "" else parent_path
        else:
            search_dir = "."
            prefix = target_path

        dir_node, _ = ctx.vfs.get_node(ctx.state.current_path, search_dir)
        if dir_node and dir_node.is_dir():
            for child_name, child_node in dir_node.children.items():
                if child_name.lower().startswith(prefix.lower()):
                    display_name = child_name + ("/" if child_node.is_dir() else "")
                    yield Completion(display_name, start_position=-len(prefix))


def build_key_bindings(get_context):
    kb = KeyBindings()

    @kb.add("c-c")
    def handle_sigint(event):
        sys.stdout.write("^C\n")
        event.app.output.flush()
        event.app.current_buffer.reset()

    @kb.add("up")
    def handle_up_arrow(event):
        ctx = get_context()
        if not (ctx.state.unlocked_ergonomics.get("history_arrows", False) or ctx.state.unlocked_ergonomics.get("history", False)):
            sys.stdout.write("\n[HARDWARE ERROR]: Input ring buffer corrupted. Navigation history disabled.\n")
            event.app.output.flush()
        else:
            event.app.current_buffer.auto_up()

    @kb.add("down")
    def handle_down_arrow(event):
        ctx = get_context()
        if not (ctx.state.unlocked_ergonomics.get("history_arrows", False) or ctx.state.unlocked_ergonomics.get("history", False)):
            sys.stdout.write("\n[HARDWARE ERROR]: Input ring buffer corrupted. Navigation history disabled.\n")
            event.app.output.flush()
        else:
            event.app.current_buffer.auto_down()

    @kb.add("tab")
    def handle_tab(event):
        ctx = get_context()
        if not (ctx.state.unlocked_ergonomics.get("tab_completion", False) or ctx.state.unlocked_ergonomics.get("autocomplete", False)):
            sys.stdout.write("\n[DRIVER MISSING]: libreadline unit offline. Tab autocompletion unavailable.\n")
            event.app.output.flush()
        else:
            event.app.current_buffer.start_completion()

    return kb


create_key_bindings = build_key_bindings
