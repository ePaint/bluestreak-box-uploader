"""Tests for Box service layer."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from box_service.folder_manager import FolderManager
from box_service.exceptions import BoxFolderError


class TestFolderManager:
    """Tests for FolderManager."""

    def test_cache_hit(self):
        """Test that cached folder IDs are returned."""
        mock_client = Mock()
        manager = FolderManager(mock_client)

        # Pre-populate cache
        manager._cache["root123"] = {"subfolder": "folder456"}

        # Should return cached value without API call
        result = manager.get_or_create_folder("root123", "subfolder")

        assert result == "folder456"
        mock_client.folders.get_folder_items.assert_not_called()

    def test_find_existing_folder(self):
        """Test finding an existing folder."""
        mock_client = Mock()

        # Mock folder items response
        mock_item = Mock()
        mock_item.type = "folder"
        mock_item.name = "test_folder"
        mock_item.id = "found123"

        mock_items = Mock()
        mock_items.entries = [mock_item]
        mock_client.folders.get_folder_items.return_value = mock_items

        manager = FolderManager(mock_client)
        result = manager.get_or_create_folder("root123", "test_folder")

        assert result == "found123"
        assert manager._cache["root123"]["test_folder"] == "found123"

    def test_create_new_folder(self):
        """Test creating a new folder when it doesn't exist."""
        mock_client = Mock()

        # Mock empty folder items (folder doesn't exist)
        mock_items = Mock()
        mock_items.entries = []
        mock_client.folders.get_folder_items.return_value = mock_items

        # Mock folder creation
        mock_folder = Mock()
        mock_folder.id = "new123"
        mock_client.folders.create_folder.return_value = mock_folder

        manager = FolderManager(mock_client)
        result = manager.get_or_create_folder("root123", "new_folder")

        assert result == "new123"
        mock_client.folders.create_folder.assert_called_once()

    def test_ensure_folder_path_single(self):
        """Test ensuring a single folder path."""
        mock_client = Mock()

        mock_item = Mock()
        mock_item.type = "folder"
        mock_item.name = "test"
        mock_item.id = "test123"

        mock_items = Mock()
        mock_items.entries = [mock_item]
        mock_client.folders.get_folder_items.return_value = mock_items

        manager = FolderManager(mock_client)
        result = manager.ensure_folder_path("root", "test")

        assert result == "test123"

    def test_ensure_folder_path_nested(self):
        """Test ensuring a nested folder path."""
        mock_client = Mock()
        manager = FolderManager(mock_client)

        # Pre-populate cache to avoid API calls
        manager._cache["root"] = {"Certifications": "certs1"}
        manager._cache["certs1"] = {"PO#TEST (BII WO#444337)": "order123"}
        manager._cache["order123"] = {"Cert#444337-1": "cert123"}

        result = manager.ensure_folder_path(
            "root", "Certifications/PO#TEST (BII WO#444337)/Cert#444337-1"
        )

        assert result == "cert123"

    def test_find_folder_with_pagination(self):
        """Test finding a folder across multiple pages."""
        mock_client = Mock()

        # Page 1: 1000 dummy folders
        page1_entries = []
        for i in range(1000):
            item = Mock()
            item.type = "folder"
            item.name = f"other_{i}"
            item.id = f"other_id_{i}"
            page1_entries.append(item)
        mock_page1 = Mock()
        mock_page1.entries = page1_entries
        mock_page1.total_count = 1001

        # Page 2: target folder
        target_item = Mock()
        target_item.type = "folder"
        target_item.name = "target_folder"
        target_item.id = "target_id_999"
        mock_page2 = Mock()
        mock_page2.entries = [target_item]
        mock_page2.total_count = 1001

        mock_client.folders.get_folder_items.side_effect = [mock_page1, mock_page2]

        manager = FolderManager(mock_client)
        result = manager.get_or_create_folder("root123", "target_folder")

        assert result == "target_id_999"
        assert mock_client.folders.get_folder_items.call_count == 2
        assert manager._cache["root123"]["target_folder"] == "target_id_999"

    def test_create_folder_conflict_with_context_info(self):
        """Test that 409 item_name_in_use extracts conflict ID from context_info."""
        mock_client = Mock()

        # Folder not found initially
        mock_empty = Mock()
        mock_empty.entries = []
        mock_client.folders.get_folder_items.return_value = mock_empty

        # Create folder raises 409 with context_info
        class Mock409Error(Exception):
            pass

        err = Mock409Error("409 Item with the same name already exists: item_name_in_use")
        mock_response_info = Mock()
        mock_response_info.context_info = {
            "conflicts": [{"id": "conflict_id_456", "name": "existing_folder", "type": "folder"}]
        }
        err.response_info = mock_response_info
        mock_client.folders.create_folder.side_effect = err

        manager = FolderManager(mock_client)
        result = manager.get_or_create_folder("root123", "existing_folder")

        assert result == "conflict_id_456"
        assert manager._cache["root123"]["existing_folder"] == "conflict_id_456"

    def test_create_folder_conflict_with_regex_fallback(self):
        """Test that 409 item_name_in_use extracts conflict ID via regex if context_info is in string."""
        mock_client = Mock()

        # Folder not found initially
        mock_empty = Mock()
        mock_empty.entries = []
        mock_client.folders.get_folder_items.return_value = mock_empty

        error_msg = (
            "409 Item with the same name already exists: item_name_in_use\n"
            "'context_info': {'conflicts': [{'etag': '0', 'id': '888999', 'name': 'existing'}]}"
        )
        mock_client.folders.create_folder.side_effect = Exception(error_msg)

        manager = FolderManager(mock_client)
        result = manager.get_or_create_folder("root123", "existing")

        assert result == "888999"
        assert manager._cache["root123"]["existing"] == "888999"

    def test_clear_cache(self):
        """Test cache clearing."""
        mock_client = Mock()
        manager = FolderManager(mock_client)

        manager._cache["root"] = {"folder": "id123"}
        manager.clear_cache()

        assert len(manager._cache) == 0


