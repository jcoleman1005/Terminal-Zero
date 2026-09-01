from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class VFSNode:
    type: str  # "dir" or "file"
    permissions: str = "755"
    owner: str = "root"
    content: Optional[str] = None
    children: Dict[str, "VFSNode"] = field(default_factory=dict)

    def is_dir(self) -> bool:
        return self.type == "dir"

    def is_file(self) -> bool:
        return self.type == "file"


class VirtualFilesystem:
    def __init__(self, root_node: VFSNode):
        self.root = root_node

    def resolve_path(self, path_parts: List[str]) -> Optional[VFSNode]:
        current = self.root
        for part in path_parts:
            if not current.is_dir():
                return None
            if part not in current.children:
                return None
            current = current.children[part]
        return current

    def get_node(self, current_cwd: List[str], target_path: str) -> Tuple[Optional[VFSNode], List[str]]:
        if not target_path or target_path == ".":
            return self.resolve_path(current_cwd), current_cwd
        
        parts = target_path.split("/")
        if target_path.startswith("/"):
            resolved_parts: List[str] = []
        else:
            resolved_parts = list(current_cwd)

        for part in parts:
            if not part or part == ".":
                continue
            elif part == "..":
                if resolved_parts:
                    resolved_parts.pop()
            elif part == "~":
                resolved_parts = ["home", "alice"]
            else:
                resolved_parts.append(part)

        node = self.resolve_path(resolved_parts)
        return node, resolved_parts

    def write_file(self, current_cwd: List[str], target_path: str, content: str, append: bool = False, owner: str = "root") -> Tuple[bool, str]:
        node, resolved_path = self.get_node(current_cwd, target_path)
        if node:
            if node.is_dir():
                return False, "Is a directory"
            if node.permissions in ["000", "444"]:
                return False, "Permission denied"
            if append:
                node.content = (node.content or "") + content
            else:
                node.content = content
            return True, ""
        
        # Create new file: parent directory must exist
        parent_parts = resolved_path[:-1]
        filename = resolved_path[-1] if resolved_path else target_path.split("/")[-1]
        parent_node = self.resolve_path(parent_parts)
        if not parent_node or not parent_node.is_dir():
            return False, "No such file or directory"
        if parent_node.permissions == "000":
            return False, "Permission denied"

        new_node = VFSNode(type="file", permissions="644", owner=owner, content=content)
        parent_node.children[filename] = new_node
        return True, ""

    def find_nodes(self, start_node: VFSNode, base_display: str = "", base_name: str = "") -> List[Tuple[VFSNode, str, str]]:
        """Returns list of (VFSNode, display_path, filename)."""
        results: List[Tuple[VFSNode, str, str]] = []

        def _recurse(node: VFSNode, cur_disp: str, cur_name: str):
            results.append((node, cur_disp, cur_name))
            if node.is_dir():
                for child_name, child_node in sorted(node.children.items()):
                    sub_display = f"{cur_disp.rstrip('/')}/{child_name}" if cur_disp else child_name
                    _recurse(child_node, sub_display, child_name)

        _recurse(start_node, base_display, base_name)
        return results

    def check_permissions(self, path_parts: List[str], user: str = "alice") -> Tuple[bool, str]:
        """Checks traversal permissions for directory parts along path_parts."""
        curr = self.root
        for part in path_parts:
            if not curr.is_dir() or part not in curr.children:
                return True, ""
            curr = curr.children[part]
            if curr.is_dir() and curr.permissions in ["000", "700", "0700", "600", "644"] and curr.owner != user:
                return False, "Permission denied"
        return True, ""

    def walk(self, current_cwd: List[str], target_path: str = ".") -> List[Tuple[VFSNode, str, str]]:
        start_node, resolved_path = self.get_node(current_cwd, target_path)
        if not start_node:
            return []
        display_prefix = target_path.rstrip("/")
        if not display_prefix:
            display_prefix = "/"
        return self.find_nodes(start_node, display_prefix, resolved_path[-1] if resolved_path else "")
