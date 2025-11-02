# Pantree Subscribe & Save System

Complete ML-powered recommendation system for grocery subscription services.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (optional for demo)
```

### 3. Run Demo

```bash
# Complete end-to-end demo
python orchestrator.py
```

### 4. Start API Server

```bash
# Start the FastAPI server
python api/server.py

# Server will be available at http://localhost:8000
```

## What This System Does

The Pantree Subscribe & Save system analyzes customer purchase patterns and generates personalized subscription recommendations through a 5-step pipeline:

### Step 1: Frontend (Not Included)
Your frontend sends a seed purchase to the API

### Step 2: Simulation ✓
- Takes seed purchase items
- Generates 6 months of realistic purchase history
- Streams data month-by-month back to frontend in real-time

### Step 3: Vector DB Initialization ✓
- Transforms purchase data into embeddings
- Stores in Vector Database (Milvus/Qdrant)
- Creates customer purchase profiles

### Step 4: Frequency Analysis ✓
- Analyzes purchase frequency with statistical confidence
- Calculates consistency, trends, and recency
- Integrates with Llama NIM for AI-enhanced insights
- Identifies related products

### Step 5: Sagemaker Recommendations ✓
- Sends high-confidence items to AWS Sagemaker
- Gets ML-powered recommendations
- Returns results to frontend via API/WebSocket

## System Components

```
pantree/
├── config/                    # Configuration
│   └── settings.py           # Centralized settings
├── simulation/               # Step 2: Simulation
│   ├── purchase_simulator.py
│   └── streaming_service.py
├── vectordb/                 # Step 3: Vector DB
│   ├── db_client.py
│   ├── embedding_service.py
│   └── data_pipeline.py
├── frequency_analysis/       # Step 4: Frequency Analysis
│   ├── llama_integration.py  # Llama NIM integration
│   └── (uses analyze_customer_frequency.py)
├── recommendations/          # Step 5: Sagemaker
│   └── sagemaker_client.py
├── api/                      # API Layer
│   └── server.py            # FastAPI server
├── orchestrator.py           # Main coordinator
└── analyze_customer_frequency.py  # Existing frequency analyzer
```

## API Endpoints

### REST API

- `GET /` - Status and health
- `GET /health` - Health check
- `POST /api/v1/process` - Process seed purchase (synchronous)
- `GET /api/v1/archetypes` - Get customer archetypes
- `GET /api/v1/config` - Get configuration

### WebSocket

- `WS /ws/stream/{customer_id}` - Real-time streaming updates

## Example: Process Seed Purchase

### Using REST API

```bash
curl -X POST http://localhost:8000/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_001",
    "customer_name": "John Doe",
    "archetype": "health_conscious",
    "items": [
      {"name": "Bananas", "price": 1.99},
      {"name": "Chicken Breast", "price": 12.99},
      {"name": "Milk", "price": 5.49}
    ]
  }'
```

### Using WebSocket (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream/cust_001');

ws.onopen = () => {
  ws.send(JSON.stringify({
    items: [
      {name: 'Bananas', price: 1.99},
      {name: 'Milk', price: 5.49}
    ],
    archetype: 'health_conscious'
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  if (msg.type === 'monthly_update') {
    console.log(`Month: ${msg.data.month_display}`);
    console.log(`Progress: ${msg.data.progress.percentage}%`);
  } else if (msg.type === 'completed') {
    console.log('Recommendations:', msg.data.recommendations);
  }
};
```

## Customer Archetypes

1. **health_conscious** - Organic foods, fresh produce, meal prep
2. **busy_family** - Bulk purchases, snacks, convenience
3. **budget_conscious** - Value items, store brands
4. **single_professional** - Small quantities, frequent trips

## Configuration

### Minimal (Demo Mode)

No configuration needed! System works out-of-the-box with:
- Mock Vector DB
- TF-IDF embeddings
- Fallback recommendations

### Production Setup

Configure in `.env`:

