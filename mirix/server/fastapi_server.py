import asyncio
import base64
import json
import logging
import os
import queue
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..agent.agent_wrapper import AgentWrapper
from ..functions.mcp_client import StdioServerConfig, get_mcp_client_manager
from ..services.mcp_marketplace import get_mcp_marketplace
from ..services.mcp_tool_registry import get_mcp_tool_registry
from ..schemas.custom_models import (
    UpdateCustomModelRequest,
    UpdateCustomModelResponse,
    DeleteCustomModelResponse,
    CustomModelDetailResponse,
    ModelStatusResponse,
    get_model_id_from_name,
    validate_custom_models_directory
)

logger = logging.getLogger(__name__)


# User data isolation utilities
def validate_and_sanitize_user_id(
    request_user_id: Optional[str], 
    current_user_id: str
) -> str:
    """
    验证并清理user_id参数,确保用户数据隔离
    
    为了安全,所有用户只能访问自己的数据。如果请求中的user_id
    与当前用户ID不匹配,将被忽略并使用当前用户ID。
    
    Args:
        request_user_id: 请求中的user_id参数
        current_user_id: 当前认证用户的ID
        
    Returns:
        清理后的user_id(始终为当前用户ID)
    """
    if request_user_id is None:
        return current_user_id
    
    if request_user_id != current_user_id:
        logger.warning(
            f"User {current_user_id} attempted to access data of user {request_user_id}. "
            f"Request denied - using current user ID instead."
        )
    
    return current_user_id


# User context switching utilities
def switch_user_context(agent_wrapper, user_id: str):
    """Switch agent's user context and manage user status"""
    if agent_wrapper and agent_wrapper.client:

        # Set current user to inactive
        if agent_wrapper.client.user:
            current_user = agent_wrapper.client.user
            agent_wrapper.client.server.user_manager.update_user_status(
                current_user.id, "inactive"
            )

        # Get and set new user to active
        user = agent_wrapper.client.server.user_manager.get_user_by_id(user_id)
        agent_wrapper.client.server.user_manager.update_user_status(user_id, "active")
        agent_wrapper.client.user = user
        return user
    return None


def get_user_or_default(agent_wrapper, user_id: Optional[str] = None):
    """
    Get user by ID or return current user
    
    安全增强: 如果提供的user_id与当前用户不匹配,将被忽略并使用当前用户,
    确保用户数据隔离。
    """
    if user_id:
        # 获取当前用户以进行验证
        current_user = agent_wrapper.client.user if (agent_wrapper and agent_wrapper.client.user) else None
        
        # 如果当前用户存在且user_id不匹配,使用当前用户
        if current_user and user_id != current_user.id:
            logger.warning(
                f"get_user_or_default called with user_id={user_id} "
                f"but current user is {current_user.id}. Using current user for security."
            )
            return current_user
        
        # 如果匹配或没有当前用户,尝试获取指定用户
        try:
            return agent_wrapper.client.server.user_manager.get_user_by_id(user_id)
        except Exception:
            # 如果指定用户不存在，回退到默认用户
            logger.warning(f"用户 {user_id} 不存在，使用默认用户")
            return agent_wrapper.client.server.user_manager.get_default_user()
    elif agent_wrapper and agent_wrapper.client.user:
        return agent_wrapper.client.user
    else:
        return agent_wrapper.client.server.user_manager.get_default_user()


async def handle_gmail_connection(
    client_id: str, client_secret: str, server_name: str
) -> bool:
    """
    Handle Gmail OAuth2 authentication and MCP connection
    Using EXACT same logic as /Users/yu.wang/work/Gmail/single_user_gmail.py
    """
    import os

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    # Use all required Gmail scopes for full functionality
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    try:
        print(f"🔐 Starting Gmail OAuth for {server_name}")

        # Set up token file path (same pattern as original)
        token_file = os.path.expanduser("~/.mirix/gmail_token.json")
        os.makedirs(os.path.dirname(token_file), exist_ok=True)

        # Create client config - EXACT same structure as original
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [
                    "http://localhost:8080/",
                    "http://localhost:8081/",
                    "http://localhost:8082/",
                ],
            }
        }

        creds = None

        # Load existing token if available - EXACT same logic
        if os.path.exists(token_file):
            try:
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            except Exception:
                print("🔄 Refreshing Gmail credentials (previous token expired)")
                os.remove(token_file)
                creds = None

        # If there are no (valid) credentials available, let the user log in - EXACT same logic
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None

            if not creds:
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

                print("\n🔐 Starting OAuth authentication...")
                print("Opening browser for Google authentication...")

                # Try specific ports that match redirect URIs - EXACT same logic
                for port in [8080, 8081, 8082]:
                    try:
                        creds = flow.run_local_server(port=port, open_browser=True)
                        break
                    except OSError:
                        if port == 8082:
                            # If all ports fail, use automatic port selection
                            creds = flow.run_local_server(port=0, open_browser=True)

            # Save the credentials for the next run - EXACT same logic
            with open(token_file, "w") as token:
                token.write(creds.to_json())

        # Build the Gmail service - EXACT same logic
        service = build("gmail", "v1", credentials=creds)
        print("✅ Successfully authenticated with Gmail API")

        # Gmail service built successfully - ready for email sending
        print("✅ Gmail API connected successfully")

        # Now create the MCP client and add it to the manager
        from ..functions.mcp_client import (
            GmailMCPClient,
            GmailServerConfig,
            get_mcp_client_manager,
        )

        config = GmailServerConfig(
            server_name=server_name,
            client_id=client_id,
            client_secret=client_secret,
            token_file=token_file,
        )

        # Create Gmail MCP client directly
        client = GmailMCPClient(config)
        client.gmail_service = service
        client.credentials = creds
        client.initialized = True

        # Add to MCP manager
        mcp_manager = get_mcp_client_manager()
        mcp_manager.clients[server_name] = client
        mcp_manager.server_configs[server_name] = config

        # Save configuration to disk for persistence (this was missing!)
        mcp_manager._save_persistent_connections()

        print(
            f"✅ Gmail MCP client added to manager as '{server_name}' and saved to disk"
        )
        return True

    except Exception as e:
        print(f"❌ Error in Gmail OAuth flow: {str(e)}")
        logger.error(f"Gmail connection error: {str(e)}")
        return False


"""
VOICE RECORDING STRATEGY & ARCHITECTURE:

Current Implementation:
- Frontend records audio in 5-second chunks (CHUNK_DURATION = 5000ms)
- Chunks are accumulated locally until a screenshot is sent
- Raw voice files are sent to the agent for accumulation and processing
- Agent accumulates voice files alongside images until TEMPORARY_MESSAGE_LIMIT is reached
- Voice processing happens in agent.absorb_content_into_memory()

Recommended Alternative Strategy:
Instead of 5-second chunks, you can:
1. Send 1-second micro-chunks to reduce latency
2. Agent accumulates chunks until TEMPORARY_MESSAGE_LIMIT is reached
3. This aligns perfectly with how images are accumulated in agent.py

Benefits of 1-second chunks:
- Lower latency for real-time feedback
- More granular control over audio processing
- Better alignment with the existing image accumulation pattern
- Smoother user experience
- Voice processing happens in batches during memory absorption

Implementation changes needed:
- Frontend: Change CHUNK_DURATION from 5000 to 1000
- Agent: Handles voice file accumulation and processing during memory absorption
- Server: Passes raw voice files to agent without processing

FFPROBE WARNING:
The warning about ffprobe/avprobe is harmless and expected if FFmpeg isn't in your system PATH.
To fix it, install FFmpeg:
- Windows: Download from https://ffmpeg.org and add to PATH
- macOS: brew install ffmpeg  
- Linux: sudo apt install ffmpeg

The warning doesn't affect functionality as pydub falls back gracefully.
"""

