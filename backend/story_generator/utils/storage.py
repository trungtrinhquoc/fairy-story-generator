"""
Supabase storage utilities.
Helper functions for file uploads.
"""

import logging
from typing import Optional
from story_generator.database import db

logger = logging.getLogger(__name__)


async def upload_to_supabase(
    bucket: str,
    path: str,
    file_data: bytes,
    content_type: str = "image/png"
) -> Optional[str]:
    """
    Upload file to Supabase Storage and return public URL.
    
    Args:
        bucket: Storage bucket name (e.g., 'story-images')
        path: File path in bucket (e.g., 'story_id/scene_1.png')
        file_data: File bytes
        content_type: MIME type
    
    Returns:
        Public URL or None if failed
    """
    return await db.upload_file(bucket, path, file_data, content_type)


async def get_public_url(bucket: str, path: str) -> str:
    """
    Get public URL for a file in Supabase Storage.
    
    Args:
        bucket: Storage bucket name
        path: File path in bucket
    
    Returns:
        Public URL
    """
    return db.client.storage.from_(bucket).get_public_url(path)