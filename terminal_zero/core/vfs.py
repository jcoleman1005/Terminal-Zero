from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from terminal_zero.core.events import Event


@dataclass
class VFSNode:
    type: str  # "dir" or "file"
    permissions: str = "755"
    owner: str = "root"
    group: str = "root"
    content: Optional[str] = None
    children: Dict[str, "VFSNode"] = field(default_factory=dict)

    def is_dir(self) -> bool:
        return self.type == "dir"

    def is_file(self) -> bool:
        return self.type == "file"

    def can_write(self, user: str) -> bool:
        if user == "root":
            return True
        try:
            mode = int(self.permissions, 8) if (self.permissions and self.permissions.isdigit()) else 0
        except ValueError:
            mode = 0
        if self.owner == user:
            return bool(mode & 0o200)
        return bool(mode & 0o002)

    def can_read(self, user: str) -> bool:
        if user == "root":
            return True
        try:
            mode = int(self.permissions, 8) if (self.permissions and self.permissions.isdigit()) else 0
        except ValueError:
            mode = 0
        if self.owner == user:
            return bool(mode & 0o400)
        return bool(mode & 0o004)

    def can_execute(self, user: str) -> bool:
        if user == "root":
            return True
        try:
            mode = int(self.permissions, 8) if (self.permissions and self.permissions.isdigit()) else 0
        except ValueError:
            mode = 0
        if self.owner == user:
            return bool(mode & 0o100)
        return bool(mode & 0o001)


class VirtualFilesystem:
    def __init__(self, root_node: VFSNode, event_bus: Optional[Any] = None):
        self.root = root_node
        self.bus = event_bus

    def set_event_bus(self, event_bus: Any) -> None:
        self.bus = event_bus

    def can_write(self, node: VFSNode, user: str) -> bool:
        return node.can_write(user)

    def can_read(self, node: VFSNode, user: str) -> bool:
        return node.can_read(user)

    def can_execute(self, node: VFSNode, user: str) -> bool:
        return node.can_execute(user)

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

    def write_file(
        self,
        current_cwd: List[str],
        target_path: str,
        content: str,
        append: bool = False,
        owner: str = "root",
        permissions: str = "644",
        group: Optional[str] = None,
        user: Optional[str] = None
    ) -> Tuple[bool, str]:
        node, resolved_path = self.get_node(current_cwd, target_path)
        acting_user = user if user is not None else owner
        if node:
            if node.is_dir():
                return False, "Is a directory"
            if not self.can_write(node, acting_user):
                return False, "Permission denied"
            if append:
                node.content = (node.content or "") + content
            else:
                node.content = content
                node.owner = owner
                if group is not None:
                    node.group = group
                if permissions:
                    node.permissions = permissions

            if self.bus:
                self.bus.publish(Event("vfs_node_modified", {
                    "path": resolved_path,
                    "path_str": "/" + "/".join(resolved_path),
                    "content": node.content or "",
                    "append": append,
                    "owner": node.owner
                }))
            return True, ""
        
        # Create new file: parent directory must exist
        parent_parts = resolved_path[:-1]
        filename = resolved_path[-1] if resolved_path else target_path.split("/")[-1]
        parent_node = self.resolve_path(parent_parts)
        if not parent_node or not parent_node.is_dir():
            return False, "No such file or directory"
        if not self.can_write(parent_node, acting_user):
            return False, "Permission denied"

        actual_group = group if group is not None else ("alice" if owner == "alice" else "root")
        new_node = VFSNode(type="file", permissions=permissions, owner=owner, group=actual_group, content=content)
        parent_node.children[filename] = new_node

        if self.bus:
            self.bus.publish(Event("vfs_node_modified", {
                "path": resolved_path,
                "path_str": "/" + "/".join(resolved_path),
                "content": new_node.content or "",
                "append": append,
                "owner": new_node.owner
            }))
        return True, ""

    def delete_node(
        self,
        current_cwd: List[str],
        target_path: str,
        recursive: bool = False,
        user: Optional[str] = None
    ) -> Tuple[bool, str]:
        node, resolved_path = self.get_node(current_cwd, target_path)
        if not node:
            return False, f"cannot remove '{target_path}': No such file or directory"
        if node.is_dir() and not recursive:
            return False, f"cannot remove '{target_path}': Is a directory"

        parent_parts = resolved_path[:-1]
        filename = resolved_path[-1] if resolved_path else ""
        parent_node = self.root if not parent_parts else self.resolve_path(parent_parts)
        if not parent_node or not parent_node.is_dir():
            return False, f"cannot remove '{target_path}': No such file or directory"

        if user is not None and user != "root":
            if not self.can_write(parent_node, user) or not self.can_execute(parent_node, user):
                return False, f"cannot remove '{target_path}': Permission denied"
            if node.owner == "root" and not self.can_write(node, user):
                return False, f"cannot remove '{target_path}': Permission denied"

        if filename in parent_node.children:
            del parent_node.children[filename]
            if self.bus:
                self.bus.publish(Event("vfs_node_deleted", {
                    "path": resolved_path,
                    "path_str": "/" + "/".join(resolved_path),
                }))
            return True, ""
        return False, f"cannot remove '{target_path}': No such file or directory"

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