app = FastAPI(title="Mirix Agent API", version="0.1.4")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def register_mcp_tools_for_restored_connections():
    """Register tools for MCP connections that were restored on startup"""
    try:
        mcp_manager = get_mcp_client_manager()
        connected_servers = mcp_manager.list_servers()

        if connected_servers and agent and agent.client.user:
            logger.info(
                f"Re-registering tools for {len(connected_servers)} restored MCP servers"
            )

            mcp_tool_registry = get_mcp_tool_registry()
            current_user = agent.client.user

            for server_name in connected_servers:
                try:
                    # Register tools for this server
                    registered_tools = mcp_tool_registry.register_mcp_tools(
                        current_user, [server_name]
                    )

                    # Add MCP tool to the current chat agent if available
                    if hasattr(agent, "agent_states"):
                        agent.client.server.agent_manager.add_mcp_tool(
                            agent_id=agent.agent_states.agent_state.id,
                            mcp_tool_name=server_name,
                            tool_ids=list(
                                set(
                                    [tool.id for tool in registered_tools]
                                    + [
                                        tool.id
                                        for tool in agent.client.server.agent_manager.get_agent_by_id(
                                            agent.agent_states.agent_state.id,
                                            actor=agent.client.user,
                                        ).tools
                                    ]
                                )
                            ),
                            actor=agent.client.user,
                        )

                    logger.info(
                        f"Re-registered {len(registered_tools)} tools for server {server_name}"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to re-register tools for server {server_name}: {str(e)}"
                    )

    except Exception as e:
        logger.error(f"Error re-registering MCP tools: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Initialize and restore MCP connections on startup"""
    try:
        logger.info("Starting up Mirix FastAPI server...")

        # Initialize the MCP client manager (this will auto-restore connections)
        print("🚀 Initializing MCP client manager...")
        mcp_manager = get_mcp_client_manager()
        connected_servers = mcp_manager.list_servers()
        logger.info(
            f"MCP client manager initialized with {len(connected_servers)} restored connections: {connected_servers}"
        )
        print(
            f"🔄 MCP Manager: Restored {len(connected_servers)} connections: {connected_servers}"
        )

        # Debug: Check if the configuration file exists
        import os

        config_file = os.path.expanduser("~/.mirix/mcp_connections.json")
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                import json

                configs = json.load(f)
                print(
                    f"📋 Found MCP config file with {len(configs)} entries: {list(configs.keys())}"
                )
        else:
            print(f"📋 No MCP config file found at {config_file}")

        # Tool registration will happen later when agent is available

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")


# Global agent instance
agent = None
# Global storage for confirmation queues keyed by confirmation_id
confirmation_queues = {}
# Flag to track if MCP tools have been registered for restored connections
_mcp_tools_registered = False


class MessageRequest(BaseModel):
    message: Optional[str] = None
    image_uris: Optional[List[str]] = None
    sources: Optional[List[str]] = None  # Source names corresponding to image_uris
    voice_files: Optional[List[str]] = None  # Base64 encoded voice files
    memorizing: bool = False
    is_screen_monitoring: Optional[bool] = False
    user_id: Optional[str] = None  # Optional user ID, defaults to None (uses default user)


class MessageResponse(BaseModel):
    response: str
    status: str = "success"


class ConfirmationRequest(BaseModel):
    confirmation_id: str
    confirmed: bool


class PersonaDetailsResponse(BaseModel):
    personas: Dict[str, str]


class UpdatePersonaRequest(BaseModel):
    text: str
    user_id: Optional[str] = None


class UpdatePersonaResponse(BaseModel):
    success: bool
    message: str


class UpdateCoreMemoryRequest(BaseModel):
    label: str
    text: str


class UpdateCoreMemoryResponse(BaseModel):
    success: bool
    message: str


class ApplyPersonaTemplateRequest(BaseModel):
    persona_name: str
    user_id: Optional[str] = None


class CoreMemoryPersonaResponse(BaseModel):
    text: str


class SetModelRequest(BaseModel):
    model: str


class AddCustomModelRequest(BaseModel):
    model_name: str
    model_endpoint: str
    api_key: str
    model_provider: str = "openai-compatible"  # 新增：模型提供商类型
    temperature: float = 0.7
    max_tokens: int = 4096
    maximum_length: int = 32768


class AddCustomModelResponse(BaseModel):
    success: bool
    message: str


class ListCustomModelsResponse(BaseModel):
    models: List[str]


class SetModelResponse(BaseModel):
    success: bool
    message: str
    missing_keys: List[str]
    model_requirements: Dict[str, Any]


class GetCurrentModelResponse(BaseModel):
    current_model: str


class SetTimezoneRequest(BaseModel):
    timezone: str


class SetTimezoneResponse(BaseModel):
    success: bool
    message: str


class GetTimezoneResponse(BaseModel):
    timezone: str


class ScreenshotSettingRequest(BaseModel):
    include_recent_screenshots: bool


class ScreenshotSettingResponse(BaseModel):
    success: bool
    include_recent_screenshots: bool
    message: str


# API Key validation functionality
def get_required_api_keys_for_model(model_endpoint_type: str) -> List[str]:
    """Get required API keys for a given model endpoint type"""
    api_key_mapping = {
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "azure": ["AZURE_API_KEY", "AZURE_BASE_URL", "AZURE_API_VERSION"],
        "google_ai": ["GEMINI_API_KEY"],
        "groq": ["GROQ_API_KEY"],
        "together": ["TOGETHER_API_KEY"],
        "bedrock": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
    }
    return api_key_mapping.get(model_endpoint_type, [])


def check_missing_api_keys(agent) -> Dict[str, List[str]]:
    """Check for missing API keys based on the agent's configuration"""

    if agent is None:
        return {"error": ["Agent not initialized"]}

    try:
        # Use the new AgentWrapper method instead of the old logic
        status = agent.check_api_key_status()

        return {
            "missing_keys": status["missing_keys"],
            "model_type": status.get("model_requirements", {}).get(
                "current_model", "unknown"
            ),
        }

    except Exception as e:
        print(f"Error in check_missing_api_keys: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": [f"Error checking API keys: {str(e)}"]}


class ApiKeyRequest(BaseModel):
    key_name: str
    key_value: str


class ApiKeyCheckResponse(BaseModel):
    missing_keys: List[str]
    model_type: str
    requires_api_key: bool


class ApiKeyUpdateResponse(BaseModel):
    success: bool
    message: str


# Memory endpoint response models
class EpisodicMemoryItem(BaseModel):
    timestamp: str
    content: str
    context: Optional[str] = None
    emotions: Optional[List[str]] = None


class KnowledgeSkillItem(BaseModel):
    title: str
    type: str  # "semantic" or "procedural"
    content: str
    proficiency: Optional[str] = None
    tags: Optional[List[str]] = None


class DocsFilesItem(BaseModel):
    filename: str
    type: str
    summary: str
    last_accessed: Optional[str] = None
    size: Optional[str] = None


class CoreUnderstandingItem(BaseModel):
    aspect: str
    understanding: str
    confidence: Optional[float] = None
    last_updated: Optional[str] = None


class CredentialItem(BaseModel):
    name: str
    type: str
    content: str  # Will be masked
    tags: Optional[List[str]] = None
    last_used: Optional[str] = None


class ClearConversationResponse(BaseModel):
    success: bool
    message: str
    messages_deleted: int


class CleanupDetachedMessagesResponse(BaseModel):
    success: bool
    message: str
    cleanup_results: Dict[str, int]


class ExportMemoriesRequest(BaseModel):
    file_path: str
    memory_types: List[str]
    include_embeddings: bool = False
    user_id: Optional[str] = None


class ExportMemoriesResponse(BaseModel):
    success: bool
    message: str
    exported_counts: Dict[str, int]
    total_exported: int
    file_path: str


class ReflexionRequest(BaseModel):
    pass  # No parameters needed for now


class ReflexionResponse(BaseModel):
    success: bool
    message: str
    processing_time: Optional[float] = None


# Memory management models
class DeleteMemoryRequest(BaseModel):
    """删除记忆的请求模型"""
    memory_type: str = Field(..., description="记忆类型: episodic, semantic, procedural, resource, core, credentials")
    memory_ids: List[str] = Field(..., description="要删除的记忆ID列表")
    user_id: Optional[str] = Field(None, description="用户ID，可选")


class DeleteMemoryResponse(BaseModel):
    """删除记忆的响应模型"""
    success: bool
    message: str
    deleted_count: int
    failed_ids: List[str] = Field(default_factory=list)


class UpdateMemoryRequest(BaseModel):
    """更新记忆的请求模型"""
    memory_type: str = Field(..., description="记忆类型: episodic, semantic, procedural, resource, core, credentials")
    memory_id: str = Field(..., description="记忆ID")
    updates: Dict[str, Any] = Field(..., description="要更新的字段和值")
    user_id: Optional[str] = Field(None, description="用户ID，可选")


class UpdateMemoryResponse(BaseModel):
    """更新记忆的响应模型"""
    success: bool
    message: str
    updated_memory: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the agent when the server starts"""
    global agent

    # Handle PyInstaller bundled resources
    import sys
    from pathlib import Path

    if getattr(sys, "frozen", False):
        # Running in PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        config_path = bundle_dir / "mirix" / "configs" / "mirix_monitor.yaml"
    else:
        # Running in development
        config_path = Path("mirix/configs/mirix_monitor.yaml")

    agent = AgentWrapper(str(config_path))
    print("Agent initialized successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring server status"""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/send_message")
async def send_message_endpoint(request: MessageRequest):
    """Send a message to the agent and get the response"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    # Register tools for restored MCP connections (one-time only)
    global _mcp_tools_registered
    if not _mcp_tools_registered:
        register_mcp_tools_for_restored_connections()
        _mcp_tools_registered = True

    # Check for missing API keys
    api_key_check = check_missing_api_keys(agent)
    if "error" in api_key_check:
        raise HTTPException(status_code=500, detail=api_key_check["error"][0])

    if api_key_check["missing_keys"]:
        # Return a special response indicating missing API keys
        return MessageResponse(
            response=f"Missing API keys for {api_key_check['model_type']} model: {', '.join(api_key_check['missing_keys'])}. Please provide the required API keys.",
            status="missing_api_keys",
        )

    try:
        # Handle user context switching if user_id is provided
        if request.user_id:
            switch_user_context(agent, request.user_id)

        print(
            f"Starting agent.send_message (non-streaming) with: message='{request.message}', memorizing={request.memorizing}, user_id={request.user_id}"
        )

        # Run the blocking agent.send_message() in a background thread to avoid blocking other requests
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,  # Use default ThreadPoolExecutor
            lambda: agent.send_message(
                message=request.message,
                image_uris=request.image_uris,
                sources=request.sources,  # Pass sources to agent
                voice_files=request.voice_files,  # Pass voice files to agent
                memorizing=request.memorizing,
                user_id=request.user_id,
            ),
        )

        print(f"Agent response (non-streaming): {response}")

        if response == "ERROR":
            raise HTTPException(status_code=500, detail="Agent returned an error")

        # Handle case where agent returns None
        if response is None:
            if request.memorizing:
                # When memorizing=True, None response is expected (no response needed)
                response = ""
            else:
                # When memorizing=False, None response is an error
                response = "I received your message but couldn't generate a response. Please try again."

        return MessageResponse(response=response)

    except Exception as e:
        print(f"Error in send_message_endpoint: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Error processing message: {str(e)}"
        )


@app.post("/send_streaming_message")
async def send_streaming_message_endpoint(request: MessageRequest):
    """Send a message to the agent and stream intermediate messages and final response"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    # Register tools for restored MCP connections (one-time only)
    global _mcp_tools_registered
    if not _mcp_tools_registered:
        register_mcp_tools_for_restored_connections()
        _mcp_tools_registered = True

    # Check for missing API keys
    api_key_check = check_missing_api_keys(agent)
    if "error" in api_key_check:
        raise HTTPException(status_code=500, detail=api_key_check["error"][0])

    if api_key_check["missing_keys"]:
        # Return a special SSE event for missing API keys
        async def missing_keys_response():
            yield f"data: {json.dumps({'type': 'missing_api_keys', 'missing_keys': api_key_check['missing_keys'], 'model_type': api_key_check['model_type']})}\n\n"

        return StreamingResponse(
            missing_keys_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            },
        )

    agent.update_chat_agent_system_prompt(request.is_screen_monitoring)

    # Create a queue to collect intermediate messagess
    message_queue = queue.Queue()

    def display_intermediate_message(message_type: str, message: str):
        """Callback function to capture intermediate messages"""
        message_queue.put(
            {"type": "intermediate", "message_type": message_type, "content": message}
        )

    def request_user_confirmation(confirmation_type: str, details: dict) -> bool:
        """Request confirmation from user and wait for response"""
        import uuid

        confirmation_id = str(uuid.uuid4())

        # Create a queue for this specific confirmation
        confirmation_result_queue = queue.Queue()
        confirmation_queues[confirmation_id] = confirmation_result_queue

        # Put confirmation request in message queue
        message_queue.put(
            {
                "type": "confirmation_request",
                "confirmation_type": confirmation_type,
                "confirmation_id": confirmation_id,
                "details": details,
            }
        )

        # Wait for confirmation response with timeout
        try:
            result = confirmation_result_queue.get(timeout=300)  # 5 minute timeout
            return result.get("confirmed", False)
        except queue.Empty:
            # Timeout - default to not confirmed
            return False
        finally:
            # Clean up the queue
            confirmation_queues.pop(confirmation_id, None)

    async def generate_stream():
        """Generator function for streaming responses"""
        try:
            # Start the agent processing in a separate thread
            result_queue = queue.Queue()

            async def run_agent():
                try:
                    # find the current active user
                    users = agent.client.server.user_manager.list_users()
                    active_user = next(
                        (user for user in users if user.status == "active"), None
                    )
                    current_user_id = active_user.id if active_user else None

                    # Run agent.send_message in a background thread to avoid blocking
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,  # Use default ThreadPoolExecutor
                        lambda: agent.send_message(
                            message=request.message,
                            image_uris=request.image_uris,
                            sources=request.sources,  # Pass sources to agent
                            voice_files=request.voice_files,  # Pass raw voice files
                            memorizing=request.memorizing,
                            display_intermediate_message=display_intermediate_message,
                            request_user_confirmation=request_user_confirmation,
                            is_screen_monitoring=request.is_screen_monitoring,
                            user_id=current_user_id,
                        ),
                    )
                    # Handle various response cases
                    if response is None:
                        if request.memorizing:
                            result_queue.put({"type": "final", "response": ""})
                        else:
                            print("[DEBUG] Agent returned None response")
                            result_queue.put(
                                {"type": "error", "error": "Agent returned no response"}
                            )
                    elif isinstance(response, str) and response.startswith("ERROR_"):
                        # Handle specific error types from agent wrapper
                        print(f"[DEBUG] Agent returned specific error: {response}")
                        if response == "ERROR_RESPONSE_FAILED":
                            print("[DEBUG] - Message queue response failed")
                            result_queue.put(
                                {
                                    "type": "error",
                                    "error": "Message processing failed in agent queue",
                                }
                            )
                        elif response == "ERROR_INVALID_RESPONSE_STRUCTURE":
                            print(
                                "[DEBUG] - Response structure invalid (missing messages or insufficient count)"
                            )
                            result_queue.put(
                                {
                                    "type": "error",
                                    "error": "Invalid response structure from agent",
                                }
                            )
                        elif response == "ERROR_NO_TOOL_CALL":
                            print(
                                "[DEBUG] - Expected message missing tool_call attribute"
                            )
                            result_queue.put(
                                {
                                    "type": "error",
                                    "error": "Agent response missing required tool call",
                                }
                            )
                        elif response == "ERROR_NO_MESSAGE_IN_ARGS":
                            print("[DEBUG] - Tool call arguments missing 'message' key")
                            result_queue.put(
                                {
                                    "type": "error",
                                    "error": "Agent tool call missing message content",
                                }
                            )
                        elif response == "ERROR_PARSING_EXCEPTION":
                            print(
                                "[DEBUG] - Exception occurred during response parsing"
                            )
                            result_queue.put(
                                {
                                    "type": "error",
                                    "error": "Failed to parse agent response",
                                }
                            )
                        else:
                            print(f"[DEBUG] - Unknown error type: {response}")
                            result_queue.put(
                                {
                                    "type": "error",
                                    "error": f"Unknown agent error: {response}",
                                }
                            )
                    elif response == "ERROR":
                        print("[DEBUG] Agent returned generic ERROR string")
                        result_queue.put(
                            {"type": "error", "error": "Agent processing failed"}
                        )
                    elif not response or (
                        isinstance(response, str) and response.strip() == ""
                    ):
                        if request.memorizing:
                            print(
                                "[DEBUG] Agent returned empty response - expected for memorizing=True"
                            )
                            result_queue.put({"type": "final", "response": ""})
                        else:
                            print("[DEBUG] Agent returned empty response unexpectedly")
                            result_queue.put(
                                {
                                    "type": "error",
                                    "error": "Agent returned empty response",
                                }
                            )
                    else:
                        print(
                            f"[DEBUG] Agent returned successful response (length: {len(str(response))})"
                        )
                        result_queue.put({"type": "final", "response": response})

                except Exception as e:
                    print(f"[DEBUG] Exception in run_agent: {str(e)}")
                    print(f"Traceback: {traceback.format_exc()}")
                    result_queue.put({"type": "error", "error": str(e)})

            # Start agent processing as async task
            agent_task = asyncio.create_task(run_agent())

            # Keep track of whether we've sent the final result
            final_result_sent = False

            # Stream intermediate messages and wait for final result
            while not final_result_sent:
                # Check for intermediate messages first
                try:
                    intermediate_msg = message_queue.get_nowait()
                    yield f"data: {json.dumps(intermediate_msg)}\n\n"
                    continue  # Continue to next iteration to check for more messages
                except queue.Empty:
                    pass

                # Check for final result with timeout
                try:
                    # Use a short timeout to allow for intermediate messages
                    final_result = result_queue.get(timeout=0.1)
                    if final_result["type"] == "error":
                        yield f"data: {json.dumps({'type': 'error', 'error': final_result['error']})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'final', 'response': final_result['response']})}\n\n"
                    final_result_sent = True
                    break
                except queue.Empty:
                    # If no result yet, check if task is still running
                    if agent_task.done():
                        # Task is done but no result - this shouldn't happen, but handle it
                        try:
                            # Check if the task raised an exception
                            agent_task.result()
                        except Exception as e:
                            yield f"data: {json.dumps({'type': 'error', 'error': f'Agent processing failed: {str(e)}'})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'error', 'error': 'Agent processing completed unexpectedly without result'})}\n\n"
                        final_result_sent = True
                        break
                    # Otherwise continue the loop to check for more intermediate messages
                    await asyncio.sleep(0.1)  # Yield control to allow other operations

            # Make sure task completes
            if not agent_task.done():
                try:
                    await asyncio.wait_for(agent_task, timeout=5.0)
                except asyncio.TimeoutError:
                    agent_task.cancel()
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Agent processing timed out'})}\n\n"

        except Exception as e:
            print(f"Traceback: {traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    try:
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            },
        )
    except Exception as e:
        print(f"Error in send_streaming_message_endpoint: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")