class TestBoxUploaderPagination:
    """Tests for BoxUploader pagination."""

    def test_file_exists_pagination(self):
        """Test file_exists paginating across pages."""
        from pathlib import Path
        from box_service.uploader import BoxUploader

        uploader = BoxUploader(Path("dummy_jwt.json"))
        uploader._client = Mock()

        # Page 1: 1000 other files
        page1_entries = []
        for i in range(1000):
            item = Mock()
            item.type = "file"
            item.name = f"other_{i}.pdf"
            item.id = f"other_file_{i}"
            page1_entries.append(item)
        mock_page1 = Mock()
        mock_page1.entries = page1_entries
        mock_page1.total_count = 1001

        # Page 2: target file
        target_item = Mock()
        target_item.type = "file"
        target_item.name = "target.pdf"
        target_item.id = "file_target_123"
        mock_page2 = Mock()
        mock_page2.entries = [target_item]
        mock_page2.total_count = 1001

        uploader.client.folders.get_folder_items.side_effect = [mock_page1, mock_page2]

        found_id = uploader.file_exists("folder1", "target.pdf")
        assert found_id == "file_target_123"
        assert uploader.client.folders.get_folder_items.call_count == 2


class TestFolderPath:
    """Tests for folder path formatting."""

    def test_folder_path_with_po(self):
        """Test folder path construction with PO number."""
        order_id = 444337
        po_number = "TEST123"
        cert_no = "444337-1"

        if po_number:
            parent_folder = f"PO#{po_number} (BII WO#{order_id})"
        else:
            parent_folder = f"BII WO#{order_id}"
        path = f"Certifications/{parent_folder}/Cert#{cert_no}"

        assert path == "Certifications/PO#TEST123 (BII WO#444337)/Cert#444337-1"

    def test_folder_path_without_po(self):
        """Test folder path construction without PO number."""
        order_id = 444337
        po_number = None
        cert_no = "444337-1"

        if po_number:
            parent_folder = f"PO#{po_number} (BII WO#{order_id})"
        else:
            parent_folder = f"BII WO#{order_id}"
        path = f"Certifications/{parent_folder}/Cert#{cert_no}"

        assert path == "Certifications/BII WO#444337/Cert#444337-1"
