from __future__ import annotations

import os
from .xrd_types import allowed_suffix_types, FormatSelector
from hollarek.resources import FsysNode
from typing import Optional
# -------------------------------------------

def find_all_parsable_files(dir_path : str, format_selector : Optional[FormatSelector]) -> list[str]:
    if not os.path.isdir(dir_path):
        raise ValueError(f"Given path {dir_path} is not a directory")
    root_node = FsysNode(path=dir_path)
    xrd_files_nodes = root_node.select_file_nodes(allowed_formats=allowed_suffix_types)

    xrd_file_paths = [node.path for node in xrd_files_nodes if format_selector.is_allowed(node.get_suffix())]
    return xrd_file_paths