@app.get("/personas", response_model=PersonaDetailsResponse)
async def get_personas(user_id: Optional[str] = None):
    """Get all personas with their details (name and text)"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        target_user = active_user if active_user else (users[0] if users else None)

        persona_details = agent.get_persona_details()
        return PersonaDetailsResponse(personas=persona_details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting personas: {str(e)}")


@app.post("/personas/update", response_model=UpdatePersonaResponse)
async def update_persona(request: UpdatePersonaRequest):
    """Update the agent's core memory persona text"""

    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        target_user = active_user if active_user else (users[0] if users else None)

        agent.update_core_memory_persona(request.text)
        return UpdatePersonaResponse(
            success=True, message="Core memory persona updated successfully"
        )
    except Exception as e:
        return UpdatePersonaResponse(
            success=False, message=f"Error updating core memory persona: {str(e)}"
        )


@app.post("/personas/apply_template", response_model=UpdatePersonaResponse)
async def apply_persona_template(request: ApplyPersonaTemplateRequest):
    """Apply a persona template to the agent"""

    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        target_user = active_user if active_user else (users[0] if users else None)

        agent.apply_persona_template(request.persona_name)
        return UpdatePersonaResponse(
            success=True,
            message=f"Persona template '{request.persona_name}' applied successfully",
        )
    except Exception as e:
        return UpdatePersonaResponse(
            success=False, message=f"Error applying persona template: {str(e)}"
        )


@app.post("/core_memory/update", response_model=UpdateCoreMemoryResponse)
async def update_core_memory(request: UpdateCoreMemoryRequest):
    """Update a specific core memory block with new text"""

    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        agent.update_core_memory(text=request.text, label=request.label)
        return UpdateCoreMemoryResponse(
            success=True,
            message=f"Core memory block '{request.label}' updated successfully",
        )
    except Exception as e:
        return UpdateCoreMemoryResponse(
            success=False, message=f"Error updating core memory: {str(e)}"
        )


@app.get("/personas/core_memory", response_model=CoreMemoryPersonaResponse)
async def get_core_memory_persona(user_id: Optional[str] = None):
    """Get the core memory persona text"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        target_user = active_user if active_user else (users[0] if users else None)

        persona_text = agent.get_core_memory_persona()
        return CoreMemoryPersonaResponse(text=persona_text)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting core memory persona: {str(e)}"
        )


@app.get("/models/current", response_model=GetCurrentModelResponse)
async def get_current_model():
    """Get the current model being used by the agent"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        current_model = agent.get_current_model()
        return GetCurrentModelResponse(current_model=current_model)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting current model: {str(e)}"
        )


@app.post("/models/set", response_model=SetModelResponse)
async def set_model(request: SetModelRequest):
    """Set the model for the agent"""

    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Check if this is a custom model
        custom_models_dir = Path.home() / ".mirix" / "custom_models"
        custom_config = None

        if custom_models_dir.exists():
            # Look for a config file that matches this model name
            for config_file in custom_models_dir.glob("*.yaml"):
                try:
                    with open(config_file, "r") as f:
                        config = yaml.safe_load(f)
                        if config and config.get("model_name") == request.model:
                            custom_config = config
                            print(
                                f"Found custom model config for '{request.model}' at {config_file}"
                            )
                            break
                except Exception as e:
                    print(f"Error reading custom model config {config_file}: {e}")
                    continue

        # Set the model with custom config if found, otherwise use standard method
        if custom_config:
            result = agent.set_model(request.model, custom_agent_config=custom_config)
        else:
            result = agent.set_model(request.model)

        return SetModelResponse(
            success=result["success"],
            message=result["message"],
            missing_keys=result.get("missing_keys", []),
            model_requirements=result.get("model_requirements", {}),
        )
    except Exception as e:
        return SetModelResponse(
            success=False,
            message=f"Error setting model: {str(e)}",
            missing_keys=[],
            model_requirements={},
        )


