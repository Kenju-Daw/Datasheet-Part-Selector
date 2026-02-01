"""
Settings Router - API key management and application configuration

Endpoints:
- GET /settings - Retrieve current settings (masked API keys)
- POST /settings - Save settings
- POST /settings/test-key - Validate an API key
"""
import json
import os
from pathlib import Path
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter()

# Settings file location (in backend directory)
SETTINGS_FILE = Path(__file__).parent.parent / "user_settings.json"


# ============ Schemas ============

class SettingsResponse(BaseModel):
    """Response model for settings (with masked keys)"""
    active_provider: Literal["google", "openrouter"] = "google"
    selected_model: Optional[str] = None  # Selected model ID
    gemini_api_key_configured: bool = False
    openrouter_api_key_configured: bool = False
    gemini_api_key_masked: Optional[str] = None
    openrouter_api_key_masked: Optional[str] = None


class SettingsUpdate(BaseModel):
    """Request model for updating settings"""
    active_provider: Optional[Literal["google", "openrouter"]] = None
    selected_model: Optional[str] = None  # Model ID to use
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    clear_gemini_key: bool = False
    clear_openrouter_key: bool = False


class TestKeyRequest(BaseModel):
    """Request model for testing an API key"""
    provider: Literal["google", "openrouter"]
    api_key: str


class TestKeyResponse(BaseModel):
    """Response model for key test"""
    valid: bool
    message: str


# ============ Helper Functions ============

def load_settings() -> dict:
    """Load settings from JSON file"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_settings(settings: dict) -> None:
    """Save settings to JSON file"""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


def mask_key(key: str) -> str:
    """Mask an API key for display (show first 4 and last 4 chars)"""
    if not key or len(key) < 12:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


# ============ Endpoints ============

@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current settings with masked API keys"""
    settings = load_settings()
    
    gemini_key = settings.get("gemini_api_key", "")
    openrouter_key = settings.get("openrouter_api_key", "")
    
    return SettingsResponse(
        active_provider=settings.get("active_provider", "google"),
        selected_model=settings.get("selected_model"),
        gemini_api_key_configured=bool(gemini_key),
        openrouter_api_key_configured=bool(openrouter_key),
        gemini_api_key_masked=mask_key(gemini_key) if gemini_key else None,
        openrouter_api_key_masked=mask_key(openrouter_key) if openrouter_key else None,
    )


@router.post("", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate):
    """Update settings"""
    settings = load_settings()
    
    # Update provider if specified
    if update.active_provider:
        settings["active_provider"] = update.active_provider
    
    # Update or clear Gemini key
    if update.clear_gemini_key:
        settings.pop("gemini_api_key", None)
    elif update.gemini_api_key:
        settings["gemini_api_key"] = update.gemini_api_key
    
    # Update or clear OpenRouter key
    if update.clear_openrouter_key:
        settings.pop("openrouter_api_key", None)
    elif update.openrouter_api_key:
        settings["openrouter_api_key"] = update.openrouter_api_key
    
    # Update selected model if specified
    if update.selected_model is not None:
        settings["selected_model"] = update.selected_model
    
    # Save to file
    save_settings(settings)
    
    # Return updated settings (masked)
    gemini_key = settings.get("gemini_api_key", "")
    openrouter_key = settings.get("openrouter_api_key", "")
    
    return SettingsResponse(
        active_provider=settings.get("active_provider", "google"),
        selected_model=settings.get("selected_model"),
        gemini_api_key_configured=bool(gemini_key),
        openrouter_api_key_configured=bool(openrouter_key),
        gemini_api_key_masked=mask_key(gemini_key) if gemini_key else None,
        openrouter_api_key_masked=mask_key(openrouter_key) if openrouter_key else None,
    )


