"""Text refinement service with Mistral integration.

This service provides the refinement modes for post-processing transcripts
using Mistral's API. It implements a registry pattern where each mode is a separate
prompt template, allowing for easy extension.

Modes:
1. Meeting notes / bullet points - Structured summary with key points, decisions, topics
2. Clean transcript - Rewrite transcript to read naturally, fixing transcription errors
3. Action items - Extract structured checklist with tasks, owners, due dates
4. Prompt generator - Create best-practice prompts from transcript intent
5. Custom instruction - Apply user's own instruction to the transcript
"""

import json
import re
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from services.mistral_client import (
    get_mistral_client, 
    MistralClientService, 
    MistralAuthenticationError,
    MistralRateLimitError,
    MistralNetworkError
)


class RefinementMode(Enum):
    """Available refinement modes."""
    MEETING_NOTES = "meeting_notes"
    CLEAN_TRANSCRIPT = "clean_transcript"
    ACTION_ITEMS = "action_items"
    PROMPT_GENERATOR = "prompt_generator"
    CUSTOM = "custom"


@dataclass
class RefinementResult:
    """Result of a refinement operation."""
    success: bool
    refined_text: str
    original_text: str
    mode: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefinementModeConfig:
    """Configuration for a refinement mode."""
    name: str
    description: str
    system_prompt: str
    user_prompt_template: Optional[str] = None
    model: str = "mistral-small-latest"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    output_format: str = "text"  # "text" or "json"
    
    def __post_init__(self):
        # Validate temperature
        if not 0 <= self.temperature <= 1:
            raise ValueError("Temperature must be between 0 and 1")


# Version comment: v1.0 - Initial implementation based on evidence-based prompt engineering
# Follows standards: system/user separation, specific instructions, few-shot exemplars,
# explicit output contracts, low temperature for fidelity, guardrails against fabrication

MEETING_NOTES_SYSTEM_PROMPT = (
    "You are a professional meeting transcription assistant. "
    "Your task is to create structured meeting notes from the provided transcript.\n\n"
    "Guidelines:\n"
    "- Extract key points, decisions, and main topics discussed\n"
    "- Organize as clean, headed bullet points\n"
    "- Do NOT invent content not present in the transcript\n"
    "- Do NOT add interpretation or analysis beyond what was said\n"
    "- Group related points under appropriate headings\n"
    "- Preserve the original meaning and intent\n"
    "- Use clear, professional language\n"
    "- If the transcript is empty or garbled, state that meeting notes cannot be extracted"
)

CLEAN_TRANSCRIPT_SYSTEM_PROMPT = (
    "You are a transcription refinement assistant. "
    "Your task is to clean up a machine-generated transcript to read as natural speech.\n\n"
    "Guidelines:\n"
    "- Rewrite the FULL transcript to read naturally as proper English\n"
    "- Infer likely intended words the transcriber missed from context\n"
    "- Remove filler words (um, ah, like, you know, etc.)\n"
    "- Remove false starts and self-repetition\n"
    "- Preserve ALL meaning and content - do NOT omit or change what was said\n"
    "- Do NOT summarize - this must be the complete transcript, just cleaned up\n"
    "- Do NOT add facts, information, or content not present in the original\n"
    "- Maintain proper punctuation, capitalization, and paragraph structure\n"
    "- If the transcript is empty, return an empty string\n"
    "- If the transcript is garbled or unintelligible, return the original transcript as-is\n\n"
    "Example:\n"
    "Before: so um like i was thinking about the you know the future.. future of real estate market and uh\n"
    "After: I was thinking about the future of the real estate market."
)

ACTION_ITEMS_SYSTEM_PROMPT = (
    "You are an action item extraction assistant. "
    "Your task is to identify action items, tasks, and commitments from the provided transcript.\n\n"
    "Output Requirements:\n"
    "- Return ONLY valid JSON following this exact schema:\n"
    '  {"action_items": [{"task": "string", "owner": "string or null", "due_date": "string or null", "priority": "string or null"}]}' + "\n\n"
    "Guidelines:\n"
    "- Extract only explicit action items, tasks, or commitments mentioned in the transcript\n"
    "- Only include owner if a specific person or team is clearly assigned\n"
    "- Only include due_date if a specific date or timeframe is stated\n"
    "- Only include priority if explicitly mentioned\n"
    "- If no action items are found, return {\"action_items\": []}\n"
    "- Do NOT invent or infer action items not clearly stated\n"
    "- Do NOT add explanatory text outside the JSON structure\n"
    "- If the transcript is empty or garbled, return {\"action_items\": [], \"error\": \"No valid action items found\"}"
)

