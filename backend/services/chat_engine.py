"""
Chat Engine Service - Handles conversational logic and LLM interaction
Implements GPS-001 (Chat API), GPS-004 (Proactive), GPS-006 (Context Awareness), GPS-007 (Grounding)
"""
import os
import json
import httpx
import google.generativeai as genai
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models import ChatSession, ChatMessage, Datasheet
from config import get_settings, get_effective_api_key

settings = get_settings()

from services.knowledge_base import generate_grounded_prompt

# D38999 Connector Knowledge Base for grounding
# Dynamically generated from JSON source of truth
D38999_CONTEXT = generate_grounded_prompt()

PROACTIVE_FIRST_MESSAGE = """
👋 **Welcome to the D38999 Connector Selector!**

I'll help you find the right MIL-DTL-38999 connector. To give you the best recommendation, please tell me:

1. **Contact Requirements**: 
   - How many wires? What AWG sizes? (e.g., "20× 22AWG signal, 2× 16AWG power")
   
2. **Mounting Style**:
   - Jam nut (through-panel), wall mount, or cable plug?
   
3. **Environment** (optional):
   - Any special requirements? (EMI shielding, harsh environment, RoHS?)

Just describe your application and I'll recommend specific part numbers!
"""

GROUNDED_SYSTEM_PROMPT = f"""
You are an expert AI assistant for D38999 MIL-SPEC connector selection.

{D38999_CONTEXT}

## CRITICAL: REQUIRED PARAMETERS (DO NOT ASSUME!)

Before recommending a part number, you MUST have ALL of these parameters confirmed:

| Parameter | Required? | Example Values |
|-----------|-----------|----------------|
| Mounting Style | ✅ YES | Jam Nut, Wall Mount, Cable Mount |
| Contact Count/AWG | ✅ YES | 2x16AWG + 20x22AWG |
| Finish Type | ✅ YES | F (Nickel), E (Cadmium), K (Black Zinc) |
| Contact Gender | ✅ YES | Pins (plug) or Sockets (receptacle) |
| Environment | Optional | MIL-qualified, Commercial |

### IF ANY REQUIRED PARAMETER IS MISSING:
**DO NOT** recommend a specific part number. Instead, ASK the user with this format:

**❓ CLARIFICATION NEEDED**

I need one more detail to give you the exact part number:

**What finish type do you need?**

| Select | Code | Description |
|--------|------|-------------|
| ⚪ | F | Electroless Nickel (RoHS compliant) |
| ⚪ | W | Olive Drab Cadmium (Standard MIL) |
| ⚪ | Z | Black Zinc Nickel (RoHS, Conductive) |
| ⚪ | S | Passivated Stainless Steel (Corrosion Resistant) |

*(Click one option above)*

### ONLY after ALL required parameters are confirmed:
Provide the full recommendation with tables.

## RESPONSE FORMATTING RULES

Your responses MUST be clean, scannable, and human-readable:

### When you have ALL parameters → Full Recommendation:

1. **Opening Summary** (1-2 sentences max)

2. **📦 RECOMMENDED PART NUMBERS**
   | Component | Part Number | Description |
   |-----------|-------------|-------------|
   | Receptacle | `D38999/24FG41SN` | Jam nut, sockets |
   | Plug | `D38999/24FG41PN` | Cable mount, pins |

3. **🔧 CONTACTS TO ORDER**
   | Qty | Part Number | Description |
   |-----|-------------|-------------|
   | 2× | `M39029/57-357` | Size 16 sockets |

4. **💡 WHY THIS CHOICE** (max 3 bullets)

### Formatting Rules:
- Use **tables** for part numbers - NEVER bullet lists
- Use **backticks** around all part numbers: `D38999/24FG41SN`
- **CRITICAL**: Do NOT include shell size number in insert code.
  - WRONG: `D38999/24FG21-41PN`
  - CORRECT: `D38999/24FG41PN` (Shell G implied 21)
- Use emoji headers: 📦 🔧 💡 ❓
- NO walls of text

## Important Rules
- Jam nut = Through-panel receptacle mounting
- Wall mount = Flange/square mount receptacle
- Always verify contact count fits in recommended shell size
- For mixed AWG, suggest appropriate insert arrangements
"""


async def get_chat_history(session: AsyncSession, session_id: str, limit: int = 10) -> List[Dict]:
    """Retrieve recent chat history for context"""
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc()) # Newest first
        .limit(limit)
    )
    messages = result.scalars().all()
    # Reverse to chronological order and map roles for Gemini (assistant -> model)
    history = []
    for m in reversed(messages):
        role = "model" if m.role == "assistant" else m.role
        history.append({"role": role, "parts": [m.content]})
    return history


