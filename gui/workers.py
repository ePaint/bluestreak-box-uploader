"""QThread workers for background processing."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from database.connection import DatabaseConfig
from database.queries import query_order_with_customer, query_partial_order_with_customer
from database.models import Certification, Customer, UploadJob, UploadStatus
from box_service import BoxUploader


class QueryWorker(QThread):
    """Worker thread for querying certifications from database."""

    finished = Signal(object, object)  # (list[Certification], Customer | None)
    error = Signal(str)  # error message

    def __init__(self, config: DatabaseConfig, order_id: int, parent=None):
        super().__init__(parent)
        self._config = config
        self._order_id = order_id

    def run(self) -> None:
        try:
            certs, customer = query_order_with_customer(self._config, self._order_id)
            self.finished.emit(certs, customer)
        except Exception as e:
            self.error.emit(str(e))


class PartialQueryWorker(QThread):
    """Worker thread for querying certifications by partial order ID."""

    finished = Signal(object, object)  # (list[Certification], Customer | None)
    error = Signal(str)  # error message

    def __init__(
        self, config: DatabaseConfig, search_term: str, limit: int, parent=None
    ):
        super().__init__(parent)
        self._config = config
        self._search_term = search_term
        self._limit = limit

    def run(self) -> None:
        try:
            certs, customer = query_partial_order_with_customer(
                self._config, self._search_term, self._limit
            )
            self.finished.emit(certs, customer)
        except Exception as e:
            self.error.emit(str(e))


class UploadWorker(QThread):
    """Worker thread for uploading files to Box."""

    progress = Signal(int, int, str)  # current, total, filename
    file_completed = Signal(object)  # UploadJob
    finished = Signal(int, int)  # success_count, failed_count
    error = Signal(str)  # error message

    def __init__(
        self,
        jwt_config_path: str,
        certifications: list[Certification],
        root_folder_id: str,
        media_base_path: Path,
        parent=None,
    ):
        super().__init__(parent)
        self._jwt_config_path = jwt_config_path
        self._certifications = certifications
        self._root_folder_id = root_folder_id
        self._media_base_path = media_base_path
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation."""
        self._cancelled = True

    def run(self) -> None:
        try:
            uploader = BoxUploader(self._jwt_config_path)
            uploader.connect()
        except Exception as e:
            self.error.emit(f"Failed to connect to Box: {e}")
            return

        # Calculate total files
        total_files = sum(len(c.media_files) for c in self._certifications)
        current_file = 0
        success_count = 0
        failed_count = 0

        for cert in self._certifications:
            if self._cancelled:
                break

            for media_file in cert.media_files:
                if self._cancelled:
                    break

                current_file += 1
                filename = Path(media_file.med_full_path).name
                self.progress.emit(current_file, total_files, filename)

                # Create a job for this file
                job = UploadJob(
                    certification=cert,
                    media_file=media_file,
                    status=UploadStatus.UPLOADING,
                )

                local_path = self._media_base_path / media_file.med_full_path

                try:
                    # Build folder path
                    po_part = f" (PO#{cert.crt_po_number})" if cert.crt_po_number else ""
                    folder_path = f"{cert.crt_or_id}{po_part}/{cert.crt_cert_no}"

                    # Ensure folder exists
                    target_folder_id = uploader.folder_manager.ensure_folder_path(
                        self._root_folder_id, folder_path
                    )

                    # Upload file
                    uploaded = uploader.upload_file(local_path, target_folder_id)
                    job.status = UploadStatus.COMPLETED
                    job.box_file_id = uploaded.id
                    job.progress_percent = 100
                    success_count += 1

                except FileNotFoundError:
                    job.status = UploadStatus.FAILED
                    job.error_message = f"File not found: {local_path}"
                    failed_count += 1

                except Exception as e:
                    job.status = UploadStatus.FAILED
                    job.error_message = str(e)
                    failed_count += 1

                self.file_completed.emit(job)

        self.finished.emit(success_count, failed_count)