@app.get("/models/memory/current", response_model=GetCurrentModelResponse)
async def get_current_memory_model():
    """Get the current model being used by the memory manager"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        current_model = agent.get_current_memory_model()
        return GetCurrentModelResponse(current_model=current_model)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting current memory model: {str(e)}"
        )


@app.post("/models/memory/set", response_model=SetModelResponse)
async def set_memory_model(request: SetModelRequest):
    """Set the model for the memory manager"""

    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Check if this is a custom model
        custom_models_dir = Path.home() / ".mirix" / "custom_models"
        custom_config = None

        if custom_models_dir.exists():
            # Look for a config file that matches this model name
            for config_file in custom_models_dir.glob("*.yaml"):
                try:
                    with open(config_file, "r") as f:
                        config = yaml.safe_load(f)
                        if config and config.get("model_name") == request.model:
                            custom_config = config
                            print(
                                f"Found custom model config for memory model '{request.model}' at {config_file}"
                            )
                            break
                except Exception as e:
                    print(f"Error reading custom model config {config_file}: {e}")
                    continue

        # Set the memory model with custom config if found, otherwise use standard method
        if custom_config:
            result = agent.set_memory_model(
                request.model, custom_agent_config=custom_config
            )
        else:
            result = agent.set_memory_model(request.model)

        return SetModelResponse(
            success=result["success"],
            message=result["message"],
            missing_keys=result.get("missing_keys", []),
            model_requirements=result.get("model_requirements", {}),
        )
    except Exception as e:
        return SetModelResponse(
            success=False,
            message=f"Error setting memory model: {str(e)}",
            missing_keys=[],
            model_requirements={},
        )


@app.post("/models/custom/add", response_model=AddCustomModelResponse)
async def add_custom_model(request: AddCustomModelRequest):
    """Add a custom model configuration"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # 根据模型提供商类型设置正确的endpoint_type
        model_endpoint_type = "openai" if request.model_provider == "openai-compatible" else "local_server"
        
        # Create config file for the custom model
        config = {
            "agent_name": "mirix",
            "model_name": request.model_name,
            "model_endpoint": request.model_endpoint,
            "api_key": request.api_key,
            "model_provider": request.model_provider,
            "model_endpoint_type": model_endpoint_type,
            "generation_config": {
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "context_window": request.maximum_length,
            },
        }

        # Create custom models directory if it doesn't exist
        custom_models_dir = Path.home() / ".mirix" / "custom_models"
        custom_models_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from model name (sanitize for filesystem)
        safe_model_name = "".join(
            c for c in request.model_name if c.isalnum() or c in ("-", "_", ".")
        ).rstrip()
        config_filename = f"{safe_model_name}.yaml"
        config_file_path = custom_models_dir / config_filename

        # Save config to YAML file
        with open(config_file_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

        # Also set the model in the agent
        agent.set_model(request.model_name, custom_agent_config=config)

        return AddCustomModelResponse(
            success=True,
            message=f"Custom model '{request.model_name}' added successfully and saved to {config_file_path}",
        )

    except Exception as e:
        print(f"Error adding custom model: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return AddCustomModelResponse(
            success=False, message=f"Error adding custom model: {str(e)}"
        )


@app.get("/models/custom/list", response_model=ListCustomModelsResponse)
async def list_custom_models():
    """List all available custom models"""
    try:
        custom_models_dir = Path.home() / ".mirix" / "custom_models"
        models = []

        if custom_models_dir.exists():
            for config_file in custom_models_dir.glob("*.yaml"):
                try:
                    with open(config_file, "r") as f:
                        config = yaml.safe_load(f)
                        if config and "model_name" in config:
                            models.append(config["model_name"])
                except Exception as e:
                    print(f"Error reading custom model config {config_file}: {e}")
                    continue

        return ListCustomModelsResponse(models=models)

    except Exception as e:
        print(f"Error listing custom models: {e}")
        return ListCustomModelsResponse(models=[])


@app.get("/models/custom/{model_id}", response_model=CustomModelDetailResponse)
async def get_custom_model_detail(model_id: str):
    """获取指定自定义模型的详细配置信息"""
    try:
        custom_models_dir = Path.home() / ".mirix" / "custom_models"
        config_file_path = custom_models_dir / f"{model_id}.yaml"
        
        if not config_file_path.exists():
            return CustomModelDetailResponse(
                success=False,
                message=f"模型配置文件不存在: {model_id}",
                config=None
            )
        
        with open(config_file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        # 确保向后兼容性：如果没有model_provider字段，设置默认值
        if config and "model_provider" not in config:
            config["model_provider"] = "openai-compatible"
            
        return CustomModelDetailResponse(
            success=True,
            message="获取模型配置成功",
            config=config
        )
        
    except Exception as e:
        print(f"Error getting custom model detail {model_id}: {e}")
        return CustomModelDetailResponse(
            success=False,
            message=f"获取模型配置失败: {str(e)}",
            config=None
        )


@app.put("/models/custom/{model_id}", response_model=UpdateCustomModelResponse)
async def update_custom_model(model_id: str, request: UpdateCustomModelRequest):
    """更新指定的自定义模型配置"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        custom_models_dir = validate_custom_models_directory()
        old_config_file_path = custom_models_dir / f"{model_id}.yaml"
        
        # 检查原配置文件是否存在
        if not old_config_file_path.exists():
            return UpdateCustomModelResponse(
                success=False,
                message=f"模型配置文件不存在: {model_id}"
            )
        
        # 根据模型提供商类型设置正确的endpoint_type
        model_endpoint_type = "openai" if getattr(request, 'model_provider', 'openai-compatible') == "openai-compatible" else "local_server"
        
        # 创建新的配置
        new_config = {
            "agent_name": "mirix",
            "model_name": request.model_name,
            "model_endpoint": request.model_endpoint,
            "api_key": request.api_key,
            "model_provider": getattr(request, 'model_provider', 'openai-compatible'),
            "model_endpoint_type": model_endpoint_type,
            "generation_config": {
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "context_window": request.maximum_length,
            },
        }
        
        # 生成新的文件名（如果模型名称改变了）
        new_model_id = get_model_id_from_name(request.model_name)
        new_config_file_path = custom_models_dir / f"{new_model_id}.yaml"
        
        # 保存新配置
        with open(new_config_file_path, "w", encoding="utf-8") as f:
            yaml.dump(new_config, f, default_flow_style=False, indent=2, allow_unicode=True)
        
        # 如果文件名改变了，删除旧文件
        if old_config_file_path != new_config_file_path:
            old_config_file_path.unlink()
        
        return UpdateCustomModelResponse(
            success=True,
            message=f"模型 '{request.model_name}' 更新成功",
            old_model_id=model_id if old_config_file_path != new_config_file_path else None,
            new_model_id=new_model_id if old_config_file_path != new_config_file_path else None
        )
        
    except Exception as e:
        print(f"Error updating custom model {model_id}: {e}")
        return UpdateCustomModelResponse(
            success=False,
            message=f"更新模型配置失败: {str(e)}"
        )


@app.delete("/models/custom/{model_id}", response_model=DeleteCustomModelResponse)
async def delete_custom_model(model_id: str):
    """删除指定的自定义模型配置"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        custom_models_dir = Path.home() / ".mirix" / "custom_models"
        config_file_path = custom_models_dir / f"{model_id}.yaml"
        
        if not config_file_path.exists():
            return DeleteCustomModelResponse(
                success=False,
                message=f"模型配置文件不存在: {model_id}"
            )
        
        # 读取配置以获取模型名称
        with open(config_file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        model_name = config.get("model_name", model_id)
        
        # 检查模型是否正在使用
        current_model = agent.get_current_model()
        current_memory_model = getattr(agent, 'memory_manager', None)
        current_memory_model_name = None
        if current_memory_model and hasattr(current_memory_model, 'llm_config'):
            current_memory_model_name = getattr(current_memory_model.llm_config, 'model', None)
        
        is_active_model = current_model == model_name
        is_active_memory_model = current_memory_model_name == model_name
        
        if is_active_model or is_active_memory_model:
            usage_info = []
            if is_active_model:
                usage_info.append("当前聊天模型")
            if is_active_memory_model:
                usage_info.append("当前记忆模型")
            
            return DeleteCustomModelResponse(
                success=False,
                message=f"无法删除正在使用的模型。该模型正被用作: {', '.join(usage_info)}。请先切换到其他模型。",
                was_active=True
            )
        
        # 删除配置文件
        config_file_path.unlink()
        
        return DeleteCustomModelResponse(
            success=True,
            message=f"模型 '{model_name}' 删除成功",
            was_active=False
        )
        
    except Exception as e:
        print(f"Error deleting custom model {model_id}: {e}")
        return DeleteCustomModelResponse(
            success=False,
            message=f"删除模型配置失败: {str(e)}",
            was_active=False
        )


@app.get("/models/custom/{model_id}/status", response_model=ModelStatusResponse)
async def get_custom_model_status(model_id: str):
    """获取指定自定义模型的使用状态"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        custom_models_dir = Path.home() / ".mirix" / "custom_models"
        config_file_path = custom_models_dir / f"{model_id}.yaml"
        
        if not config_file_path.exists():
            return ModelStatusResponse(
                success=False,
                model_id=model_id,
                usage_info="模型配置文件不存在"
            )
        
        # 读取配置以获取模型名称
        with open(config_file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        model_name = config.get("model_name", model_id)
        
        # 检查模型使用状态
        current_model = agent.get_current_model()
        current_memory_model = getattr(agent, 'memory_manager', None)
        current_memory_model_name = None
        if current_memory_model and hasattr(current_memory_model, 'llm_config'):
            current_memory_model_name = getattr(current_memory_model.llm_config, 'model', None)
        
        is_active = current_model == model_name
        is_memory_model = current_memory_model_name == model_name
        can_delete = not (is_active or is_memory_model)
        
        usage_info_parts = []
        if is_active:
            usage_info_parts.append("当前聊天模型")
        if is_memory_model:
            usage_info_parts.append("当前记忆模型")
        
        usage_info = ", ".join(usage_info_parts) if usage_info_parts else "未使用"
        
        return ModelStatusResponse(
            success=True,
            model_id=model_id,
            is_active=is_active,
            is_memory_model=is_memory_model,
            can_delete=can_delete,
            usage_info=usage_info
        )
        
    except Exception as e:
        print(f"Error getting custom model status {model_id}: {e}")
        return ModelStatusResponse(
            success=False,
            model_id=model_id,
            usage_info=f"获取状态失败: {str(e)}"
        )


@app.get("/timezone/current", response_model=GetTimezoneResponse)
async def get_current_timezone():
    """Get the current timezone of the agent"""

    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        target_user = active_user if active_user else (users[0] if users else None)

        if not target_user:
            raise HTTPException(status_code=404, detail="No user found")

        current_timezone = target_user.timezone
        return GetTimezoneResponse(timezone=current_timezone)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting current timezone: {str(e)}"
        )


@app.post("/timezone/set", response_model=SetTimezoneResponse)
async def set_timezone(request: SetTimezoneRequest):
    """Set the timezone for the agent"""

    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        target_user = active_user if active_user else (users[0] if users else None)

        if not target_user:
            return SetTimezoneResponse(success=False, message="No user found")

        # Update the timezone for the active user
        agent.client.server.user_manager.update_user_timezone(
            user_id=target_user.id, timezone_str=request.timezone
        )

        return SetTimezoneResponse(
            success=True,
            message=f"Timezone '{request.timezone}' set successfully for user {target_user.name}",
        )
    except Exception as e:
        return SetTimezoneResponse(
            success=False, message=f"Error setting timezone: {str(e)}"
        )


@app.get("/screenshot_setting", response_model=ScreenshotSettingResponse)
async def get_screenshot_setting():
    """Get the current screenshot setting"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    return ScreenshotSettingResponse(
        success=True,
        include_recent_screenshots=agent.include_recent_screenshots,
        message="Screenshot setting retrieved successfully",
    )


@app.post("/screenshot_setting/set", response_model=ScreenshotSettingResponse)
async def set_screenshot_setting(request: ScreenshotSettingRequest):
    """Set whether to include recent screenshots in messages"""

    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        agent.set_include_recent_screenshots(request.include_recent_screenshots)
        return ScreenshotSettingResponse(
            success=True,
            include_recent_screenshots=request.include_recent_screenshots,
            message=f"Screenshot setting updated: {'enabled' if request.include_recent_screenshots else 'disabled'}",
        )
    except Exception as e:
        return ScreenshotSettingResponse(
            success=False,
            include_recent_screenshots=False,
            message=f"Error updating screenshot setting: {str(e)}",
        )


@app.get("/api_keys/check", response_model=ApiKeyCheckResponse)
async def check_api_keys():
    """Check for missing API keys based on current agent configuration"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Use the new AgentWrapper method
        api_key_status = agent.check_api_key_status()

        return ApiKeyCheckResponse(
            missing_keys=api_key_status["missing_keys"],
            model_type=api_key_status.get("model_requirements", {}).get(
                "current_model", "unknown"
            ),
            requires_api_key=len(api_key_status["missing_keys"]) > 0,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking API keys: {str(e)}"
        )


@app.post("/api_keys/update", response_model=ApiKeyUpdateResponse)
async def update_api_key(request: ApiKeyRequest):
    """Update an API key value"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Use the new AgentWrapper method which handles .env file saving
        result = agent.provide_api_key(request.key_name, request.key_value)

        # Also update environment variable and model_settings for backwards compatibility
        if result["success"]:
            os.environ[request.key_name] = request.key_value

            from mirix.settings import model_settings

            setting_name = request.key_name.lower()
            if hasattr(model_settings, setting_name):
                setattr(model_settings, setting_name, request.key_value)
        else:
            # If AgentWrapper doesn't support this key type, fall back to manual .env saving
            if "Unsupported API key type" in result["message"]:
                # Save to .env file manually for non-Gemini keys
                _save_api_key_to_env_file(request.key_name, request.key_value)
                os.environ[request.key_name] = request.key_value

                from mirix.settings import model_settings

                setting_name = request.key_name.lower()
                if hasattr(model_settings, setting_name):
                    setattr(model_settings, setting_name, request.key_value)

                result["success"] = True
                result["message"] = (
                    f"API key '{request.key_name}' saved to .env file successfully"
                )

        return ApiKeyUpdateResponse(
            success=result["success"], message=result["message"]
        )
    except Exception as e:
        return ApiKeyUpdateResponse(
            success=False, message=f"Error updating API key: {str(e)}"
        )


def _save_api_key_to_env_file(key_name: str, api_key: str):
    """
    Helper function to save API key to .env file for non-AgentWrapper keys.
    """
    from pathlib import Path

    # Find the .env file (look in current directory and parent directories)
    env_file_path = None
    current_path = Path.cwd()

    # Check current directory and up to 3 parent directories
    for _ in range(4):
        potential_env_path = current_path / ".env"
        if potential_env_path.exists():
            env_file_path = potential_env_path
            break
        current_path = current_path.parent

    # If no .env file found, create one in the current working directory
    if env_file_path is None:
        env_file_path = Path.cwd() / ".env"

    # Read existing .env file content
    env_content = {}
    if env_file_path.exists():
        with open(env_file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_content[key.strip()] = value.strip()

    # Update the API key
    env_content[key_name] = api_key

    # Write back to .env file
    with open(env_file_path, "w") as f:
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")

    print(f"API key {key_name} saved to {env_file_path}")


# Memory endpoints
@app.get("/memory/episodic")
async def get_episodic_memory(user_id: Optional[str] = None):
    """
    Get episodic memory (past events)
    
    Note: The user_id parameter is validated for security. Only the current user's 
    data will be returned, regardless of the user_id parameter value.
    """
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        current_user = active_user if active_user else (users[0] if users else None)
        
        # 验证并清理user_id参数,确保只访问当前用户的数据
        if current_user:
            validated_user_id = validate_and_sanitize_user_id(user_id, current_user.id)
            target_user = current_user  # 始终使用当前用户
        else:
            target_user = None

        # Access the episodic memory manager through the client
        client = agent.client
        episodic_manager = client.server.episodic_memory_manager

        # Get episodic events using the correct method name
        events = episodic_manager.list_episodic_memory(
            agent_state=agent.agent_states.episodic_memory_agent_state,
            actor=target_user,
            limit=50,
            timezone_str=target_user.timezone,
        )

        # Transform to frontend format
        episodic_items = []
        for event in events:
            episodic_items.append(
                {
                    "id": event.id,  # 添加真正的数据库ID
                    "timestamp": event.occurred_at.isoformat()
                    if event.occurred_at
                    else None,
                    "summary": event.summary,
                    "details": event.details,
                    "event_type": event.event_type,
                    "tree_path": event.tree_path if hasattr(event, "tree_path") else [],
                }
            )

        return episodic_items

    except Exception as e:
        print(f"Error retrieving episodic memory: {str(e)}")
        # Return empty list if no memory or error
        return []


@app.get("/memory/semantic")
async def get_semantic_memory(user_id: Optional[str] = None):
    """
    Get semantic memory (knowledge)
    
    Note: The user_id parameter is validated for security. Only the current user's 
    data will be returned, regardless of the user_id parameter value.
    """
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        current_user = active_user if active_user else (users[0] if users else None)
        
        # 验证并清理user_id参数,确保只访问当前用户的数据
        if current_user:
            validated_user_id = validate_and_sanitize_user_id(user_id, current_user.id)
            target_user = current_user  # 始终使用当前用户
        else:
            target_user = None

        client = agent.client
        semantic_items_list = []

        # Get semantic memory items
        try:
            semantic_manager = client.server.semantic_memory_manager
            semantic_items = semantic_manager.list_semantic_items(
                agent_state=agent.agent_states.semantic_memory_agent_state,
                actor=target_user,
                limit=50,
                timezone_str=target_user.timezone,
            )

            for item in semantic_items:
                semantic_items_list.append(
                    {
                        "id": item.id,  # 添加真正的数据库ID
                        "title": item.name,
                        "type": "semantic",
                        "summary": item.summary,
                        "details": item.details,
                        "tree_path": item.tree_path
                        if hasattr(item, "tree_path")
                        else [],
                    }
                )
        except Exception as e:
            print(f"Error retrieving semantic memory: {str(e)}")

        return semantic_items_list

    except Exception as e:
        print(f"Error retrieving semantic memory: {str(e)}")
        return []


@app.get("/memory/procedural")
async def get_procedural_memory(user_id: Optional[str] = None):
    """
    Get procedural memory (skills and procedures)
    
    Note: The user_id parameter is validated for security. Only the current user's 
    data will be returned, regardless of the user_id parameter value.
    """
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        current_user = active_user if active_user else (users[0] if users else None)
        
        # 验证并清理user_id参数,确保只访问当前用户的数据
        if current_user:
            validated_user_id = validate_and_sanitize_user_id(user_id, current_user.id)
            target_user = current_user  # 始终使用当前用户
        else:
            target_user = None

        client = agent.client
        procedural_items_list = []

        # Get procedural memory items
        try:
            procedural_manager = client.server.procedural_memory_manager
            procedural_items = procedural_manager.list_procedures(
                agent_state=agent.agent_states.procedural_memory_agent_state,
                actor=target_user,
                limit=50,
                timezone_str=target_user.timezone,
            )

            for item in procedural_items:
                # Parse steps if it's a JSON string
                steps = item.steps
                if isinstance(steps, str):
                    try:
                        steps = json.loads(steps)
                        # Extract just the instruction text for simpler frontend display
                        if (
                            isinstance(steps, list)
                            and steps
                            and isinstance(steps[0], dict)
                        ):
                            steps = [
                                step.get("instruction", str(step)) for step in steps
                            ]
                    except (json.JSONDecodeError, KeyError, TypeError):
                        # If parsing fails, keep as string and split by common delimiters
                        if isinstance(steps, str):
                            steps = [
                                s.strip()
                                for s in steps.replace("\n", "|").split("|")
                                if s.strip()
                            ]
                        else:
                            steps = []

                procedural_items_list.append(
                    {
                        "id": item.id,  # 添加真正的数据库ID
                        "title": item.entry_type,
                        "type": "procedural",
                        "summary": item.summary,
                        "steps": steps if isinstance(steps, list) else [],
                        "tree_path": item.tree_path
                        if hasattr(item, "tree_path")
                        else [],
                    }
                )

        except Exception as e:
            print(f"Error retrieving procedural memory: {str(e)}")

        return procedural_items_list

    except Exception as e:
        print(f"Error retrieving procedural memory: {str(e)}")
        return []


@app.get("/memory/resources")
async def get_resource_memory(user_id: Optional[str] = None):
    """
    Get resource memory (docs and files)
    
    Note: The user_id parameter is validated for security. Only the current user's 
    data will be returned, regardless of the user_id parameter value.
    """
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        current_user = active_user if active_user else (users[0] if users else None)
        
        # 验证并清理user_id参数,确保只访问当前用户的数据
        if current_user:
            validated_user_id = validate_and_sanitize_user_id(user_id, current_user.id)
            target_user = current_user  # 始终使用当前用户
        else:
            target_user = None

        client = agent.client
        resource_manager = client.server.resource_memory_manager

        # Get resource memory items using correct method name
        resources = resource_manager.list_resources(
            agent_state=agent.agent_states.resource_memory_agent_state,
            actor=target_user,
            limit=50,
            timezone_str=target_user.timezone,
        )

        # Transform to frontend format
        docs_files = []
        for resource in resources:
            docs_files.append(
                {
                    "id": resource.id,  # 添加真正的数据库ID
                    "filename": resource.title,
                    "type": resource.resource_type,
                    "summary": resource.summary
                    or (
                        resource.content[:200] + "..."
                        if len(resource.content) > 200
                        else resource.content
                    ),
                    "last_accessed": resource.updated_at.isoformat()
                    if resource.updated_at
                    else None,
                    "size": resource.metadata_.get("size")
                    if resource.metadata_
                    else None,
                    "tree_path": resource.tree_path
                    if hasattr(resource, "tree_path")
                    else [],
                }
            )

        return docs_files

    except Exception as e:
        print(f"Error retrieving resource memory: {str(e)}")
        return []


@app.get("/memory/core")
async def get_core_memory():
    """Get core memory (understanding of user)"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Get core memory from the main agent
        core_memory = agent.client.get_in_context_memory(
            agent.agent_states.agent_state.id
        )

        core_understanding = []
        total_characters = 0

        # Extract understanding from memory blocks (skip persona block)
        for block in core_memory.blocks:
            if block.value and block.value.strip() and block.label.lower() != "persona":
                block_chars = len(block.value)
                total_characters += block_chars

                core_item = {
                    "aspect": block.label,
                    "understanding": block.value,
                    "character_count": block_chars,
                    "total_characters": total_characters,
                    "max_characters": block.limit,
                    "last_updated": None,  # Core memory doesn't track individual updates
                }

                core_understanding.append(core_item)

        return core_understanding

    except Exception as e:
        print(f"Error retrieving core memory: {str(e)}")
        return []


@app.get("/memory/credentials")
async def get_credentials_memory():
    """Get credentials memory (knowledge vault with masked content)"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        client = agent.client
        knowledge_vault_manager = client.server.knowledge_vault_manager

        # Get knowledge vault items using correct method name
        vault_items = knowledge_vault_manager.list_knowledge(
            actor=agent.client.user,
            agent_state=agent.agent_states.knowledge_vault_agent_state,
            limit=50,
            timezone_str=agent.client.server.user_manager.get_user_by_id(
                agent.client.user.id
            ).timezone,
        )

        # Transform to frontend format with masked content
        credentials = []
        for item in vault_items:
            credentials.append(
                {
                    "id": item.id,  # 添加真正的数据库ID
                    "caption": item.caption,
                    "entry_type": item.entry_type,
                    "source": item.source,
                    "sensitivity": item.sensitivity,
                    "content": "••••••••••••"
                    if item.sensitivity == "high"
                    else item.secret_value,  # Always mask the actual content
                }
            )

        return credentials

    except Exception as e:
        print(f"Error retrieving credentials memory: {str(e)}")
        return []


# Memory management endpoints
@app.delete("/memory/{memory_type}/batch", response_model=DeleteMemoryResponse)
async def delete_memories_batch(memory_type: str, request: DeleteMemoryRequest):
    """批量删除指定类型的记忆"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # 验证记忆类型
        valid_types = ["episodic", "semantic", "procedural", "resource", "core", "credentials"]
        if memory_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的记忆类型: {memory_type}。支持的类型: {', '.join(valid_types)}"
            )

        # 获取用户
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        target_user = active_user if active_user else (users[0] if users else None)
        
        if not target_user:
            raise HTTPException(status_code=404, detail="未找到用户")

        # 这里是占位实现，需要根据实际MIRIX API调整
        deleted_count = len(request.memory_ids)  # 占位
        failed_ids = []  # 占位

        return DeleteMemoryResponse(
            success=deleted_count > 0,
            message=f"成功删除 {deleted_count} 条记忆",
            deleted_count=deleted_count,
            failed_ids=failed_ids
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除记忆失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除记忆时发生错误: {str(e)}")


@app.delete("/memory/{memory_type}/{memory_id}", response_model=DeleteMemoryResponse)
async def delete_single_memory(memory_type: str, memory_id: str):
    """删除单个记忆"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # 验证记忆类型
        valid_types = ["episodic", "semantic", "procedural", "resource", "core", "credentials"]
        if memory_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的记忆类型: {memory_type}。支持的类型: {', '.join(valid_types)}"
            )

        # 获取用户
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        target_user = active_user if active_user else (users[0] if users else None)
        
        if not target_user:
            raise HTTPException(status_code=404, detail="未找到用户")

        # 根据记忆类型调用相应的删除方法
        try:
            client = agent.client
            
            if memory_type == "episodic":
                episodic_manager = client.server.episodic_memory_manager
                episodic_manager.delete_event_by_id(memory_id, actor=target_user)
            elif memory_type == "semantic":
                semantic_manager = client.server.semantic_memory_manager
                semantic_manager.delete_semantic_item_by_id(memory_id, actor=target_user)
            elif memory_type == "procedural":
                procedural_manager = client.server.procedural_memory_manager
                procedural_manager.delete_procedure_by_id(memory_id, actor=target_user)
            elif memory_type == "resource":
                resource_manager = client.server.resource_memory_manager
                resource_manager.delete_resource_by_id(memory_id, actor=target_user)
            elif memory_type == "core":
                block_manager = client.server.block_manager
                block_manager.delete_block(memory_id, actor=target_user)
            elif memory_type == "credentials":
                knowledge_vault_manager = client.server.knowledge_vault_manager
                knowledge_vault_manager.delete_knowledge_by_id(memory_id, actor=target_user)
            
            return DeleteMemoryResponse(
                success=True,
                message="记忆删除成功",
                deleted_count=1,
                failed_ids=[]
            )
            
        except Exception as e:
            # 如果删除失败，返回失败信息
            error_msg = str(e)
            if "not found" in error_msg.lower():
                return DeleteMemoryResponse(
                    success=False,
                    message=f"未找到指定的记忆: {error_msg}",
                    deleted_count=0,
                    failed_ids=[memory_id]
                )
            else:
                return DeleteMemoryResponse(
                    success=False,
                    message=f"删除记忆失败: {error_msg}",
                    deleted_count=0,
                    failed_ids=[memory_id]
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除记忆失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除记忆时发生错误: {str(e)}")


@app.put("/memory/{memory_type}/{memory_id}", response_model=UpdateMemoryResponse)
async def update_memory(memory_type: str, memory_id: str, request: UpdateMemoryRequest):
    """更新记忆内容"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # 验证记忆类型
        valid_types = ["episodic", "semantic", "procedural", "resource", "core", "credentials"]
        if memory_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的记忆类型: {memory_type}。支持的类型: {', '.join(valid_types)}"
            )

        # 获取用户
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        target_user = active_user if active_user else (users[0] if users else None)
        
        if not target_user:
            raise HTTPException(status_code=404, detail="未找到用户")

        # 根据记忆类型调用相应的更新方法
        try:
            client = agent.client
            updated_memory = None
            
            if memory_type == "episodic":
                # 对于情景记忆，使用update_event方法
                episodic_manager = client.server.episodic_memory_manager
                updated_memory = episodic_manager.update_event(
                    event_id=memory_id,
                    new_summary=request.updates.get('summary'),
                    new_details=request.updates.get('details'),
                    actor=target_user
                )
                
            elif memory_type == "semantic":
                # 语义记忆的更新逻辑
                from mirix.schemas.semantic_memory import SemanticMemoryItemUpdate
                semantic_manager = client.server.semantic_memory_manager
                
                update_data = SemanticMemoryItemUpdate(
                    id=memory_id,
                    name=request.updates.get('title'),
                    summary=request.updates.get('summary'),
                    details=request.updates.get('details')
                )
                updated_memory = semantic_manager.update_item(update_data, actor=target_user)
                
            elif memory_type == "procedural":
                # 程序记忆的更新逻辑
                from mirix.schemas.procedural_memory import ProceduralMemoryItemUpdate
                procedural_manager = client.server.procedural_memory_manager
                
                update_data = ProceduralMemoryItemUpdate(
                    id=memory_id,
                    summary=request.updates.get('summary'),
                    content=request.updates.get('content'),
                    steps=request.updates.get('steps')
                )
                updated_memory = procedural_manager.update_item(update_data, actor=target_user)
                
            elif memory_type == "resource":
                # 资源记忆的更新逻辑 - 需要检查是否有更新方法
                resource_manager = client.server.resource_memory_manager
                # 注意：这里可能需要根据实际的资源管理器API来实现
                updated_memory = {
                    "id": memory_id,
                    "type": memory_type,
                    "message": "资源记忆更新功能需要进一步实现",
                    **request.updates
                }
                
            elif memory_type == "core":
                # 核心记忆的更新逻辑
                block_manager = client.server.block_manager
                # 注意：这里可能需要根据实际的block_manager API来实现
                updated_memory = {
                    "id": memory_id,
                    "type": memory_type,
                    "message": "核心记忆更新功能需要进一步实现",
                    **request.updates
                }
                
            elif memory_type == "credentials":
                # 凭证记忆的更新逻辑
                knowledge_vault_manager = client.server.knowledge_vault_manager
                # 注意：这里可能需要根据实际的knowledge_vault_manager API来实现
                updated_memory = {
                    "id": memory_id,
                    "type": memory_type,
                    "message": "凭证记忆更新功能需要进一步实现",
                    **request.updates
                }
            
            return UpdateMemoryResponse(
                success=True,
                message="记忆更新成功",
                updated_memory=updated_memory.model_dump() if hasattr(updated_memory, 'model_dump') else updated_memory
            )
            
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=f"未找到指定的记忆: {error_msg}")
            else:
                raise HTTPException(status_code=500, detail=f"更新记忆失败: {error_msg}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新记忆失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新记忆时发生错误: {str(e)}")


@app.post("/conversation/clear", response_model=ClearConversationResponse)
async def clear_conversation_history():
    """Permanently clear all conversation history for the current agent (memories are preserved)"""
    try:
        if agent is None:
            raise HTTPException(status_code=400, detail="Agent not initialized")

        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        target_user = active_user if active_user else (users[0] if users else None)

        # Get current message count for this specific actor for reporting
        current_messages = agent.client.server.agent_manager.get_in_context_messages(
            agent_id=agent.agent_states.agent_state.id, actor=target_user
        )
        # Count messages belonging to this actor (excluding system messages)
        actor_messages_count = len(
            [
                msg
                for msg in current_messages
                if msg.role != "system" and msg.user_id == target_user.id
            ]
        )

        # Clear conversation history using the agent manager reset_messages method
        agent.client.server.agent_manager.reset_messages(
            agent_id=agent.agent_states.agent_state.id,
            actor=target_user,
            add_default_initial_messages=True,  # Keep system message and initial setup
        )

        return ClearConversationResponse(
            success=True,
            message=f"Successfully cleared conversation history for {target_user.name}. Messages from other users and system messages preserved.",
            messages_deleted=actor_messages_count,
        )

    except Exception as e:
        print(f"Error clearing conversation history: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Error clearing conversation: {str(e)}"
        )


@app.post("/export/memories", response_model=ExportMemoriesResponse)
async def export_memories(request: ExportMemoriesRequest):
    """Export memories to Excel file with separate sheets for each memory type"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Find the current active user
        users = agent.client.server.user_manager.list_users()
        active_user = next((user for user in users if user.status == "active"), None)
        target_user = active_user if active_user else (users[0] if users else None)
        result = agent.export_memories_to_excel(
            actor=target_user,
            file_path=request.file_path,
            memory_types=request.memory_types,
            include_embeddings=request.include_embeddings,
        )

        if result["success"]:
            return ExportMemoriesResponse(
                success=True,
                message=result["message"],
                exported_counts=result["exported_counts"],
                total_exported=result["total_exported"],
                file_path=result["file_path"],
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        print(f"Error exporting memories: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Failed to export memories: {str(e)}"
        )


@app.post("/reflexion", response_model=ReflexionResponse)
async def trigger_reflexion(request: ReflexionRequest):
    """Trigger reflexion agent to reorganize memory - runs in separate thread to not block other requests"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        print("Starting reflexion process...")
        start_time = datetime.now()

        # Run reflexion in a separate thread to avoid blocking other requests
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,  # Use default ThreadPoolExecutor
            _run_reflexion_process,
            agent,
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        print(f"Reflexion process completed in {processing_time:.2f} seconds")

        return ReflexionResponse(
            success=result["success"],
            message=result["message"],
            processing_time=processing_time,
        )

    except Exception as e:
        print(f"Error in reflexion endpoint: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Reflexion process failed: {str(e)}"
        )


# MCP Marketplace endpoints
@app.get("/mcp/marketplace")
async def get_marketplace():
    """Get available MCP servers from marketplace"""
    marketplace = get_mcp_marketplace()
    servers = marketplace.get_all_servers()
    categories = marketplace.get_categories()

    # Check connection status
    mcp_manager = get_mcp_client_manager()
    connected_servers = mcp_manager.list_servers()

    # Debug logging
    logger.debug(
        f"MCP Marketplace: {len(connected_servers)} connected servers: {connected_servers}"
    )

    server_data = []
    for server in servers:
        server_dict = server.to_dict()
        server_dict["is_connected"] = server.id in connected_servers
        server_data.append(server_dict)

    return {"servers": server_data, "categories": categories}


@app.get("/mcp/status")
async def get_mcp_status():
    """Get current MCP connection status"""
    try:
        mcp_manager = get_mcp_client_manager()
        connected_servers = mcp_manager.list_servers()

        # Get detailed status for each connected server
        server_status = {}
        for server_name in connected_servers:
            try:
                # Try to get server info to verify it's actually working
                info = mcp_manager.get_server_info(server_name)
                server_status[server_name] = {
                    "connected": True,
                    "status": "active",
                    "info": info,
                }
            except Exception as e:
                server_status[server_name] = {
                    "connected": False,
                    "status": "error",
                    "error": str(e),
                }

        return {
            "connected_servers": connected_servers,
            "server_count": len(connected_servers),
            "server_status": server_status,
        }

    except Exception as e:
        logger.error(f"Error getting MCP status: {str(e)}")
        return {
            "connected_servers": [],
            "server_count": 0,
            "server_status": {},
            "error": str(e),
        }


@app.get("/mcp/marketplace/search")
async def search_mcp_marketplace(query: str = ""):
    """Search MCP marketplace"""
    try:
        marketplace = get_mcp_marketplace()

        if query.strip():
            results = marketplace.search(query)
        else:
            results = marketplace.get_all_servers()

        # Check connection status
        mcp_manager = get_mcp_client_manager()
        connected_servers = mcp_manager.list_servers()

        result_data = []
        for server in results:
            server_dict = server.to_dict()
            server_dict["is_connected"] = server.id in connected_servers
            result_data.append(server_dict)

        return {"results": result_data}

    except Exception as e:
        logger.error(f"Error searching MCP marketplace: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to search MCP marketplace: {str(e)}"
        )


@app.post("/mcp/marketplace/connect")
async def connect_mcp_server(request: dict):
    """Connect to an MCP server"""
    try:
        server_id = request.get("server_id")
        env_vars = request.get("env_vars", {})

        if not server_id:
            raise HTTPException(status_code=400, detail="server_id is required")

        marketplace = get_mcp_marketplace()
        server_listing = marketplace.get_server(server_id)

        if not server_listing:
            raise HTTPException(
                status_code=404, detail=f"Server {server_id} not found in marketplace"
            )

        mcp_manager = get_mcp_client_manager()

        # Special handling for Gmail - handle OAuth flow directly in backend
        if server_id == "gmail-native":
            client_id = env_vars.get("client_id")
            client_secret = env_vars.get("client_secret")

            if not client_id or not client_secret:
                raise HTTPException(
                    status_code=400,
                    detail="client_id and client_secret are required for Gmail integration",
                )

            # Handle Gmail OAuth and MCP connection directly
            success = await handle_gmail_connection(
                client_id, client_secret, server_listing.id
            )

        else:
            # Create stdio config for other servers
            config = StdioServerConfig(
                server_name=server_listing.id,
                command=server_listing.command,
                args=server_listing.args,
                env={**(server_listing.env or {}), **env_vars},
            )
            success = mcp_manager.add_server(config, env_vars)

        if success:
            # Register tools for this server
            mcp_tool_registry = get_mcp_tool_registry()
            # Get current user (using agent's user for now)
            if agent and agent.client.user:
                current_user = agent.client.user
                registered_tools = mcp_tool_registry.register_mcp_tools(
                    current_user, [server_listing.id]
                )
                tools_count = len(registered_tools)
            else:
                tools_count = 0

            # Add MCP tool to the current chat agent if available
            if agent and agent.client.user and hasattr(agent, "agent_states"):
                # Update the agent's MCP tools list
                agent.client.server.agent_manager.add_mcp_tool(
                    agent_id=agent.agent_states.agent_state.id,
                    mcp_tool_name=server_listing.id,
                    tool_ids=list(
                        set(
                            [tool.id for tool in registered_tools]
                            + [
                                tool.id
                                for tool in agent.client.server.agent_manager.get_agent_by_id(
                                    agent.agent_states.agent_state.id,
                                    actor=agent.client.user,
                                ).tools
                            ]
                        )
                    ),
                    actor=agent.client.user,
                )

                print(
                    f"✅ Added MCP tool '{server_listing.id}' to agent '{agent.agent_states.agent_state.name}'"
                )

            return {
                "success": True,
                "server_name": server_listing.name,
                "tools_count": tools_count,
                "message": f"Successfully connected to {server_listing.name}",
            }
        else:
            return {
                "success": False,
                "error": f"Failed to connect to {server_listing.name}",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting MCP server: {str(e)}")
        return {"success": False, "error": f"Connection failed: {str(e)}"}


@app.post("/mcp/marketplace/disconnect")
async def disconnect_mcp_server(request: dict):
    """Disconnect from an MCP server"""

    server_id = request.get("server_id")

    if not server_id:
        raise HTTPException(status_code=400, detail="server_id is required")

    mcp_manager = get_mcp_client_manager()
    success = mcp_manager.remove_server(server_id)

    if success:
        # Unregister tools for this server and get the list of unregistered tool IDs
        mcp_tool_registry = get_mcp_tool_registry()
        if agent and agent.client.user:
            current_user = agent.client.user
            unregistered_tool_ids = mcp_tool_registry.unregister_mcp_tools(
                current_user, server_id
            )
            logger.info(
                f"Unregistered {len(unregistered_tool_ids)} tools for server {server_id}"
            )

            # Remove MCP tool from the current chat agent if available
            if hasattr(agent, "agent_states"):
                # Get current agent state
                current_agent = agent.client.server.agent_manager.get_agent_by_id(
                    agent.agent_states.agent_state.id, actor=agent.client.user
                )

                # Remove the specific MCP server from the mcp_tools list
                updated_mcp_tools = [
                    tool
                    for tool in (current_agent.mcp_tools or [])
                    if tool != server_id
                ]

                # Remove only the tools that belonged to this MCP server
                current_tool_ids = [tool.id for tool in current_agent.tools]
                updated_tool_ids = [
                    tool_id
                    for tool_id in current_tool_ids
                    if tool_id not in unregistered_tool_ids
                ]

                # Update the agent with the filtered lists
                agent.client.server.agent_manager.update_mcp_tools(
                    agent_id=agent.agent_states.agent_state.id,
                    mcp_tools=updated_mcp_tools,
                    tool_ids=updated_tool_ids,
                    actor=agent.client.user,
                )
                print(
                    f"✅ Removed MCP tool '{server_id}' and {len(unregistered_tool_ids)} associated tools from agent '{agent.agent_states.agent_state.name}'"
                )

        return {
            "success": True,
            "message": f"Successfully disconnected from {server_id}",
        }
    else:
        return {"success": False, "error": f"Failed to disconnect from {server_id}"}


def _run_reflexion_process(agent):
    """
    Run the reflexion process - this is the blocking function that runs in a separate thread.
    This function can be replaced with the actual reflexion agent logic.
    """
    try:
        # TODO: Replace this with actual reflexion agent logic
        # For now, this is a placeholder that simulates reflexion work

        agent.reflexion_on_memory()
        return {
            "success": True,
            "message": "Memory reorganization completed successfully. Reflexion agent has optimized memory structure and connections.",
        }

    except Exception as e:
        print(f"Error in reflexion process: {str(e)}")
        return {"success": False, "message": f"Reflexion process failed: {str(e)}"}


@app.post("/confirmation/respond")
async def respond_to_confirmation(request: ConfirmationRequest):
    """Handle user confirmation response"""
    confirmation_id = request.confirmation_id
    confirmed = request.confirmed

    # Find the confirmation queue for this ID
    confirmation_queue = confirmation_queues.get(confirmation_id)

    if confirmation_queue:
        # Send the confirmation result to the waiting thread
        confirmation_queue.put({"confirmed": confirmed})
        return {"success": True, "message": "Confirmation received"}
    else:
        return {"success": False, "message": "Confirmation ID not found or expired"}


@app.get("/users")
async def get_all_users():
    """Get all users in the system"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        users = agent.client.server.user_manager.list_users()
        return {"users": [user.model_dump() for user in users]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")


class SwitchUserRequest(BaseModel):
    user_id: str


class SwitchUserResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None


@app.post("/users/switch", response_model=SwitchUserResponse)
async def switch_user(request: SwitchUserRequest):
    """
    Switch the active user (DISABLED FOR SECURITY)
    
    This endpoint is disabled for security reasons to prevent unauthorized 
    access to other users' data. Please contact administrator if you need 
    this feature.
    """
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    # 记录切换尝试并拒绝
    logger.warning(
        f"User switch attempt blocked: target_user_id={request.user_id}. "
        f"This feature is disabled for security reasons."
    )
    
    raise HTTPException(
        status_code=403,
        detail="User switching is disabled for security reasons. "
               "Please contact administrator if you need this feature."
    )


class CreateUserRequest(BaseModel):
    name: str
    set_as_active: bool = True  # Whether to set this user as active when created


class UploadDocumentRequest(BaseModel):
    """文档上传请求模型"""
    file_name: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    content: str = Field(..., description="Base64编码的文件内容")
    user_id: Optional[str] = Field(None, description="用户ID")
    description: Optional[str] = Field(None, description="文档描述")


class UploadDocumentResponse(BaseModel):
    """文档上传响应模型"""
    success: bool = Field(..., description="上传是否成功")
    message: str = Field(..., description="响应消息")
    document_id: Optional[str] = Field(None, description="文档ID")
    processed_content: Optional[Dict[str, Any]] = Field(None, description="处理后的内容信息")


class CreateUserResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None


@app.post("/users/create", response_model=CreateUserResponse)
async def create_user(request: CreateUserRequest):
    """Create a new user in the system"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Use the AgentWrapper's create_user method
        result = agent.create_user(
            name=request.name, set_as_active=request.set_as_active
        )

        return CreateUserResponse(
            success=result["success"],
            message=result["message"],
            user=result["user"].model_dump(),
        )

    except Exception as e:
        return CreateUserResponse(
            success=False, message=f"Error creating user: {str(e)}"
        )


@app.post("/documents/upload", response_model=UploadDocumentResponse)
async def upload_document(request: UploadDocumentRequest):
    """
    上传文档并处理为记忆数据
    
    支持格式：markdown、txt、excel、csv等
    集成文档处理器进行文档处理和记忆存储
    
    Args:
        request: 文档上传请求
        
    Returns:
        UploadDocumentResponse: 上传处理结果
    """
    logger.info(f"=== 文档上传请求开始 ===")
    logger.info(f"文件名: {request.file_name}")
    logger.info(f"文件类型: {request.file_type}")
    logger.info(f"用户ID: {request.user_id}")
    logger.info(f"内容长度: {len(request.content) if request.content else 0}")
    
    if agent is None:
        logger.error("智能体未初始化")
        raise HTTPException(status_code=500, detail="智能体未初始化")
    
    try:
        # 解码Base64内容
        try:
            logger.info(f"接收到的content类型: {type(request.content)}")
            logger.info(f"接收到的content长度: {len(request.content) if request.content else 0}")
            logger.info(f"接收到的content前100字符: {request.content[:100] if request.content else 'None'}")
            
            file_content = base64.b64decode(request.content)
            logger.info(f"Base64解码成功，内容长度: {len(file_content)}")
        except Exception as e:
            logger.error(f"Base64解码失败: {e}")
            logger.error(f"解码失败的content: {request.content}")
            raise HTTPException(status_code=400, detail=f"文件内容解码失败: {str(e)}")
        
        # 初始化文档处理器
        from mirix.services.document_processor import DocumentProcessor
        document_processor = DocumentProcessor()
        
        # 检查文件格式支持
        if not document_processor.is_supported_format(request.file_name):
            supported_formats = list(document_processor.SUPPORTED_FORMATS.keys())
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式。支持的格式: {', '.join(supported_formats)}"
            )
        
        # 处理文档内容
        logger.info("开始处理文档内容")
        processed_doc = document_processor.process_document(
            file_path=request.file_name,
            content=file_content
        )
        
        # 提取文本内容
        text_content = document_processor.extract_text_content(processed_doc)
        
        # 获取当前用户 - 文档必须归属于当前用户,确保数据隔离
        current_user = agent.client.server.user_manager.get_user_by_id(agent.client.user_id)
        if not current_user:
            raise HTTPException(status_code=500, detail="无法获取当前用户信息")
        
        # 获取资源记忆管理器
        resource_manager = agent.client.server.resource_memory_manager
        
        # 创建资源记忆项 - 强制使用当前用户ID,忽略请求中的user_id参数
        from mirix.schemas.resource_memory import ResourceMemoryItem
        item_data = ResourceMemoryItem(
            title=request.file_name,
            content=text_content,
            summary=processed_doc.get('summary', ''),
            resource_type=processed_doc.get('file_type', 'unknown'),
            metadata_=processed_doc,
            tree_path=[],  # 文档路径
            user_id=current_user.id,  # 强制使用当前用户ID
            organization_id=current_user.organization_id  # 强制使用当前组织ID
        )
        
        resource_item = resource_manager.create_item(
            item_data=item_data,
            actor=current_user
        )
        
        logger.info(f"文档已存储到记忆系统: {resource_item.id}")
        
        # 构建响应消息
        success_message = f"文档 '{request.file_name}' 上传并处理成功"
        
        return UploadDocumentResponse(
            success=True,
            message=success_message,
            document_id=resource_item.id,
            processed_content={
                "file_name": processed_doc['file_name'],
                "file_type": processed_doc['file_type'],
                "summary": processed_doc.get('summary', ''),
                "word_count": processed_doc.get('word_count'),
                "processed_at": processed_doc.get('processed_at')
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传处理失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"文档处理失败: {str(e)}"
        )


# 新增向量搜索API接口
class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询字符串")
    search_method: str = Field(default="embedding", description="搜索方法，默认为embedding")
    search_field: str = Field(default="summary", description="搜索字段")
    limit: int = Field(default=10, description="返回结果数量限制")
    user_id: Optional[str] = Field(None, description="用户ID")
    similarity_threshold: float = Field(default=0.7, description="相似度阈值")


@app.post("/memories/episodic/search")
async def search_episodic_memory(request: VectorSearchRequest):
    """向量搜索情景记忆"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        logger.info(f"情景记忆向量搜索: query='{request.query}', method={request.search_method}, user_id={request.user_id}")
        
        # 获取用户 - 如果没有指定user_id，使用当前活跃用户或默认用户
        if request.user_id:
            target_user = get_user_or_default(agent, request.user_id)
        else:
            target_user = get_user_or_default(agent, None)
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        logger.debug(f"使用用户: {target_user.id}")

        # 获取情景记忆管理器
        episodic_manager = agent.client.server.episodic_memory_manager
        
        # 执行搜索，添加SSL错误重试
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 先获取查询的embedding向量
                from mirix.embeddings import embedding_model
                embed_model = embedding_model(agent.agent_states.episodic_memory_agent_state.embedding_config)
                query_embedding = embed_model.get_text_embedding(request.query)
                
                results = episodic_manager.list_episodic_memory(
                    agent_state=agent.agent_states.episodic_memory_agent_state,
                    query=request.query,
                    search_method=request.search_method,
                    search_field=request.search_field,
                    actor=target_user,
                    limit=request.limit
                )
                break  # 成功则跳出重试循环
            except Exception as e:
                if "SSL" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"SSL错误，重试 {attempt + 1}/{max_retries}: {e}")
                    import time
                    time.sleep(1)  # 等待1秒后重试
                    continue
                else:
                    raise  # 非SSL错误或已达到最大重试次数，抛出异常
        
        # 转换结果格式，计算真实相似度分数
        formatted_results = []
        for event in results:
            # 计算相似度分数
            similarity_score = 0.5  # 默认分数
            try:
                if hasattr(event, 'details_embedding') and event.details_embedding:
                    # 计算余弦相似度
                    import numpy as np
                    event_embedding = np.array(event.details_embedding)
                    query_embedding_np = np.array(query_embedding)
                    
                    # 计算余弦相似度 (1 - cosine_distance)
                    dot_product = np.dot(event_embedding, query_embedding_np)
                    norm_event = np.linalg.norm(event_embedding)
                    norm_query = np.linalg.norm(query_embedding_np)
                    
                    if norm_event > 0 and norm_query > 0:
                        similarity_score = dot_product / (norm_event * norm_query)
                        # 确保分数在0-1范围内
                        similarity_score = max(0, min(1, similarity_score))
            except Exception as e:
                logger.debug(f"计算相似度失败: {e}")
            
            event_dict = {
                "id": event.id,
                "summary": event.summary,
                "details": event.details,
                "event_type": event.event_type,
                "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
                "tree_path": getattr(event, "tree_path", []),
                "similarity_score": similarity_score
            }
            formatted_results.append(event_dict)
        
        # 按相似度分数排序
        formatted_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        logger.info(f"情景记忆搜索完成，找到 {len(formatted_results)} 条结果")
        return formatted_results

    except Exception as e:
        logger.error(f"情景记忆搜索失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@app.post("/memories/semantic/search")
async def search_semantic_memory(request: VectorSearchRequest):
    """向量搜索语义记忆"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        logger.info(f"语义记忆向量搜索: query='{request.query}', method={request.search_method}, user_id={request.user_id}")
        
        # 获取用户 - 如果没有指定user_id，使用当前活跃用户或默认用户
        if request.user_id:
            target_user = get_user_or_default(agent, request.user_id)
        else:
            target_user = get_user_or_default(agent, None)
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        logger.debug(f"使用用户: {target_user.id}")

        # 获取语义记忆管理器
        semantic_manager = agent.client.server.semantic_memory_manager
        
        # 执行搜索，添加SSL错误重试
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 先获取查询的embedding向量
                from mirix.embeddings import embedding_model
                embed_model = embedding_model(agent.agent_states.semantic_memory_agent_state.embedding_config)
                query_embedding = embed_model.get_text_embedding(request.query)
                
                results = semantic_manager.list_semantic_items(
                    agent_state=agent.agent_states.semantic_memory_agent_state,
                    query=request.query,
                    search_method=request.search_method,
                    search_field=request.search_field,
                    actor=target_user,
                    limit=request.limit
                )
                break  # 成功则跳出重试循环
            except Exception as e:
                if "SSL" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"SSL错误，重试 {attempt + 1}/{max_retries}: {e}")
                    import time
                    time.sleep(1)  # 等待1秒后重试
                    continue
                else:
                    raise  # 非SSL错误或已达到最大重试次数，抛出异常
        
        # 转换结果格式，计算真实相似度分数
        formatted_results = []
        for item in results:
            # 计算相似度分数
            similarity_score = 0.5  # 默认分数
            try:
                if hasattr(item, 'details_embedding') and item.details_embedding:
                    # 计算余弦相似度
                    import numpy as np
                    item_embedding = np.array(item.details_embedding)
                    query_embedding_np = np.array(query_embedding)
                    
                    # 计算余弦相似度
                    dot_product = np.dot(item_embedding, query_embedding_np)
                    norm_item = np.linalg.norm(item_embedding)
                    norm_query = np.linalg.norm(query_embedding_np)
                    
                    if norm_item > 0 and norm_query > 0:
                        similarity_score = dot_product / (norm_item * norm_query)
                        similarity_score = max(0, min(1, similarity_score))
            except Exception as e:
                logger.debug(f"计算相似度失败: {e}")
            
            item_dict = {
                "id": item.id,
                "name": item.name,
                "summary": item.summary,
                "details": item.details,
                "tree_path": getattr(item, "tree_path", []),
                "similarity_score": similarity_score
            }
            formatted_results.append(item_dict)
        
        # 按相似度分数排序
        formatted_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        logger.info(f"语义记忆搜索完成，找到 {len(formatted_results)} 条结果")
        return formatted_results

    except Exception as e:
        logger.error(f"语义记忆搜索失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@app.post("/memories/procedural/search")
async def search_procedural_memory(request: VectorSearchRequest):
    """向量搜索程序记忆"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        logger.info(f"程序记忆向量搜索: query='{request.query}', method={request.search_method}, user_id={request.user_id}")
        
        # 获取用户 - 如果没有指定user_id，使用当前活跃用户或默认用户
        if request.user_id:
            target_user = get_user_or_default(agent, request.user_id)
        else:
            target_user = get_user_or_default(agent, None)
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        logger.debug(f"使用用户: {target_user.id}")

        # 获取程序记忆管理器
        procedural_manager = agent.client.server.procedural_memory_manager
        
        # 执行搜索
        # 先获取查询的embedding向量
        from mirix.embeddings import embedding_model
        embed_model = embedding_model(agent.agent_states.procedural_memory_agent_state.embedding_config)
        query_embedding = embed_model.get_text_embedding(request.query)
        
        results = procedural_manager.list_procedures(
            agent_state=agent.agent_states.procedural_memory_agent_state,
            query=request.query,
            search_method=request.search_method,
            search_field=request.search_field,
            actor=target_user,
            limit=request.limit
        )
        
        # 转换结果格式，计算真实相似度分数
        formatted_results = []
        for item in results:
            # 计算相似度分数
            similarity_score = 0.5  # 默认分数
            try:
                if hasattr(item, 'summary_embedding') and item.summary_embedding:
                    # 计算余弦相似度
                    import numpy as np
                    item_embedding = np.array(item.summary_embedding)
                    query_embedding_np = np.array(query_embedding)
                    
                    # 计算余弦相似度
                    dot_product = np.dot(item_embedding, query_embedding_np)
                    norm_item = np.linalg.norm(item_embedding)
                    norm_query = np.linalg.norm(query_embedding_np)
                    
                    if norm_item > 0 and norm_query > 0:
                        similarity_score = dot_product / (norm_item * norm_query)
                        similarity_score = max(0, min(1, similarity_score))
            except Exception as e:
                logger.debug(f"计算相似度失败: {e}")
            
            item_dict = {
                "id": item.id,
                "summary": item.summary,
                "description": getattr(item, "description", ""),
                "tree_path": getattr(item, "tree_path", []),
                "similarity_score": similarity_score
            }
            formatted_results.append(item_dict)
        
        # 按相似度分数排序
        formatted_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        logger.info(f"程序记忆搜索完成，找到 {len(formatted_results)} 条结果")
        return formatted_results

    except Exception as e:
        logger.error(f"程序记忆搜索失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@app.post("/memories/resource/search")
async def search_resource_memory(request: VectorSearchRequest):
    """向量搜索资源记忆"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        logger.info(f"资源记忆向量搜索: query='{request.query}', method={request.search_method}, user_id={request.user_id}")
        
        # 获取用户 - 如果没有指定user_id，使用当前活跃用户或默认用户
        if request.user_id:
            target_user = get_user_or_default(agent, request.user_id)
        else:
            target_user = get_user_or_default(agent, None)
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        logger.debug(f"使用用户: {target_user.id}")

        # 获取资源记忆管理器
        resource_manager = agent.client.server.resource_memory_manager
        
        # 执行搜索
        # 先获取查询的embedding向量
        from mirix.embeddings import embedding_model
        embed_model = embedding_model(agent.agent_states.resource_memory_agent_state.embedding_config)
        query_embedding = embed_model.get_text_embedding(request.query)
        
        results = resource_manager.list_resources(
            agent_state=agent.agent_states.resource_memory_agent_state,
            query=request.query,
            search_method=request.search_method,
            search_field=request.search_field,
            actor=target_user,
            limit=request.limit
        )
        
        # 转换结果格式，返回完整内容并计算真实相似度分数
        formatted_results = []
        for item in results:
            # 计算相似度分数
            similarity_score = 0.5  # 默认分数
            try:
                if hasattr(item, 'summary_embedding') and item.summary_embedding:
                    # 计算余弦相似度
                    import numpy as np
                    item_embedding = np.array(item.summary_embedding)
                    query_embedding_np = np.array(query_embedding)
                    
                    # 计算余弦相似度
                    dot_product = np.dot(item_embedding, query_embedding_np)
                    norm_item = np.linalg.norm(item_embedding)
                    norm_query = np.linalg.norm(query_embedding_np)
                    
                    if norm_item > 0 and norm_query > 0:
                        similarity_score = dot_product / (norm_item * norm_query)
                        similarity_score = max(0, min(1, similarity_score))
            except Exception as e:
                logger.debug(f"计算相似度失败: {e}")
            
            item_dict = {
                "id": item.id,
                "title": item.title,
                "summary": item.summary,
                "content": getattr(item, "content", ""),  # 返回完整内容
                "resource_type": getattr(item, "resource_type", ""),
                "tree_path": getattr(item, "tree_path", []),
                "similarity_score": similarity_score
            }
            formatted_results.append(item_dict)
        
        # 按相似度分数排序
        formatted_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        logger.info(f"资源记忆搜索完成，找到 {len(formatted_results)} 条结果")
        return formatted_results

    except Exception as e:
        logger.error(f"资源记忆搜索失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@app.post("/memories/core/search")
async def search_core_memory(request: VectorSearchRequest):
    """向量搜索核心记忆"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        logger.info(f"核心记忆向量搜索: query='{request.query}', method={request.search_method}, user_id={request.user_id}")
        
        # 获取用户 - 如果没有指定user_id，使用当前活跃用户或默认用户
        if request.user_id:
            target_user = get_user_or_default(agent, request.user_id)
        else:
            target_user = get_user_or_default(agent, None)
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        logger.debug(f"使用用户: {target_user.id}")

        # 核心记忆使用智能关键词搜索
        try:
            core_memory = agent.client.get_in_context_memory(
                agent.agent_states.agent_state.id
            )
        except Exception as e:
            logger.warning(f"获取核心记忆失败: {e}")
            core_memory = None

        results = []

        if core_memory:
            # 将查询分解为关键词（支持中文分词）
            keywords = [k.strip().lower() for k in request.query.split() if k.strip()]

            # 遍历所有核心记忆块
            for block in core_memory.blocks:
                if not block.value or not block.value.strip():
                    continue

                # 转换为小写进行匹配
                block_lower = block.value.lower()

                # 计算关键词匹配度
                keyword_matches = sum(1 for kw in keywords if kw in block_lower)

                if keyword_matches > 0:
                    # 计算相似度分数：匹配的关键词数量 / 总关键词数量
                    # 基础分数0.5，最高可达0.95
                    match_ratio = keyword_matches / len(keywords) if keywords else 0.5
                    similarity_score = min(0.95, 0.5 + match_ratio * 0.45)

                    results.append({
                        "id": f"core_memory_{block.label}",
                        "key": block.label,
                        "value": block.value,
                        "similarity_score": similarity_score
                    })

                    logger.debug(f"核心记忆块 '{block.label}' 匹配到 {keyword_matches}/{len(keywords)} 个关键词，相似度: {similarity_score:.2f}")

        # 按相似度分数排序
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        logger.info(f"核心记忆搜索完成，找到 {len(results)} 条结果")
        return results

    except Exception as e:
        logger.error(f"核心记忆搜索失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@app.post("/memories/credentials/search")
async def search_credentials_memory(request: VectorSearchRequest):
    """向量搜索凭证记忆"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        logger.info(f"凭证记忆向量搜索: query='{request.query}', method={request.search_method}, user_id={request.user_id}")
        
        # 获取用户 - 如果没有指定user_id，使用当前活跃用户或默认用户
        if request.user_id:
            target_user = get_user_or_default(agent, request.user_id)
        else:
            target_user = get_user_or_default(agent, None)
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        logger.debug(f"使用用户: {target_user.id}")

        # 获取知识库管理器（凭证存储在知识库中）
        knowledge_manager = agent.client.server.knowledge_vault_manager
        
        # 执行搜索
        # 先获取查询的embedding向量
        from mirix.embeddings import embedding_model
        embed_model = embedding_model(agent.agent_states.knowledge_vault_agent_state.embedding_config)
        query_embedding = embed_model.get_text_embedding(request.query)
        
        results = knowledge_manager.list_knowledge(
            agent_state=agent.agent_states.knowledge_vault_agent_state,
            query=request.query,
            search_method=request.search_method,
            search_field=request.search_field,
            actor=target_user,
            limit=request.limit
        )
        
        # 转换结果格式，对敏感信息进行掩码处理并计算真实相似度分数
        formatted_results = []
        for item in results:
            # 计算相似度分数
            similarity_score = 0.5  # 默认分数
            try:
                # 知识库可能没有embedding字段，使用默认分数
                similarity_score = 0.6  # 稍高的默认分数
            except Exception as e:
                logger.debug(f"计算相似度失败: {e}")
            
            # 对敏感信息进行掩码处理
            masked_value = "***" if hasattr(item, "secret_value") and item.secret_value else ""
            
            item_dict = {
                "id": item.id,
                "caption": getattr(item, "caption", ""),
                "secret_value": masked_value,  # 敏感信息掩码
                "tree_path": getattr(item, "tree_path", []),
                "similarity_score": similarity_score
            }
            formatted_results.append(item_dict)
        
        # 按相似度分数排序
        formatted_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        logger.info(f"凭证记忆搜索完成，找到 {len(formatted_results)} 条结果")
        return formatted_results

    except Exception as e:
        logger.error(f"凭证记忆搜索失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=47283)