@router.post("/test-key", response_model=TestKeyResponse)
async def test_api_key(request: TestKeyRequest):
    """Test if an API key is valid"""
    try:
        if request.provider == "google":
            # Test Google Gemini key by listing models
            import google.generativeai as genai
            genai.configure(api_key=request.api_key)
            # Try to list models first to verify key
            models = list(genai.list_models())
            if models:
                return TestKeyResponse(valid=True, message=f"API key valid! Found {len(models)} models available.")
            else:
                return TestKeyResponse(valid=False, message="Key accepted but no models found")
                
        elif request.provider == "openrouter":
            # Test OpenRouter key using models endpoint
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={
                        "Authorization": f"Bearer {request.api_key}",
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    model_count = len(data.get("data", []))
                    return TestKeyResponse(valid=True, message=f"API key valid! {model_count} models available.")
                elif response.status_code == 401:
                    return TestKeyResponse(valid=False, message="Invalid API key")
                else:
                    return TestKeyResponse(valid=False, message=f"API error: {response.status_code}")
        
    except ImportError as e:
        return TestKeyResponse(valid=False, message=f"Missing dependency: {str(e)}")
    except Exception as e:
        return TestKeyResponse(valid=False, message=f"Error testing key: {str(e)}")
    
    return TestKeyResponse(valid=False, message="Unknown provider")


class ListModelsRequest(BaseModel):
    """Request model for listing models"""
    provider: Literal["google", "openrouter"]
    api_key: Optional[str] = None  # Optional - will use saved key if not provided


class ModelInfo(BaseModel):
    """Model information"""
    id: str
    name: str
    description: Optional[str] = None
    is_free: bool = False
    context_length: Optional[int] = None
    input_cost: Optional[str] = None
    output_cost: Optional[str] = None


class ListModelsResponse(BaseModel):
    """Response model for list models"""
    success: bool
    message: str
    models: list[ModelInfo] = []


@router.post("/list-models", response_model=ListModelsResponse)
async def list_models(request: ListModelsRequest):
    """List available models for a provider"""
    
    # Get API key - use provided or fall back to saved
    api_key = request.api_key
    if not api_key:
        settings = load_settings()
        if request.provider == "google":
            api_key = settings.get("gemini_api_key", "")
        else:
            api_key = settings.get("openrouter_api_key", "")
    
    if not api_key:
        return ListModelsResponse(
            success=False,
            message="No API key provided or saved for this provider",
            models=[]
        )
    
    try:
        if request.provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            models = []
            for model in genai.list_models():
                # Only include models that support generateContent
                if 'generateContent' in model.supported_generation_methods:
                    models.append(ModelInfo(
                        id=model.name,
                        name=model.display_name,
                        description=model.description[:100] if model.description else None,
                        is_free=True,  # Google AI Studio is free tier
                        context_length=getattr(model, 'input_token_limit', None),
                        input_cost="Free (quota limits apply)",
                        output_cost="Free (quota limits apply)",
                    ))
            
            return ListModelsResponse(
                success=True,
                message=f"Found {len(models)} models that support chat",
                models=models
            )
            
        elif request.provider == "openrouter":
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=30.0,
                )
                
                if response.status_code != 200:
                    return ListModelsResponse(
                        success=False,
                        message=f"API error: {response.status_code}",
                        models=[]
                    )
                
                data = response.json()
                models = []
                
                for m in data.get("data", []):
                    pricing = m.get("pricing", {})
                    prompt_cost = float(pricing.get("prompt", 0))
                    completion_cost = float(pricing.get("completion", 0))
                    is_free = prompt_cost == 0 and completion_cost == 0
                    
                    models.append(ModelInfo(
                        id=m.get("id", ""),
                        name=m.get("name", m.get("id", "")),
                        description=m.get("description", "")[:100] if m.get("description") else None,
                        is_free=is_free,
                        context_length=m.get("context_length"),
                        input_cost=f"${prompt_cost}/1K tokens" if prompt_cost > 0 else "FREE",
                        output_cost=f"${completion_cost}/1K tokens" if completion_cost > 0 else "FREE",
                    ))
                
                # Sort: free models first, then by name
                models.sort(key=lambda x: (not x.is_free, x.name))
                
                return ListModelsResponse(
                    success=True,
                    message=f"Found {len(models)} models ({sum(1 for m in models if m.is_free)} free)",
                    models=models
                )
    
    except Exception as e:
        return ListModelsResponse(
            success=False,
            message=f"Error listing models: {str(e)}",
            models=[]
        )

