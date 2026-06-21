"""API router for transcript refinement with Mistral.

Provides endpoints for:
- Listing available refinement modes
- Refining transcripts using Mistral API
- Checking refinement availability
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.refine import (
    get_refinement_service,
    RefinementService,
    RefinementMode,
    RefinementResult
)
from services.file_service import get_transcription

router = APIRouter(prefix="/api/refine", tags=["refine"])


class RefineRequest(BaseModel):
    """Request body for refining an existing transcription."""
    mode: str
    custom_instruction: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None


class RefineTextRequest(RefineRequest):
    """Request body for refining arbitrary text not tied to a file."""
    text: str


def get_refiner() -> RefinementService:
    """Dependency injection for refinement service."""
    return get_refinement_service()


@router.get("/modes")
async def list_modes(refiner: RefinementService = Depends(get_refiner)):
    """List all available refinement modes.
    
    Returns:
        Dictionary mapping mode IDs to their configuration
    """
    return refiner.get_available_modes()


@router.get("/available")
async def check_availability(refiner: RefinementService = Depends(get_refiner)):
    """Check if Mistral refinement is available.
    
    Returns:
        JSON with availability status and modes
    """
    return {
        "available": refiner.is_available(),
        "modes": list(refiner.get_available_modes().keys()) if refiner.is_available() else []
    }


@router.post("/{file_id}", response_model=RefinementResult)
async def refine_transcript(
    file_id: str,
    req: RefineRequest,
    refiner: RefinementService = Depends(get_refiner)
):
    """Refine a transcription using Mistral API.

    The transcript text is loaded from the stored transcription; the request body
    carries the chosen mode and optional overrides (sent as JSON, not query params,
    so long instructions are handled safely).

    Raises:
        HTTPException: If file or transcription not found
    """
    transcription = get_transcription(file_id)
    if transcription is None:
        raise HTTPException(status_code=404, detail=f"No transcription found for file {file_id}")

    result = refiner.refine(
        transcript=transcription.text,
        mode_id=req.mode,
        custom_instruction=req.custom_instruction,
        model=req.model,
        temperature=req.temperature,
    )

    # Attach useful context for the UI when the refinement succeeded.
    if result.success:
        result.metadata["file_id"] = file_id
        result.metadata["original_model"] = transcription.model

    return result


@router.post("/text", response_model=RefinementResult)
async def refine_text(
    req: RefineTextRequest,
    refiner: RefinementService = Depends(get_refiner)
):
    """Refine arbitrary text using Mistral API.

    Useful for testing or external integrations where the text does not come from
    a stored file transcription.
    """
    return refiner.refine(
        transcript=req.text,
        mode_id=req.mode,
        custom_instruction=req.custom_instruction,
        model=req.model,
        temperature=req.temperature,
    )