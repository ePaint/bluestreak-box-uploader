"""Data models for Bluestreak Box Uploader."""

from dataclasses import dataclass, field
from enum import Enum


class UploadStatus(Enum):
    """Status of an upload job."""

    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Customer:
    """Customer record from Bluestreak."""

    cst_id: int
    cst_name: str
    cst_integration_id: str | None  # Box folder ID


@dataclass
class MediaFile:
    """Media file linked to a certification."""

    med_id: int
    med_description: str
    med_full_path: str  # Relative path from media root
    medx_id: int
    not_id: int | None


@dataclass
class Certification:
    """Certification record with linked media files."""

    crt_id: int
    crt_cert_no: str
    crt_cust_name: str
    crt_cst_id: int
    crt_po_number: str | None
    crt_or_id: int
    media_files: list[MediaFile] = field(default_factory=list)


@dataclass
class UploadJob:
    """Tracks upload status for a single file."""

    certification: Certification
    media_file: MediaFile
    status: UploadStatus = UploadStatus.PENDING
    box_file_id: str | None = None
    error_message: str | None = None
    progress_percent: int = 0
