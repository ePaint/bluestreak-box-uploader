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
        manager._cache["root"] = {"444337 (PO#TEST)": "order123"}
        manager._cache["order123"] = {"444337-1": "cert123"}

        result = manager.ensure_folder_path("root", "444337 (PO#TEST)/444337-1")

        assert result == "cert123"

    def test_clear_cache(self):
        """Test cache clearing."""
        mock_client = Mock()
        manager = FolderManager(mock_client)

        manager._cache["root"] = {"folder": "id123"}
        manager.clear_cache()

        assert len(manager._cache) == 0


class TestFolderPath:
    """Tests for folder path formatting."""

    def test_folder_path_with_po(self):
        """Test folder path construction with PO number."""
        order_id = 444337
        po_number = "TEST123"
        cert_no = "444337-1"

        po_part = f" (PO#{po_number})" if po_number else ""
        path = f"{order_id}{po_part}/{cert_no}"

        assert path == "444337 (PO#TEST123)/444337-1"

    def test_folder_path_without_po(self):
        """Test folder path construction without PO number."""
        order_id = 444337
        po_number = None
        cert_no = "444337-1"

        po_part = f" (PO#{po_number})" if po_number else ""
        path = f"{order_id}{po_part}/{cert_no}"

        assert path == "444337/444337-1"
