#!/usr/bin/env python3
"""
Backend-only verification script for Whisper Transcriber.
Run this from the backend directory after activating the venv.

Usage: 
  cd backend
  venv\\Scripts\\python verify_backend.py
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all backend modules can be imported."""
    print("Testing imports...")
    
    try:
        import main
        import config
        import models
        import services.file_service
        import services.whisper_service
        import services.docx_service
        import services.settings_service
        import services.mistral_client
        import services.refine
        import routers.files
        import routers.transcribe
        import routers.export
        import routers.refine
        print("[OK] All imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from config import BASE_DIR, UPLOADS_DIR, RECORDINGS_DIR, EXPORTS_DIR
        from config import ALLOWED_EXTENSIONS, WHISPER_MODELS, DEFAULT_MODEL
        
        # Ensure directories exist
        for directory in [UPLOADS_DIR, RECORDINGS_DIR, EXPORTS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Check constants
        assert isinstance(ALLOWED_EXTENSIONS, set)
        assert len(WHISPER_MODELS) == 5
        assert DEFAULT_MODEL == "base"
        
        print("[OK] Configuration loading successful")
        return True
    except Exception as e:
        print(f"[FAIL] Configuration test failed: {e}")
        return False


def test_models():
    """Test Pydantic models."""
    print("\nTesting models...")
    
    try:
        from models import FileInfo, TranscriptionSegment, TranscriptionResult, JobStatus, Settings
        
        # Test FileInfo
        file_info = FileInfo(id="test123", name="test.wav", size=1000, type="upload")
        assert file_info.id == "test123"
        assert file_info.has_transcription == False
        
        # Test TranscriptionSegment
        segment = TranscriptionSegment(start=0.0, end=1.0, text="Hello world")
        assert segment.text == "Hello world"
        
        # Test Settings
        settings = Settings(model="small")
        assert settings.model == "small"
        
        print("[OK] All models working correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Model test failed: {e}")
        return False


def test_settings_service():
    """Test settings service functionality."""
    print("\nTesting settings service...")
    
    try:
        from services.settings_service import get_settings, set_settings, get_default_model
        from models import Settings
        
        # Test default settings
        settings = get_settings()
        assert isinstance(settings, Settings)
        assert settings.model in ["tiny", "base", "small", "medium", "large"]
        
        # Test get_default_model
        default_model = get_default_model()
        assert default_model in ["tiny", "base", "small", "medium", "large"]
        
        # Test set_settings
        new_settings = Settings(model="small")
        set_settings(new_settings)
        updated_settings = get_settings()
        assert updated_settings.model == "small"
        
        print("[OK] Settings service working correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Settings service test failed: {e}")
        return False


def test_file_service():
    """Test file service functionality."""
    print("\nTesting file service...")
    
    try:
        from services.file_service import (
            generate_id, save_upload, save_recording, list_files, 
            get_file_path, get_file_info, delete_file
        )
        
        # Test ID generation
        file_id = generate_id()
        assert len(file_id) == 12  # UUID4 hex truncated to 12 chars
        
        # Test save_upload with temp file
        test_content = b"test audio content"
        file_info = save_upload("test.wav", test_content)
        assert file_info.id is not None
        assert file_info.name == "test.wav"
        assert file_info.size == len(test_content)
        assert file_info.type == "upload"
        
        # Test list_files
        files = list_files()
        assert len(files) >= 1  # Should have our test file
        
        # Test get_file_path
        file_path = get_file_path(file_info.id)
        assert file_path is not None
        assert file_path.exists()
        
        # Test get_file_info
        retrieved_info = get_file_info(file_info.id)
        assert retrieved_info is not None
        assert retrieved_info.name == file_info.name
        
        # Test delete_file
        deleted = delete_file(file_info.id)
        assert deleted == True
        
        # Clean up verification
        deleted_again = delete_file(file_info.id)
        assert deleted_again == False  # Should be False since already deleted
        
        print("[OK] File service working correctly")
        return True
    except Exception as e:
        print(f"[FAIL] File service test failed: {e}")
        return False


def test_transcribe_router():
    """Test that transcribe router can be imported and has correct structure."""
    print("\nTesting transcribe router...")
    
    try:
        from routers.transcribe import router, _jobs, _executor, cleanup_completed_jobs
        from fastapi import APIRouter
        
        assert isinstance(router, APIRouter)
        assert router.prefix == "/api/transcribe"
        
        # Test cleanup function
        test_jobs = {"job1": type('JobStatus', (), {"status": "completed"})()}
        cleanup_completed_jobs(test_jobs)
        assert len(test_jobs) == 0
        
        print("[OK] Transcribe router working correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Transcribe router test failed: {e}")
        return False


def test_main_app():
    """Test main application creation."""
    print("\nTesting main application...")
    
    try:
        from main import app
        from fastapi import FastAPI
        
        assert isinstance(app, FastAPI)
        assert app.title == "Transcription API"
        
        # Check that routes are registered
        routes = [route.path for route in app.routes]
        expected_routes = ["/api/files", "/api/transcribe", "/api/export", "/api/refine", "/api/settings", "/api/health"]
        
        for expected in expected_routes:
            found = any(expected in route for route in routes)
            assert found, f"Route {expected} not found in registered routes"
        
        print("[OK] Main application working correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Main application test failed: {e}")
        return False


def test_docx_service():
    """Test DOCX generation service."""
    print("\nTesting DOCX service...")
    
    try:
        from services.docx_service import format_timestamp, generate_docx
        from models import TranscriptionResult, TranscriptionSegment
        from config import EXPORTS_DIR
        
        # Test format_timestamp
        assert format_timestamp(3661) == "01:01:01"  # 1 hour, 1 minute, 1 second
        assert format_timestamp(125) == "02:05"  # 2 minutes, 5 seconds
        
        # Test generate_docx with sample data
        segments = [
            TranscriptionSegment(start=0.0, end=1.0, text="Hello world"),
            TranscriptionSegment(start=1.0, end=2.0, text="This is a test"),
        ]
        result = TranscriptionResult(
            file_id="test123",
            text="Hello world. This is a test",
            segments=segments,
            model="base",
            language="en"
        )
        
        docx_path = generate_docx(result, "test_recording.wav")
        assert docx_path.exists()
        assert docx_path.suffix == ".docx"
        
        # Clean up
        docx_path.unlink()
        
        print("[OK] DOCX service working correctly")
        return True
    except Exception as e:
        print(f"[FAIL] DOCX service test failed: {e}")
        return False


def cleanup_test_files():
    """Clean up any test files created during verification."""
    print("\nCleaning up test files...")
    
    try:
        from config import UPLOADS_DIR, RECORDINGS_DIR, EXPORTS_DIR
        
        # Clean up uploads
        for pattern in ["test*", "*.meta.json", "*.transcription.json"]:
            for file in UPLOADS_DIR.glob(pattern):
                try:
                    file.unlink()
                except:
                    pass
        
        # Clean up recordings
        for pattern in ["test*", "*.meta.json", "*.transcription.json"]:
            for file in RECORDINGS_DIR.glob(pattern):
                try:
                    file.unlink()
                except:
                    pass
        
        # Clean up exports
        for pattern in ["test*", "*.docx"]:
            for file in EXPORTS_DIR.glob(pattern):
                try:
                    file.unlink()
                except:
                    pass
        
        print("[OK] Test file cleanup completed")
    except Exception as e:
        print(f"[WARNING] Cleanup warning: {e}")


def run_all_tests():
    """Run all verification tests."""
    print("=" * 60)
    print("WHISPER TRANSCRIBER BACKEND VERIFICATION")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_models,
        test_settings_service,
        test_file_service,
        test_transcribe_router,
        test_main_app,
        test_docx_service,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Clean up
    cleanup_test_files()
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] All tests passed! Existing features preserved.")
        return True
    else:
        print("[FAIL] Some tests failed. Check the output above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)