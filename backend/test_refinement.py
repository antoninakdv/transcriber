#!/usr/bin/env python3
"""
Test script for Mistral refinement functionality.
This tests the backend refinement services without requiring a Mistral API key.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_refinement_service_without_api_key():
    """Test that refinement service handles missing API key gracefully."""
    print("Testing refinement service without API key...")
    
    try:
        # Make sure MISTRAL_API_KEY is not set
        if 'MISTRAL_API_KEY' in os.environ:
            del os.environ['MISTRAL_API_KEY']
        
        from services.refine import get_refinement_service, RefinementMode
        from services.mistral_client import reset_mistral_client
        
        # Reset to ensure clean state
        reset_mistral_client()
        
        service = get_refinement_service()
        
        # Test that service is not available
        assert not service.is_available(), "Service should not be available without API key"
        
        # Test getting modes (should still work, just not available)
        modes = service.get_available_modes()
        assert len(modes) == 5, f"Expected 5 modes, got {len(modes)}"
        
        # Test refinement without API key
        result = service.refine(
            transcript="This is a test transcript",
            mode_id="clean_transcript"
        )
        
        assert not result.success, "Refinement should fail without API key"
        assert "Mistral API is not configured" in result.error, "Should have API configuration error"
        assert result.original_text == "This is a test transcript", "Original text should be preserved"
        
        # Test with empty transcript
        result = service.refine(
            transcript="",
            mode_id="clean_transcript"
        )
        assert result.success, "Empty transcript should be handled gracefully"
        assert result.refined_text == "", "Empty transcript should return empty string"
        
        print("[OK] Refinement service handles missing API key correctly")
        return True
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_refinement_modes():
    """Test that all refinement modes are properly configured."""
    print("\nTesting refinement mode configuration...")
    
    try:
        from services.refine import get_refinement_service, RefinementMode, PROMPT_TEMPLATES
        
        service = get_refinement_service()
        modes = service.get_available_modes()
        
        expected_modes = [
            "meeting_notes",
            "clean_transcript", 
            "action_items",
            "prompt_generator",
            "custom"
        ]
        
        for mode in expected_modes:
            assert mode in modes, f"Mode {mode} not found in available modes"
        
        # Test that each mode has required properties
        for mode_id, mode_info in modes.items():
            assert 'name' in mode_info, f"Mode {mode_id} missing 'name'"
            assert 'description' in mode_info, f"Mode {mode_id} missing 'description'"
            assert 'model' in mode_info, f"Mode {mode_id} missing 'model'"
            assert 'temperature' in mode_info, f"Mode {mode_id} missing 'temperature'"
            assert 'output_format' in mode_info, f"Mode {mode_id} missing 'output_format'"
        
        # Test getting specific mode config
        config = service.get_mode_config("clean_transcript")
        assert config.name == "Clean Transcript"
        assert config.temperature == 0.1  # Low temperature for fidelity
        assert config.output_format == "text"
        
        # Test invalid mode
        try:
            service.get_mode_config("invalid_mode")
            assert False, "Should have raised ValueError for invalid mode"
        except ValueError:
            pass  # Expected
        
        print("[OK] All refinement modes properly configured")
        return True
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_engineering_standards():
    """Test that prompts follow the required standards."""
    print("\nTesting prompt engineering standards...")
    
    try:
        from services.refine import (
            MEETING_NOTES_SYSTEM_PROMPT,
            CLEAN_TRANSCRIPT_SYSTEM_PROMPT,
            ACTION_ITEMS_SYSTEM_PROMPT,
            PROMPT_GENERATOR_SYSTEM_PROMPT,
            CUSTOM_SYSTEM_PROMPT
        )
        
        # Test system/user separation - all prompts should be system-level
        prompts = [
            MEETING_NOTES_SYSTEM_PROMPT,
            CLEAN_TRANSCRIPT_SYSTEM_PROMPT,
            ACTION_ITEMS_SYSTEM_PROMPT,
            PROMPT_GENERATOR_SYSTEM_PROMPT,
            CUSTOM_SYSTEM_PROMPT
        ]
        
        for prompt in prompts:
            assert isinstance(prompt, str), "Prompt should be a string"
            assert len(prompt) > 0, "Prompt should not be empty"
        
        # Test specific requirements
        # 1. Clean transcript should have few-shot example
        assert "Example:" in CLEAN_TRANSCRIPT_SYSTEM_PROMPT, "Clean transcript should have example"
        assert "Before:" in CLEAN_TRANSCRIPT_SYSTEM_PROMPT, "Clean transcript should have before example"
        assert "After:" in CLEAN_TRANSCRIPT_SYSTEM_PROMPT, "Clean transcript should have after example"
        
        # 2. Action items should specify JSON output
        assert "JSON" in ACTION_ITEMS_SYSTEM_PROMPT, "Action items should specify JSON output"
        assert "action_items" in ACTION_ITEMS_SYSTEM_PROMPT, "Action items should mention action_items"
        
        # 3. All should have explicit instructions about what NOT to do
        for prompt in prompts:
            prompt_lower = prompt.lower()
            assert "do not" in prompt_lower or "don't" in prompt_lower, \
                f"Prompt should have explicit 'do not' instructions: {prompt[:100]}..."
        
        print("[OK] Prompt engineering standards verified")
        return True
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mistral_client_without_key():
    """Test Mistral client behavior without API key."""
    print("\nTesting Mistral client without API key...")
    
    try:
        # Ensure no API key is set
        if 'MISTRAL_API_KEY' in os.environ:
            del os.environ['MISTRAL_API_KEY']
        
        from services.mistral_client import MistralClientService, reset_mistral_client
        
        reset_mistral_client()
        
        client = MistralClientService()
        
        # Should not be available
        assert not client.is_available(), "Client should not be available without API key"
        
        # Test refine_text raises authentication error
        from services.mistral_client import MistralAuthenticationError
        
        try:
            client.refine_text("test", "system", "user")
            assert False, "Should have raised authentication error"
        except MistralAuthenticationError as e:
            assert "MISTRAL_API_KEY" in str(e), "Error should mention API key"
        
        # Test with empty transcript
        # This should be handled before reaching the API
        try:
            client.refine_text("", "system", "user")
            # Should return empty string for empty input
        except MistralAuthenticationError:
            # This is also acceptable - the empty check happens before API call
            pass
        
        print("[OK] Mistral client handles missing API key correctly")
        return True
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_refinement_router():
    """Test that refinement router can be imported and has correct structure."""
    print("\nTesting refinement router...")
    
    try:
        from routers.refine import router
        from fastapi import APIRouter
        
        assert isinstance(router, APIRouter)
        assert router.prefix == "/api/refine"
        
        # Check that router has the expected endpoints
        routes = [route.path for route in router.routes]
        expected_routes = ["/modes", "/available", "/{file_id}", "/text"]
        
        for expected in expected_routes:
            # The actual paths will have the prefix, so we need to check differently
            found = any(expected.replace("{file_id}", "") in route for route in routes)
            assert found, f"Route pattern {expected} not found in {routes}"
        
        print("[OK] Refinement router configured correctly")
        return True
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_docx_export_refined():
    """Test DOCX export with refined text."""
    print("\nTesting DOCX export with refined text...")
    
    try:
        from services.docx_service import generate_docx
        from models import TranscriptionResult, TranscriptionSegment
        from config import EXPORTS_DIR
        
        # Create sample transcription result
        segments = [TranscriptionSegment(start=0.0, end=1.0, text="Hello world")]
        result = TranscriptionResult(
            file_id="test123",
            text="Hello world",
            segments=segments,
            model="base",
            language="en"
        )
        
        # Test export with refined text
        refined_text = "This is the refined version of the transcript."
        docx_path = generate_docx(result, "test.wav", refined_text, "clean_transcript")
        
        assert docx_path.exists(), "DOCX file should be created"
        assert "clean_transcript" in docx_path.name, "Filename should include refinement mode"
        
        # Clean up
        docx_path.unlink()
        
        # Test export without refined text (original behavior)
        docx_path2 = generate_docx(result, "test2.wav")
        assert docx_path2.exists(), "DOCX file should be created for original"
        
        # Clean up
        docx_path2.unlink()
        
        print("[OK] DOCX export with refined text working")
        return True
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all refinement tests."""
    print("=" * 60)
    print("MISTRAL REFINEMENT BACKEND TESTS")
    print("=" * 60)
    
    tests = [
        test_refinement_service_without_api_key,
        test_refinement_modes,
        test_prompt_engineering_standards,
        test_mistral_client_without_key,
        test_refinement_router,
        test_docx_export_refined,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("REFINEMENT TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] All refinement tests passed!")
        return True
    else:
        print("[FAIL] Some refinement tests failed.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)