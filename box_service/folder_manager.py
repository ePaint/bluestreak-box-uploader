"""Box folder management with caching."""

from box_sdk_gen import BoxClient
from box_sdk_gen.schemas import FolderFull

from box_service.exceptions import BoxFolderError


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
        """Find a folder by name in parent, returns folder ID or None."""
        try:
            items = self._client.folders.get_folder_items(parent_id)
            for item in items.entries:
                if item.type == "folder" and item.name == name:
                    return item.id
            return None
        except Exception as e:
            raise BoxFolderError(f"Failed to list folder {parent_id}: {e}")

    def _create_folder(self, parent_id: str, name: str) -> str:
        """Create a folder, returns folder ID."""
        try:
            from box_sdk_gen.managers.folders import CreateFolderParent

            folder = self._client.folders.create_folder(
                name=name,
                parent=CreateFolderParent(id=parent_id),
            )
            return folder.id
        except Exception as e:
            # Check if folder already exists (race condition)
            if "item_name_in_use" in str(e).lower():
                folder_id = self._find_folder(parent_id, name)
                if folder_id:
                    return folder_id
            raise BoxFolderError(f"Failed to create folder '{name}' in {parent_id}: {e}")

    def ensure_folder_path(self, root_id: str, path: str) -> str:
        """
        Ensure a folder path exists, creating folders as needed.

        Args:
            root_id: The root folder ID to start from
            path: Path like "444337 (PO#TEST123)/444337-1"

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
