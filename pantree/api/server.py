"""
API Server - FastAPI server for Subscribe & Save system.

Provides REST API and WebSocket endpoints for frontend communication.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
from datetime import datetime

from orchestrator import SubscribeSaveOrchestrator
from config.settings import config

# Initialize FastAPI app
app = FastAPI(
    title="Pantree Subscribe & Save API",
    version="1.0.0",
    description="API for grocery Subscribe & Save recommendations",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = None


# Pydantic models
class SeedItem(BaseModel):
    """Seed purchase item."""
    name: str
    price: float
    quantity: Optional[int] = 1


class SeedPurchaseRequest(BaseModel):
    """Request to process a seed purchase."""
    customer_id: str
    customer_name: Optional[str] = "Customer"
    archetype: Optional[str] = "health_conscious"
    items: List[SeedItem]
    simulation_months: Optional[int] = 6


class StatusResponse(BaseModel):
    """API status response."""
    status: str
    version: str
    timestamp: str
    services: Dict[str, bool]


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global orchestrator

    print("\n" + "="*60)
    print("Starting Pantree Subscribe & Save API")
    print("="*60)

    config.print_config()

    orchestrator = SubscribeSaveOrchestrator(
        simulation_months=config.SIMULATION_MONTHS,
        stream_delay=config.SIMULATION_STREAM_DELAY,
        enable_llama=bool(config.LLAMA_NIM_ENDPOINT),
        enable_sagemaker=bool(config.SAGEMAKER_ENDPOINT),
    )

    print("\n✓ API Server Ready")
    print(f"  Listening on {config.API_HOST}:{config.API_PORT}")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global orchestrator

    if orchestrator:
        orchestrator.cleanup()

    print("\n✓ API Server Shutdown Complete\n")


@app.get("/", response_model=StatusResponse)
async def root():
    """API root endpoint."""
    return StatusResponse(
        status="online",
        version=config.VERSION,
        timestamp=datetime.now().isoformat(),
        services={
            "simulation": True,
            "vectordb": True,
            "frequency_analysis": True,
            "llama_nim": orchestrator.enable_llama if orchestrator else False,
            "sagemaker": orchestrator.enable_sagemaker if orchestrator else False,
        }
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/v1/process")
async def process_seed_purchase(request: SeedPurchaseRequest):
    """
    Process a seed purchase and generate recommendations.

    This is a synchronous endpoint that returns all results at once.
    For streaming updates, use the WebSocket endpoint.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        # Convert Pydantic models to dicts
        seed_items = [item.dict() for item in request.items]

        # Process
        results = await orchestrator.process_seed_purchase(
            seed_items=seed_items,
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            archetype=request.archetype,
        )

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.websocket("/ws/stream/{customer_id}")
async def websocket_stream(websocket: WebSocket, customer_id: str):
    """
    WebSocket endpoint for streaming recommendations.

    Provides real-time updates as data is processed:
    1. Simulation progress (month by month)
    2. Vector DB initialization
    3. Frequency analysis
    4. Final recommendations
    """
    await websocket.accept()

    try:
        # Receive seed purchase data
        data = await websocket.receive_json()

        seed_items = data.get("items", [])
        customer_name = data.get("customer_name", "Customer")
        archetype = data.get("archetype", "health_conscious")

        # Send acknowledgment
        await websocket.send_json({
            "type": "started",
            "customer_id": customer_id,
            "timestamp": datetime.now().isoformat(),
        })

        # Define streaming callback
        async def stream_callback(month_data):
            """Send monthly updates to frontend."""
            await websocket.send_json({
                "type": "monthly_update",
                "data": month_data,
            })

        # Process with streaming
        results = await orchestrator.process_seed_purchase(
            seed_items=seed_items,
            customer_id=customer_id,
            customer_name=customer_name,
            archetype=archetype,
            streaming_callback=stream_callback,
        )

        # Send final results
        await websocket.send_json({
            "type": "completed",
            "data": results,
        })

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for customer {customer_id}")

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    finally:
        await websocket.close()


@app.get("/api/v1/archetypes")
async def get_archetypes():
    """Get available customer archetypes."""
    return {
        "archetypes": [
            {
                "id": "health_conscious",
                "name": "Health Conscious",
                "description": "Focuses on organic and fresh foods, meal preparation oriented",
            },
            {
                "id": "busy_family",
                "name": "Busy Family",
                "description": "Buys in bulk for family needs, higher proportion of snacks",
            },
            {
                "id": "budget_conscious",
                "name": "Budget Conscious",
                "description": "Focuses on value and store brands, balanced purchases",
            },
            {
                "id": "single_professional",
                "name": "Single Professional",
                "description": "Shops frequently with smaller quantities, convenience focused",
            },
        ]
    }


@app.get("/api/v1/config")
async def get_config():
    """Get public configuration information."""
    return {
        "simulation_months": config.SIMULATION_MONTHS,
        "freq_min_purchases": config.FREQ_MIN_PURCHASES,
        "freq_min_confidence": config.FREQ_MIN_CONFIDENCE,
        "llama_enabled": orchestrator.enable_llama if orchestrator else False,
        "sagemaker_enabled": orchestrator.enable_sagemaker if orchestrator else False,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level="info",
    )
