from app.core.exceptions.custom_exceptions.ClientExceptionHandler import ClientException


def validate_media(file_type: str, file_length: int) -> None:

    allowed_media = {
        # Audio types (max 16 MB)
        "audio/aac": 16 * 1024 * 1024,
        "audio/amr": 16 * 1024 * 1024,
        "audio/mpeg": 16 * 1024 * 1024,
        "audio/mp4": 16 * 1024 * 1024,
        "audio/ogg": 16 * 1024 * 1024,
        # Document types (max 100 MB)
        "text/plain": 100 * 1024 * 1024,
        "application/vnd.ms-excel": 100 * 1024 * 1024,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": 100
        * 1024
        * 1024,
        "application/msword": 100 * 1024 * 1024,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 100
        * 1024
        * 1024,
        "application/vnd.ms-powerpoint": 100 * 1024 * 1024,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": 100
        * 1024
        * 1024,
        "application/pdf": 100 * 1024 * 1024,
        # Image types (max 5 MB)
        "image/jpeg": 5 * 1024 * 1024,
        "image/png": 5 * 1024 * 1024,
        # Sticker (WebP) - using the animated sticker size (500 KB)
        "image/webp": 500 * 1024,
        # Video types (max 16 MB)
        "video/3gpp": 16 * 1024 * 1024,
        "video/mp4": 16 * 1024 * 1024,
    }

    if file_type not in allowed_media:
        raise ClientException(f"Unsupported file type: {file_type}")

    max_allowed_size = allowed_media[file_type]
    if file_length > max_allowed_size:
        raise ClientException(
            f"File size {file_length} bytes exceeds maximum allowed size for {file_type} ({max_allowed_size} bytes)"
        )
