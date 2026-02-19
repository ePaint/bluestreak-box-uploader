"""Box service exceptions."""


class BoxServiceError(Exception):
    """Base exception for Box service errors."""

    pass


class BoxAuthError(BoxServiceError):
    """Authentication failed."""

    pass


class BoxUploadError(BoxServiceError):
    """Upload failed."""

    pass


class BoxFolderError(BoxServiceError):
    """Folder operation failed."""

    pass
