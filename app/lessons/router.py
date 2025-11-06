"""
This module defines the routing layer for lesson playback endpoints.

It exposes routes under the /lessons prefix, enabling authenticated users
to request video playback information (such as Mux manifest URLs) for lessons
in which they are enrolled.

Core responsibilities:
- Validate user authentication and enrollment.
- Retrieve lesson metadata from the NoSQL (MongoDB) database.
- Integrate with Mux via `mux_service` to generate signed playback URLs.
- Provide a clean JSON response containing all relevant playback information
  for front-end clients or embedded players.

Dependencies:
- User authentication is handled by `get_current_user` from `app.auth.deps`.
- Enrollment verification uses `user_ops` from the SQL service layer.
- Video playback data is fetched and enriched using `mux_service`.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.deps import get_current_user
from app.models.sql.database import get_db as get_sql_db
from app.services import user_ops
from app.services.mux_service import create_signed_manifest_url
from app.models.no_sql.lesson import get_lesson

router = APIRouter(prefix="/lessons")

@router.get("/{lesson_id}/playback")
async def get_playback(
    lesson_id: str,
    current_user = Depends(get_current_user),
    sql_db: AsyncSession = Depends(get_sql_db)
):
    """
    Retrieve and return playback information for a specific lesson.

    This endpoint ensures that the requested lesson exists in database, includes valid Mux playback metadata.
    The authenticated user is enrolled in the corresponding course.

    If all conditions are met, it returns a structured JSON object containing:
      - playback_id: The Mux playback identifier.
      - manifest_url: A signed M3U8 manifest URL (valid temporarily).
      - watch_page_url: Optional Mux watch page link.
      - thumbnail_url: Preview image of the video.
      - mux: Sub-object with asset metadata (asset_id, status, etc.).
      - embed_iframe: An embeddable <iframe> snippet ready for the front-end.

    Args:
        lesson_id (str): The unique identifier of the lesson in MongoDB.
        current_user (User): The authenticated user obtained from the token.
        sql_db (AsyncSession): SQLAlchemy async session for relational data (e.g., enrollments).

    Returns:
        dict: JSON response containing playback and metadata details.

    Raises:
        HTTPException:
            - 404: If the lesson or Mux metadata is missing.
            - 403: If the user is not enrolled in the course.
    """

    lesson = await get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not foud")
    
    ## Ensure lesson has Mux Metadata.
    mux_meta = lesson.get("mux") or {}
    if not mux_meta.get("playback_id") and not mux_meta.get("manifest_url"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playback not available")
    
    ## Verify enrollment (application level check)
    course_id = str(lesson.get("course_id"))
    enrolled = await user_ops.is_enrolled(sql_db, current_user.id, course_id)
    if not enrolled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not enrolled.")
    
    # Signed manifest URL via mux_service (with caching)
    signed_url = await create_signed_manifest_url(mux_meta["playback_id"], str(current_user.id))
    
    
    response = {
        "playback_id": mux_meta.get("playback_id"),
        "manifest_url": signed_url,
        "watch_page_url": mux_meta.get("watch_page_url"),
        "thumbnail_url": mux_meta.get("thumbnail_url"),
        "mux": {k: mux_meta.get(k) for k in ("asset_id", "status", "duration", "visibility")},
        
        # Embed iframe ready to use, for front-end
        "embed_iframe": (
            f'<iframe src="https://player.mux.com/{mux_meta.get("playback_id")}" '
            'style="width:100%;border:none;aspect-ratio:16/9;" '
            'allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture;" '
            'allowfullscreen></iframe>' if mux_meta.get("playback_id") else None
        )
    }
    return response