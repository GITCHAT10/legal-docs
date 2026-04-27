from datetime import datetime, UTC

def create_file_metadata(file_id: str, owner_id: str, filename: str, size: int) -> dict:
    return {
        "file_id": file_id,
        "owner_id": owner_id,
        "filename": filename,
        "size": size,
        "created_at": datetime.now(UTC).isoformat(),
        "shared_with": []
    }
