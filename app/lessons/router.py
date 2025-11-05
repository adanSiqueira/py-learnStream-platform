from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from bson import ObjectId
from typing import Dict
from app.auth.deps import get_current_user
from app.models.sql.database import get_db as get_sql_db
from app.services import user_ops
from app.models.no_sql.lesson import get_lesson

router = APIRouter(prefix="/lessons")

@router.get("/{lesson_id}/playback")
async def get_playback(
    lesson_id: str,
    current_user = Depends(get_current_user),
    sql_db: AsyncSession = Depends(get_sql_db)
):
    """
    Return playback information for a lesson if the current_user is enrolled.
    Response contains:
      - playback_id
      - manifest_url (m3u8) if available
      - embed_iframe (optional HTML snippet)
      - mux metadata
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
    
    
    response = {
        "playback_id": mux_meta.get("playback_id"),
        "manifest_url": mux_meta.get("manifest_url"),
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
    

    
