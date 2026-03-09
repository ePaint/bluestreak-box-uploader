"""QThread workers for background processing."""

import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from database.connection import DatabaseConfig
from database.queries import query_order_with_customer, query_partial_order_with_customer
from database.models import Certification, Customer, DuplicateAction, UploadJob, UploadStatus, UploadHistoryRecord
from database.history import generate_session_id, record_upload
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
    finished = Signal(int, int, int, bool)  # success_count, failed_count, skipped_count, was_cancelled
    error = Signal(str)  # error message
    duplicate_found = Signal(str, str)  # filename, cert_no

    def __init__(
        self,
        jwt_config_path: str,
        certifications: list[Certification],
        root_folder_id: str,
        media_base_path: Path,
        customer_name: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._jwt_config_path = jwt_config_path
        self._certifications = certifications
        self._root_folder_id = root_folder_id
        self._media_base_path = media_base_path
        self._customer_name = customer_name
        self._session_id = generate_session_id()
        self._cancelled = False

        # Duplicate handling state
        self._duplicate_response: DuplicateAction | None = None
        self._apply_to_all: bool = False
        self._pending_response = threading.Event()

    def cancel(self) -> None:
        """Request cancellation."""
        self._cancelled = True
        # Unblock waiting for duplicate response if cancelled
        self._pending_response.set()

    def set_duplicate_response(self, action: DuplicateAction, apply_to_all: bool) -> None:
        """Set the user's response to a duplicate file prompt."""
        self._duplicate_response = action
        self._apply_to_all = apply_to_all
        self._pending_response.set()

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
        skipped_count = 0

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
                    if cert.crt_po_number:
                        parent_folder = f"PO#{cert.crt_po_number} (BII WO#{cert.crt_or_id})"
                    else:
                        parent_folder = f"BII WO#{cert.crt_or_id}"
                    folder_path = f"{parent_folder}/Cert#{cert.crt_cert_no}"

                    # Ensure folder exists
                    target_folder_id = uploader.folder_manager.ensure_folder_path(
                        self._root_folder_id, folder_path
                    )

                    # Check for duplicate file
                    existing_file_id = uploader.file_exists(target_folder_id, filename)
                    if existing_file_id:
                        # Determine action based on apply_to_all or ask user
                        if self._apply_to_all and self._duplicate_response:
                            action = self._duplicate_response
                        else:
                            # Reset event and wait for response from GUI
                            self._pending_response.clear()
                            self.duplicate_found.emit(filename, cert.crt_cert_no)
                            self._pending_response.wait()

                            if self._cancelled:
                                break

                            action = self._duplicate_response

                        if action == DuplicateAction.SKIP:
                            job.status = UploadStatus.SKIPPED
                            job.progress_percent = 100
                            skipped_count += 1
                            self._record_and_emit(job, cert, filename, local_path, "skipped")
                            continue
                        elif action == DuplicateAction.CANCEL:
                            self.cancel()
                            break
                        # else REPLACE - proceed with upload

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

                self._record_and_emit(job, cert, filename, local_path)

        self.finished.emit(success_count, failed_count, skipped_count, self._cancelled)

    def _record_and_emit(
        self,
        job: UploadJob,
        cert: Certification,
        filename: str,
        local_path: Path,
        status_override: str | None = None,
    ) -> None:
        """Record upload to history and emit completion signal."""
        file_size = local_path.stat().st_size if local_path.exists() else None

        # Determine status string
        if status_override:
            status = status_override
        elif job.status == UploadStatus.COMPLETED:
            status = "success"
        elif job.status == UploadStatus.SKIPPED:
            status = "skipped"
        else:
            status = "failed"

        history_record = UploadHistoryRecord(
            session_id=self._session_id,
            timestamp=datetime.now(),
            order_id=cert.crt_or_id,
            cert_no=cert.crt_cert_no,
            filename=filename,
            box_file_id=job.box_file_id,
            status=status,
            error_msg=job.error_message,
            customer_name=self._customer_name,
            po_number=cert.crt_po_number,
            file_size=file_size,
        )
        record_upload(history_record)

        self.file_completed.emit(job)
