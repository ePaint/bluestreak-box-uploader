"""Box.com upload service."""

import json
from pathlib import Path
from typing import Callable

from box_sdk_gen import BoxClient, BoxJWTAuth, JWTConfig
from box_sdk_gen.schemas import FileFull, UserFull

from box_service.exceptions import BoxAuthError, BoxUploadError
from box_service.folder_manager import FolderManager
from database.models import Certification, MediaFile, UploadJob, UploadStatus


class BoxUploader:
    """Handles Box.com authentication and file uploads."""

    def __init__(self, jwt_config_path: str | Path):
        self._jwt_config_path = Path(jwt_config_path)
        self._client: BoxClient | None = None
        self._folder_manager: FolderManager | None = None

    def connect(self) -> None:
        """Connect to Box using JWT authentication."""
        if not self._jwt_config_path.exists():
            raise BoxAuthError(f"JWT config file not found: {self._jwt_config_path}")

        try:
            with open(self._jwt_config_path) as f:
                config_dict = json.load(f)

            jwt_config = JWTConfig.from_config_json_string(json.dumps(config_dict))
            auth = BoxJWTAuth(config=jwt_config)
            self._client = BoxClient(auth=auth)
            self._folder_manager = FolderManager(self._client)

        except Exception as e:
            raise BoxAuthError(f"Failed to authenticate with Box: {e}")

    @property
    def client(self) -> BoxClient:
        """Get the Box client, raising if not connected."""
        if self._client is None:
            raise BoxAuthError("Not connected. Call connect() first.")
        return self._client

    @property
    def folder_manager(self) -> FolderManager:
        """Get the folder manager, raising if not connected."""
        if self._folder_manager is None:
            raise BoxAuthError("Not connected. Call connect() first.")
        return self._folder_manager

    def get_current_user(self) -> UserFull:
        """Get the current authenticated user."""
        return self.client.users.get_user_me()

    def upload_file(
        self,
        local_path: Path,
        folder_id: str,
        filename: str | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> FileFull:
        """
        Upload a file to Box.

        Args:
            local_path: Path to the local file
            folder_id: Box folder ID to upload to
            filename: Optional filename override
            progress_callback: Optional callback(bytes_uploaded, total_bytes)

        Returns:
            The uploaded file object
        """
        if not local_path.exists():
            raise BoxUploadError(f"Local file not found: {local_path}")

        upload_name = filename or local_path.name

        try:
            with open(local_path, "rb") as f:
                file_content = f.read()

            from box_sdk_gen.managers.uploads import UploadFileAttributes, UploadFileAttributesParentField

            # Use simple upload for files
            uploaded_files = self.client.uploads.upload_file(
                attributes=UploadFileAttributes(
                    name=upload_name,
                    parent=UploadFileAttributesParentField(id=folder_id),
                ),
                file=file_content,
            )

            if uploaded_files.entries:
                return uploaded_files.entries[0]
            else:
                raise BoxUploadError("Upload succeeded but no file returned")

        except Exception as e:
            if "item_name_in_use" in str(e).lower():
                # File already exists - this is okay for our use case
                # Could implement versioning here if needed
                raise BoxUploadError(f"File already exists: {upload_name}")
            raise BoxUploadError(f"Upload failed: {e}")

    def upload_certification_files(
        self,
        certification: Certification,
        root_folder_id: str,
        media_base_path: Path,
        progress_callback: Callable[[UploadJob], None] | None = None,
    ) -> list[UploadJob]:
        """
        Upload all media files for a certification.

        Args:
            certification: The certification to upload files for
            root_folder_id: Customer's Box folder ID
            media_base_path: Base path for media files
            progress_callback: Optional callback for progress updates

        Returns:
            List of UploadJob objects with status
        """
        jobs: list[UploadJob] = []

        # Create folder path: [OrderID] (PO#[PONumber])/[CertNo]
        po_part = f" (PO#{certification.crt_po_number})" if certification.crt_po_number else ""
        folder_path = f"{certification.crt_or_id}{po_part}/{certification.crt_cert_no}"

        try:
            target_folder_id = self.folder_manager.ensure_folder_path(root_folder_id, folder_path)
        except Exception as e:
            # All files fail if we can't create the folder
            for mf in certification.media_files:
                job = UploadJob(
                    certification=certification,
                    media_file=mf,
                    status=UploadStatus.FAILED,
                    error_message=f"Failed to create folder: {e}",
                )
                jobs.append(job)
            return jobs

        # Upload each file
        for media_file in certification.media_files:
            job = UploadJob(
                certification=certification,
                media_file=media_file,
                status=UploadStatus.UPLOADING,
            )

            if progress_callback:
                progress_callback(job)

            local_path = media_base_path / media_file.med_full_path

            try:
                uploaded = self.upload_file(local_path, target_folder_id)
                job.status = UploadStatus.COMPLETED
                job.box_file_id = uploaded.id
                job.progress_percent = 100
            except BoxUploadError as e:
                job.status = UploadStatus.FAILED
                job.error_message = str(e)
            except FileNotFoundError:
                job.status = UploadStatus.FAILED
                job.error_message = f"File not found: {local_path}"
            except Exception as e:
                job.status = UploadStatus.FAILED
                job.error_message = f"Unexpected error: {e}"

            jobs.append(job)

            if progress_callback:
                progress_callback(job)

        return jobs