PROMPT_GENERATOR_SYSTEM_PROMPT = (
    "You are a prompt engineering expert. "
    "Your task is to convert spoken intent from a transcript into a high-quality, best-practice prompt.\n\n"
    "Create prompts that follow these standards:\n"
    "- Include a clear role that the LLM should assume\n"
    "- Provide relevant context and background\n"
    "- State the task explicitly and specifically\n"
    "- Include explicit constraints and requirements\n"
    "- Define the desired output format precisely\n"
    "- Use clear, unambiguous language\n\n"
    "Output Format:\n"
    "Return the prompt in this exact format:\n\n"
    "---\n"
    "ROLE: [role description]\n\n"
    "CONTEXT: [relevant background and context]\n\n"
    "TASK: [specific task to accomplish]\n\n"
    "CONSTRAINTS:\n"
    "- [constraint 1]\n"
    "- [constraint 2]\n"
    "- [constraint 3]\n\n"
    "DESIRED OUTPUT: [exactly what should be returned, including format]\n"
    "---\n\n"
    "Guidelines:\n"
    "- Base the prompt on the actual intent expressed in the transcript\n"
    "- Include all necessary context from the conversation\n"
    "- Make constraints specific and actionable\n"
    "- Specify output format precisely\n"
    "- Do NOT add assumptions or information not present in the transcript\n"
    "- Do NOT create prompts that are overly vague or ambiguous\n"
    "- If the transcript is empty or unclear, create a general-purpose prompt"
)

CUSTOM_SYSTEM_PROMPT = (
    "You are a text processing assistant. "
    "Apply the user's instruction exactly as provided to the transcript text.\n\n"
    "Guidelines:\n"
    "- Follow the user's instruction precisely\n"
    "- If the instruction is unclear, ask for clarification in your response\n"
    "- Preserve all meaning from the original transcript unless instructed otherwise\n"
    "- Do NOT make assumptions beyond what the user requests"
)


# Prompt templates for each mode
PROMPT_TEMPLATES = {
    RefinementMode.MEETING_NOTES: RefinementModeConfig(
        name="Meeting Notes",
        description="Structured summary with key points, decisions, and topics as clean bullets",
        system_prompt=MEETING_NOTES_SYSTEM_PROMPT,
        user_prompt_template="Here is the meeting transcript:\n\n{transcript}\n\nPlease extract the meeting notes.",
        model="mistral-small-latest",
        temperature=0.3,
        max_tokens=2000,
        output_format="text"
    ),
    
    RefinementMode.CLEAN_TRANSCRIPT: RefinementModeConfig(
        name="Clean Transcript", 
        description="Rewrite the full transcript to read naturally, fixing transcription errors",
        system_prompt=CLEAN_TRANSCRIPT_SYSTEM_PROMPT,
        user_prompt_template="Please clean up this transcript:\n\n{transcript}",
        model="mistral-small-latest", 
        temperature=0.1,
        max_tokens=4000,
        output_format="text"
    ),
    
    RefinementMode.ACTION_ITEMS: RefinementModeConfig(
        name="Action Items",
        description="Extract structured checklist with tasks, owners, and due dates",
        system_prompt=ACTION_ITEMS_SYSTEM_PROMPT,
        user_prompt_template="Extract action items from this transcript:\n\n{transcript}",
        model="mistral-small-latest",
        temperature=0.1,
        max_tokens=1000,
        output_format="json"
    ),
    
    RefinementMode.PROMPT_GENERATOR: RefinementModeConfig(
        name="Prompt Generator",
        description="Create best-practice prompts from transcript intent",
        system_prompt=PROMPT_GENERATOR_SYSTEM_PROMPT,
        user_prompt_template="Convert this spoken intent into a best-practice LLM prompt:\n\n{transcript}",
        model="mistral-small-latest",
        temperature=0.3,
        max_tokens=1500,
        output_format="text"
    ),
    
    RefinementMode.CUSTOM: RefinementModeConfig(
        name="Custom Instruction",
        description="Apply user's own instruction to the transcript",
        system_prompt=CUSTOM_SYSTEM_PROMPT,
        user_prompt_template=None,
        model="mistral-small-latest",
        temperature=0.2,
        max_tokens=2000,
        output_format="text"
    )
}


