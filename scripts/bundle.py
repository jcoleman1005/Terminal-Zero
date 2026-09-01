#!/usr/bin/env python3
"""Bundle the modular Terminal Zero package into a single standalone file (Prototype.txt)."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HEADER = """from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import datetime
import fnmatch
import json
import os
from pathlib import Path
import re
import shlex
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style

"""

MODULE_ORDER = [
    ROOT / "terminal_zero" / "core" / "events.py",
    ROOT / "terminal_zero" / "core" / "vfs.py",
    ROOT / "terminal_zero" / "content" / "narrative.py",
    ROOT / "terminal_zero" / "content" / "initial_vfs.py",
    ROOT / "terminal_zero" / "core" / "state.py",
    ROOT / "terminal_zero" / "content" / "man_pages.py",
    ROOT / "terminal_zero" / "commands" / "posix.py",
    ROOT / "terminal_zero" / "content" / "debriefs.py",
    ROOT / "terminal_zero" / "core" / "persistence.py",
    ROOT / "terminal_zero" / "commands" / "diegetic.py",
    ROOT / "terminal_zero" / "commands" / "__init__.py",
    ROOT / "terminal_zero" / "engine" / "pipeline.py",
    ROOT / "terminal_zero" / "engine" / "keybindings.py",
    ROOT / "terminal_zero" / "engine" / "repl.py",
    ROOT / "terminal_zero" / "__main__.py",
]


def clean_module_code(code: str) -> str:
    cleaned_lines = []
    for line in code.splitlines():
        # Strip local package imports
        stripped = line.strip()
        if stripped.startswith("from terminal_zero") or stripped.startswith("import terminal_zero"):
            continue
        # Strip standard library imports that are already in the global header
        if stripped in [
            "import os", "import sys", "import datetime", "import json", "import re",
            "import shlex", "import fnmatch",
            "from dataclasses import dataclass, field",
            "from typing import Any, Callable, Dict, List, Optional, Set, Tuple",
            "from typing import Dict, List, Optional, Tuple, Any, Callable",
            "from typing import Dict, Optional", "from typing import Dict",
            "from typing import Any, Dict, List, Optional",
            "from typing import Any, Callable, Dict, List",
            "from typing import Any, Dict", "from typing import List",
            "from prompt_toolkit import PromptSession",
            "from prompt_toolkit.formatted_text import ANSI",
            "from prompt_toolkit.history import InMemoryHistory",
            "from prompt_toolkit.patch_stdout import patch_stdout",
            "from prompt_toolkit.completion import Completer, Completion",
            "from prompt_toolkit.key_binding import KeyBindings",
        ]:
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def bundle(target_file: Path = ROOT / "Prototype.txt"):
    chunks = [HEADER.strip()]
    for module_path in MODULE_ORDER:
        if module_path.exists():
            code = module_path.read_text(encoding="utf-8")
            cleaned = clean_module_code(code)
            chunks.append(f"\n# --- {module_path.name} ---\n" + cleaned)
    
    output = "\n\n".join(chunks) + "\n"
    target_file.write_text(output, encoding="utf-8")
    print(f"[OK] Bundled {len(MODULE_ORDER)} modules into {target_file.name} ({len(output.splitlines())} lines)")


if __name__ == "__main__":
    bundle()