```bash
# Vector DB (Milvus or Qdrant)
VECTORDB_HOST=your-vectordb-host
VECTORDB_PORT=19530

# Llama NIM (Optional)
LLAMA_NIM_ENDPOINT=https://your-llama-endpoint
LLAMA_NIM_API_KEY=your-api-key

# AWS Sagemaker (Required for ML recommendations)
SAGEMAKER_ENDPOINT=your-endpoint-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-2
```

## Optional: Set Up External Services

### Milvus Vector DB

```bash
docker run -d --name milvus \
  -p 19530:19530 \
  milvusdb/milvus:latest
```

### Llama NIM

```bash
docker run -d --name llama-nim \
  -p 8001:8000 \
  nvcr.io/nvidia/nim/meta/llama-3.1-8b-instruct
```

## Testing Components Individually

Each component can be tested standalone:

```bash
# Test simulation
python simulation/purchase_simulator.py

# Test streaming
python simulation/streaming_service.py

# Test Vector DB
python vectordb/db_client.py

# Test embeddings
python vectordb/embedding_service.py

# Test Llama integration
python frequency_analysis/llama_integration.py

# Test Sagemaker
python recommendations/sagemaker_client.py

# Test complete flow
python orchestrator.py
```

## Output Example

```
FINAL RECOMMENDATIONS
====================

1. Whole Milk
   Confidence: 92.1%
   Purchase Count: 10
   Avg Interval: 6.5 days
   Subscription: weekly (every 7 days)
   Est. Annual Savings: $14.15

2. Bananas
   Confidence: 85.3%
   Purchase Count: 8
   Avg Interval: 7.2 days
   Subscription: weekly (every 7 days)
   Est. Annual Savings: $5.18

3. Chicken Breast
   Confidence: 78.4%
   Purchase Count: 6
   Avg Interval: 14.8 days
   Subscription: bi-weekly (every 14 days)
   Est. Annual Savings: $16.89
```

## Frequency Analysis Features

The system includes advanced statistical analysis:

- **Confidence Score** (0-100): Overall recommendation confidence
- **Consistency Score**: How regular the purchase pattern is
- **Trend Analysis**: Detecting increasing/decreasing frequency
- **Recency Weighting**: Recent purchases weighted higher
- **Standard Deviation**: Variability in purchase intervals
- **Coefficient of Variation**: Normalized consistency measure

See `analyze_customer_frequency.py` for implementation details.

## Architecture Diagram

```
Frontend
   ↓
FastAPI Server (REST/WebSocket)
   ↓
Orchestrator
   ↓
┌─────────┬──────────┬────────────┬──────────────┐
↓         ↓          ↓            ↓              ↓
Simulator VectorDB  Frequency   Llama NIM   Sagemaker
          Pipeline  Analyzer
```

## Production Deployment

1. Deploy API server (Docker/ECS/EKS)
2. Set up managed Vector DB (Milvus Cloud/Qdrant Cloud)
3. Configure Sagemaker endpoints
4. Set environment variables
5. Enable HTTPS and authentication
6. Set up monitoring and logging

## Troubleshooting

**API won't start:**
- Check if port 8000 is available
- Verify Python dependencies installed

**Recommendations low quality:**
- Increase `SIMULATION_MONTHS` for more data
- Lower `FREQ_MIN_CONFIDENCE` threshold
- Enable Llama NIM for AI enhancement

**Performance issues:**
- Use production Vector DB instead of mock
- Enable caching
- Use sentence-transformers for better embeddings

## Documentation

- **Full Documentation**: `SYSTEM_DOCUMENTATION.md`
- **Dataset Info**: `DATASET_README.md`, `LARGE_DATASET_README.md`
- **Usage Guide**: `USAGE_GUIDE.md`

## Future Enhancements

Planned ML improvements (see `analyze_customer_frequency.py:6-12`):
- Time series forecasting (ARIMA, Prophet, LSTM)
- Purchase likelihood classification
- Collaborative filtering
- Churn prediction

## License

Copyright © 2025 Pantree

## Support

For issues, questions, or contributions, please contact the development team.
