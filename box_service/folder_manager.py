"""Box folder management with caching."""

import time

from box_sdk_gen import BoxClient
from box_sdk_gen.schemas import FolderFull

from box_service.exceptions import BoxFolderError


def _is_jti_error(error: Exception) -> bool:
    """Check if error is a JWT jti collision error."""
    error_str = str(error).lower()
    return "invalid_grant" in error_str and "jti" in error_str


def _retry_on_jti_error(func, *args, max_retries: int = 3, base_delay: float = 1.0, **kwargs):
    """Retry a function if it fails with a JWT jti collision error."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if _is_jti_error(e) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                time.sleep(delay)
                last_error = e
            else:
                raise
    raise last_error


def _extract_conflict_id(error: Exception) -> str | None:
    """Extract conflicting folder/item ID from a Box 409 error, if available."""
    # 1. Try response_info.context_info
    response_info = getattr(error, "response_info", None)
    if response_info:
        context_info = getattr(response_info, "context_info", None)
        if isinstance(context_info, dict):
            conflicts = context_info.get("conflicts", [])
            if conflicts and isinstance(conflicts, list):
                first = conflicts[0]
                if isinstance(first, dict) and "id" in first:
                    return str(first["id"])

    # 2. Try direct context_info attribute on error
    context_info = getattr(error, "context_info", None)
    if isinstance(context_info, dict):
        conflicts = context_info.get("conflicts", [])
        if conflicts and isinstance(conflicts, list):
            first = conflicts[0]
            if isinstance(first, dict) and "id" in first:
                return str(first["id"])

    # 3. Fallback: regex search in str(error)
    import re
    match = re.search(
        r"['\"]?conflicts['\"]?\s*:\s*\[\s*\{[^}]*?['\"]?id['\"]?\s*:\s*['\"]?(\d+)['\"]?",
        str(error),
    )
    if match:
        return match.group(1)

    return None


class FolderManager:
    """Manages Box folder operations with caching."""

    def __init__(self, client: BoxClient):
        self._client = client
        # Cache: folder_id -> {subfolder_name -> folder_id}
        self._cache: dict[str, dict[str, str]] = {}

    def get_or_create_folder(self, parent_id: str, name: str) -> str:
        """Get or create a folder, returns folder ID. Uses cache."""
        # Check cache first
        if parent_id in self._cache and name in self._cache[parent_id]:
            return self._cache[parent_id][name]

        # Try to find existing folder
        folder_id = self._find_folder(parent_id, name)

        if folder_id is None:
            # Create new folder
            folder_id = self._create_folder(parent_id, name)

        # Update cache
        if parent_id not in self._cache:
            self._cache[parent_id] = {}
        self._cache[parent_id][name] = folder_id

        return folder_id

    def _find_folder(self, parent_id: str, name: str) -> str | None:
        """Find a folder by name in parent, returns folder ID or None. Paginates across all items."""
        try:
            offset = 0
            limit = 1000
            while True:
                items = _retry_on_jti_error(
                    self._client.folders.get_folder_items,
                    parent_id,
                    offset=offset,
                    limit=limit,
                )
                entries = getattr(items, "entries", None) or []
                if not entries:
                    break

                if parent_id not in self._cache:
                    self._cache[parent_id] = {}

                found_id = None
                for item in entries:
                    item_type = getattr(item, "type", None)
                    item_name = getattr(item, "name", None)
                    item_id = getattr(item, "id", None)
                    if item_type == "folder" and item_name:
                        self._cache[parent_id][item_name] = item_id
                        if item_name == name:
                            found_id = item_id

                if found_id is not None:
                    return found_id

                if len(entries) < limit:
                    break
                offset += len(entries)
                total_count = getattr(items, "total_count", None)
                if total_count is not None and offset >= total_count:
                    break

            return None
        except Exception as e:
            raise BoxFolderError(f"Failed to list folder {parent_id}: {e}")

    def _create_folder(self, parent_id: str, name: str) -> str:
        """Create a folder, returns folder ID."""
        try:
            from box_sdk_gen.managers.folders import CreateFolderParent

            folder = _retry_on_jti_error(
                self._client.folders.create_folder,
                name=name,
                parent=CreateFolderParent(id=parent_id),
            )
            return folder.id
        except Exception as e:
            # Check if folder already exists (race condition or missed in cache/search)
            if "item_name_in_use" in str(e).lower():
                conflict_id = _extract_conflict_id(e)
                if conflict_id:
                    return conflict_id
                folder_id = self._find_folder(parent_id, name)
                if folder_id:
                    return folder_id
            raise BoxFolderError(f"Failed to create folder '{name}' in {parent_id}: {e}")

    def ensure_folder_path(self, root_id: str, path: str) -> str:
        """
        Ensure a folder path exists, creating folders as needed.

        Args:
            root_id: The root folder ID to start from
            path: Path like "PO#TEST123 (BII WO#444337)/Cert#444337-1"

        Returns:
            The folder ID of the final folder in the path
        """
        current_id = root_id
        parts = [p.strip() for p in path.split("/") if p.strip()]

        for part in parts:
            current_id = self.get_or_create_folder(current_id, part)

        return current_id

    def clear_cache(self) -> None:
        """Clear the folder cache."""
        self._cache.clear()