class RefinementService:
    """Service for refining transcripts using Mistral API.
    
    Implements the registry pattern for modes, allowing easy addition of new
    refinement modes without changing existing code.
    """
    
    def __init__(self, mistral_client: Optional[MistralClientService] = None):
        """Initialize the refinement service.
        
        Args:
            mistral_client: Mistral client service instance. If None, creates one.
        """
        self.mistral_client = mistral_client or get_mistral_client()
        self.mode_registry = self._build_mode_registry()
    
    def _build_mode_registry(self) -> Dict[str, RefinementModeConfig]:
        """Build the mode registry from prompt templates.
        
        Returns:
            Dictionary mapping mode names to configurations
        """
        return {mode.value: config for mode, config in PROMPT_TEMPLATES.items()}
    
    def get_available_modes(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available refinement modes.
        
        Returns:
            Dictionary with mode information (name, description, etc.)
        """
        return {
            mode_id: {
                "name": config.name,
                "description": config.description,
                "model": config.model,
                "temperature": config.temperature,
                "output_format": config.output_format,
                "requires_api_key": True
            }
            for mode_id, config in self.mode_registry.items()
        }
    
    def get_mode_config(self, mode_id: str) -> RefinementModeConfig:
        """Get configuration for a specific mode.
        
        Args:
            mode_id: The mode identifier
            
        Returns:
            RefinementModeConfig for the mode
            
        Raises:
            ValueError: If mode_id is not valid
        """
        if mode_id not in self.mode_registry:
            raise ValueError(f"Unknown refinement mode: {mode_id}. Available: {list(self.mode_registry.keys())}")
        return self.mode_registry[mode_id]
    
    def is_available(self) -> bool:
        """Check if refinement is available (Mistral API key configured).
        
        Returns:
            True if Mistral API can be used, False otherwise
        """
        return self.mistral_client.is_available()
    
    def refine(
        self,
        transcript: str,
        mode_id: str,
        custom_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> RefinementResult:
        """Refine a transcript using the specified mode.
        
        Args:
            transcript: The original transcript text
            mode_id: The refinement mode to use
            custom_instruction: For custom mode, the instruction to apply
            model: Override the default model for this mode
            temperature: Override the default temperature for this mode
            
        Returns:
            RefinementResult with refined text or error information
        """
        try:
            # Validate mode
            if mode_id not in self.mode_registry:
                return RefinementResult(
                    success=False,
                    refined_text="",
                    original_text=transcript,
                    mode=mode_id,
                    error=f"Unknown refinement mode: {mode_id}"
                )
            
            config = self.mode_registry[mode_id]
            
            # Handle empty transcript first (this doesn't require API)
            if not transcript or not transcript.strip():
                return RefinementResult(
                    success=True,
                    refined_text="",
                    original_text=transcript,
                    mode=mode_id,
                    error="Empty transcript provided"
                )
            
            # Check if Mistral is available
            if not self.mistral_client.is_available():
                return RefinementResult(
                    success=False,
                    refined_text="",
                    original_text=transcript,
                    mode=mode_id,
                    error="Mistral API is not configured. Please set MISTRAL_API_KEY environment variable."
                )
            
            # Prepare system prompt
            system_prompt = config.system_prompt
            
            # Prepare user prompt
            if mode_id == RefinementMode.CUSTOM.value:
                if not custom_instruction:
                    return RefinementResult(
                        success=False,
                        refined_text="",
                        original_text=transcript,
                        mode=mode_id,
                        error="Custom mode requires an instruction"
                    )
                user_prompt = f"Instruction: {custom_instruction}\n\nTranscript:\n{transcript}"
            else:
                user_prompt_template = config.user_prompt_template or "{transcript}"
                user_prompt = user_prompt_template.format(transcript=transcript)
            
            # Get final parameters (allow overrides)
            final_model = model or config.model
            final_temperature = temperature if temperature is not None else config.temperature
            final_max_tokens = config.max_tokens
            
            # Call Mistral API
            refined_text = self.mistral_client.refine_text(
                transcript=transcript,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=final_model,
                temperature=final_temperature,
                max_tokens=final_max_tokens
            )
            
            # Handle JSON output format
            if config.output_format == "json":
                try:
                    # Validate and pretty-print JSON
                    parsed = json.loads(refined_text)
                    refined_text = json.dumps(parsed, indent=2)
                except json.JSONDecodeError:
                    # If not valid JSON, return as-is but note in metadata
                    pass
            
            return RefinementResult(
                success=True,
                refined_text=refined_text,
                original_text=transcript,
                mode=mode_id,
                metadata={
                    "model_used": final_model,
                    "temperature_used": final_temperature,
                    "output_format": config.output_format
                }
            )
            
        except MistralAuthenticationError as e:
            return RefinementResult(
                success=False,
                refined_text="",
                original_text=transcript,
                mode=mode_id,
                error=f"Mistral authentication error: {e}"
            )
        except MistralRateLimitError as e:
            return RefinementResult(
                success=False,
                refined_text="",
                original_text=transcript,
                mode=mode_id,
                error=f"Mistral rate limit exceeded: {e}"
            )
        except MistralNetworkError as e:
            return RefinementResult(
                success=False,
                refined_text="",
                original_text=transcript,
                mode=mode_id,
                error=f"Mistral network error: {e}"
            )
        except Exception as e:
            return RefinementResult(
                success=False,
                refined_text="",
                original_text=transcript,
                mode=mode_id,
                error=f"Unexpected error during refinement: {e}"
            )


# Module-level singleton
_refinement_service: Optional[RefinementService] = None


def get_refinement_service() -> RefinementService:
    """Get the singleton refinement service instance.
    
    Returns:
        RefinementService instance
    """
    global _refinement_service
    if _refinement_service is None:
        _refinement_service = RefinementService()
    return _refinement_service


def reset_refinement_service() -> None:
    """Reset the singleton refinement service instance.
    
    Useful for testing.
    """
    global _refinement_service
    _refinement_service = None