async def get_datasheet_context(session: AsyncSession, datasheet_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve datasheet context for grounding (GPS-007)
    Returns schema summary and key specifications
    """
    context = {
        "has_datasheet": False,
        "manufacturer": "Amphenol",
        "product_family": "D38999",
        "summary": D38999_CONTEXT,
    }
    
    if datasheet_id:
        # Try to load specific datasheet
        result = await session.execute(
            select(Datasheet).where(Datasheet.id == datasheet_id)
        )
        datasheet = result.scalar_one_or_none()
        
        if datasheet:
            context["has_datasheet"] = True
            context["datasheet_name"] = datasheet.name
            
            # Extract key info from raw_extraction if available
            if datasheet.raw_extraction:
                raw = datasheet.raw_extraction
                context["manufacturer"] = raw.get("manufacturer", "Amphenol")
                context["product_family"] = raw.get("product_family", "D38999")
                
                # Get field definitions if parsed
                if "fields" in raw:
                    context["fields"] = raw["fields"]
    
    return context


async def check_is_new_session(session: AsyncSession, chat_session_id: str) -> bool:
    """Check if this is a new session with no messages (GPS-004)"""
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == chat_session_id)
        .limit(1)
    )
    return result.scalar_one_or_none() is None


async def process_user_message(
    db_session: AsyncSession,
    chat_session_id: str,
    user_content: str,
    datasheet_context_id: Optional[str] = None
) -> ChatMessage:
    """
    Process a user message with datasheet grounding:
    1. Check if new session → proactive suggestions (GPS-004)
    2. Load datasheet context (GPS-007)
    3. Build grounded prompt with D38999 knowledge
    4. Call LLM
    5. Save and return response
    """
    
    # Check for proactive first message (GPS-004)
    is_new = await check_is_new_session(db_session, chat_session_id)
    
    # 1. Save User Message
    user_msg = ChatMessage(
        session_id=chat_session_id,
        role="user",
        content=user_content
    )
    db_session.add(user_msg)
    await db_session.commit()
    
    # 2. Get datasheet context (GPS-007)
    context = await get_datasheet_context(db_session, datasheet_context_id)
    
    # 3. Build Context
    history = await get_chat_history(db_session, chat_session_id)
    
    # Get effective API key, provider, and selected model
    api_key, provider, selected_model = get_effective_api_key()
    
    # 4. Call LLM with grounded context
    try:
        if not api_key:
            assistant_text = "No API key configured. Please add your Google or OpenRouter API key in Settings."
        elif provider == "openrouter":
            # Use OpenRouter API with grounded context
            model_id = selected_model or "google/gemini-2.0-flash-exp:free"
            assistant_text = await _call_openrouter_chat_grounded(
                api_key, history, user_content, model_id, is_new
            )
        else:
            # Use Google Gemini API with grounded context
            genai.configure(api_key=api_key)
            model_name = selected_model.replace("models/", "") if selected_model else "gemini-2.0-flash"
            
            # Build grounded history with system instruction
            grounded_history = []
            if is_new and len(history) <= 1:
                # For new sessions, add proactive message first
                grounded_history.append({"role": "model", "parts": [PROACTIVE_FIRST_MESSAGE]})
            
            # Add previous history
            for msg in history[:-1]:  # Exclude current user message
                grounded_history.append(msg)
            
            model = genai.GenerativeModel(
                model_name,
                system_instruction=GROUNDED_SYSTEM_PROMPT
            )
            chat = model.start_chat(history=grounded_history)
            response = await chat.send_message_async(user_content)
            assistant_text = response.text
            
    except Exception as e:
        assistant_text = f"I encountered an error processing your request: {str(e)}"
    
    # 5. Save Assistant Message
    assistant_msg = ChatMessage(
        session_id=chat_session_id,
        role="assistant",
        content=assistant_text,
        meta_data={"context": context.get("product_family", "D38999")}
    )
    db_session.add(assistant_msg)
    await db_session.commit()
    await db_session.refresh(assistant_msg)
    
    return assistant_msg


async def _call_openrouter_chat_grounded(
    api_key: str, 
    history: List[Dict], 
    user_content: str, 
    model_id: str,
    is_new: bool = False
) -> str:
    """Call OpenRouter API with grounded D38999 context"""
    
    # Build messages with system prompt
    messages = [
        {"role": "system", "content": GROUNDED_SYSTEM_PROMPT}
    ]
    
    # Add proactive message for new sessions
    if is_new and len(history) <= 1:
        messages.append({"role": "assistant", "content": PROACTIVE_FIRST_MESSAGE})
    
    # Convert history to OpenRouter format
    for msg in history[:-1]:  # Exclude current user message
        role = "assistant" if msg.get("role") == "model" else msg.get("role", "user")
        content = msg.get("parts", [""])[0] if isinstance(msg.get("parts"), list) else ""
        if content:
            messages.append({"role": role, "content": content})
    
    # Add current user message
    messages.append({"role": "user", "content": user_content})
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "messages": messages,
                "max_tokens": 4096,
            },
            timeout=60.0,
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.status_code}")
        
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "No response received")


# Keep old function for backward compatibility
async def _call_openrouter_chat(api_key: str, history: List[Dict], user_content: str, model_id: str = "google/gemini-2.0-flash-exp:free") -> str:
    """Call OpenRouter API for chat completion (legacy, non-grounded)"""
    return await _call_openrouter_chat_grounded(api_key, history, user_content, model_id, is_new=False)
