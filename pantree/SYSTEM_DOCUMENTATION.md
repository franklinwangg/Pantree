# Pantree Subscribe & Save System Documentation

## Overview

The Pantree Subscribe & Save system is a complete ML-powered recommendation engine for grocery subscription services. It analyzes customer purchase patterns and generates personalized Subscribe & Save recommendations.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│                  (React/Vue/etc - not included)                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      │ REST API / WebSocket
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                      API LAYER                                  │
│                   (FastAPI Server)                              │
│  • REST endpoints for synchronous requests                      │
│  • WebSocket for real-time streaming updates                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                   ORCHESTRATOR                                  │
│         (Coordinates all system components)                     │
└────┬──────┬──────┬──────┬──────┬────────────────────────────────┘
     │      │      │      │      │
     │      │      │      │      │
     ▼      ▼      ▼      ▼      ▼
  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
  │ S2 │ │ S3 │ │ S4 │ │ L  │ │ S5 │
  └────┘ └────┘ └────┘ └────┘ └────┘

  S2: Simulation Component
  S3: Vector DB Pipeline
  S4: Frequency Analyzer
  L:  Llama NIM Integration
  S5: Sagemaker Client
```

## Components

### 1. Configuration (`config/settings.py`)
- Centralized configuration management
- Environment variable support
- Service connectivity settings

### 2. Simulation Component (`simulation/`)

#### `purchase_simulator.py`
- Generates realistic purchase history from seed purchase
- Supports multiple customer archetypes
- Configurable time ranges and patterns

**Key Features:**
- Product categorization
- Archetype-specific shopping patterns
- Realistic date spacing and quantities
- Price and savings calculation

#### `streaming_service.py`
- Streams purchase data month-by-month
- Real-time updates to frontend
- Progress tracking

### 3. Vector DB Integration (`vectordb/`)

#### `db_client.py`
- Multi-backend support (Milvus, Qdrant, Mock)
- Vector storage and similarity search
- Customer profile embeddings

#### `embedding_service.py`
- Multiple embedding backends
- Product and pattern embeddings
- Customer profile creation

#### `data_pipeline.py`
- ETL pipeline for purchase data
- Batch processing
- Statistics calculation

### 4. Frequency Analysis (`frequency_analysis/`)

#### `analyze_customer_frequency.py` (Existing)
- Statistical frequency analysis
- Confidence scoring
- Trend detection
- Recency weighting

**Statistical Measures:**
- Standard deviation
- Coefficient of variation
- Consistency score
- Confidence score (0-100)

#### `llama_integration.py`
- AI-enhanced product analysis
- Related product discovery
- Smart categorization
- Subscription frequency suggestions

### 5. Recommendations (`recommendations/`)

#### `sagemaker_client.py`
- AWS Sagemaker integration
- ML model inference
- Batch prediction support
- Fallback heuristics

### 6. Orchestrator (`orchestrator.py`)
- Main coordination service
- End-to-end pipeline execution
- Component lifecycle management

### 7. API Layer (`api/server.py`)
- FastAPI REST endpoints
- WebSocket streaming
- CORS support
- Health checks

## Data Flow

### Complete Pipeline Flow

```
1. Seed Purchase (Frontend)
   ↓
2. Simulation Component
   • Generate 6 months of purchase history
   • Based on customer archetype
   ↓
3. Streaming Service
   • Stream data month-by-month to frontend
   • Real-time progress updates
   ↓
4. Vector DB Pipeline
   • Create embeddings from purchases
   • Initialize customer profiles
   • Store in Vector DB
   ↓
5. Frequency Analyzer
   • Calculate purchase statistics
   • Compute confidence scores
   • Identify patterns
   ↓
6. Llama NIM Enhancement (Optional)
   • Find related products
   • AI-powered categorization
   • Smart frequency suggestions
   ↓
7. Sagemaker Recommendations
   • Send high-confidence items to ML model
   • Get final recommendations
   • Calculate subscription details
   ↓
8. Results (Frontend)
   • Display recommendations
   • Show confidence scores
   • Suggest subscription frequencies
```

## API Endpoints

### REST API

#### `GET /`
Health check and status

#### `GET /health`
Service health status

#### `POST /api/v1/process`
Process seed purchase (synchronous)

**Request:**
```json
{
  "customer_id": "cust_001",
  "customer_name": "John Doe",
  "archetype": "health_conscious",
  "items": [
    {"name": "Bananas", "price": 1.99, "quantity": 1},
    {"name": "Chicken Breast", "price": 12.99, "quantity": 1}
  ],
  "simulation_months": 6
}
```

**Response:**
```json
{
  "customer_id": "cust_001",
  "recommendations": {
    "recommendations": [
      {
        "name": "Bananas",
        "confidence": 85.3,
        "count": 8,
        "avg_interval": 7.2,
        "subscription": {
          "frequency": "weekly",
          "interval_days": 7,
          "estimated_annual_savings": 5.18
        }
      }
    ]
  }
}
```

#### `GET /api/v1/archetypes`
Get available customer archetypes

#### `GET /api/v1/config`
Get system configuration

### WebSocket

#### `WS /ws/stream/{customer_id}`
Real-time streaming endpoint

**Message Types:**
- `started`: Processing started
- `monthly_update`: Monthly data update
- `completed`: Processing complete with results
- `error`: Error occurred

## Customer Archetypes

### 1. Health Conscious
- Shopping frequency: Every 8 days
- Focus: Organic, fresh produce, lean proteins
- Category weights: 30% produce, 25% protein

### 2. Busy Family
- Shopping frequency: Every 12 days
- Focus: Bulk purchases, snacks, convenience
- Category weights: 20% snacks, 20% protein

### 3. Budget Conscious
- Shopping frequency: Every 12 days
- Focus: Value, store brands, balanced
- Category weights: Evenly distributed

### 4. Single Professional
- Shopping frequency: Every 6 days
- Focus: Convenience, smaller quantities
- Category weights: 25% protein, frequent trips

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

**Required for Production:**
- `SAGEMAKER_ENDPOINT`: Your Sagemaker endpoint name
- `AWS_ACCESS_KEY_ID`: AWS credentials
- `AWS_SECRET_ACCESS_KEY`: AWS credentials

**Optional Enhancements:**
- `LLAMA_NIM_ENDPOINT`: Llama NIM endpoint (default: localhost:8001)
- `VECTORDB_HOST`: Vector DB host (default: localhost)

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Optional: Set up Vector DB

**Using Milvus:**
```bash
docker run -d --name milvus \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest
```

**Using Qdrant:**
```bash
docker run -d --name qdrant \
  -p 6333:6333 \
  qdrant/qdrant
```

### 4. Optional: Set up Llama NIM

```bash
docker run -d --name llama-nim \
  -p 8001:8000 \
  nvcr.io/nvidia/nim/meta/llama-3.1-8b-instruct
```

### 5. Start API Server

```bash
python api/server.py
```

Or using uvicorn directly:
```bash
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

## Usage Examples

### Running the Complete Demo

```bash
python orchestrator.py
```

### Testing Individual Components

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
```

### Using the API

```bash
# Health check
curl http://localhost:8000/health

# Get archetypes
curl http://localhost:8000/api/v1/archetypes

# Process seed purchase
curl -X POST http://localhost:8000/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "test_001",
    "items": [
      {"name": "Bananas", "price": 1.99},
      {"name": "Milk", "price": 5.49}
    ]
  }'
```

## Frontend Integration

### REST API Integration

```javascript
const response = await fetch('http://localhost:8000/api/v1/process', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    customer_id: 'cust_001',
    items: [
      {name: 'Bananas', price: 1.99},
      {name: 'Milk', price: 5.49}
    ]
  })
});

const results = await response.json();
console.log('Recommendations:', results.recommendations);
```

### WebSocket Integration

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
  const message = JSON.parse(event.data);

  switch(message.type) {
    case 'started':
      console.log('Processing started');
      break;
    case 'monthly_update':
      console.log('Month:', message.data.month_display);
      updateProgress(message.data.progress);
      break;
    case 'completed':
      console.log('Recommendations:', message.data.recommendations);
      break;
    case 'error':
      console.error('Error:', message.error);
      break;
  }
};
```

## Production Deployment

### Recommended Setup

1. **API Server**: Deploy on AWS ECS/EKS or similar
2. **Vector DB**: Use managed Milvus or Qdrant cloud
3. **Llama NIM**: Deploy on GPU instances
4. **Sagemaker**: Use existing ML endpoints

### Environment Variables for Production

```bash
# Use production Vector DB
VECTORDB_HOST=production-vectordb.example.com
VECTORDB_PORT=19530

# Use production Llama NIM
LLAMA_NIM_ENDPOINT=https://llama-nim.example.com
LLAMA_NIM_API_KEY=your-production-api-key

# Use production Sagemaker
SAGEMAKER_ENDPOINT=prod-subscribe-save-endpoint
AWS_REGION=us-west-2
```

### Scaling Considerations

- **Horizontal scaling**: Run multiple API server instances behind load balancer
- **Vector DB**: Use clustered deployment for high availability
- **Caching**: Add Redis for frequently accessed data
- **Rate limiting**: Implement API rate limiting for production

## Troubleshooting

### Common Issues

**Issue**: Vector DB connection fails
- **Solution**: Check if Vector DB is running, verify host/port, use mock mode for testing

**Issue**: Llama NIM timeout
- **Solution**: Increase timeout, check endpoint availability, disable Llama if not needed

**Issue**: Sagemaker permission denied
- **Solution**: Verify AWS credentials and IAM permissions

### Debug Mode

Enable debug logging:
```bash
DEBUG=true python api/server.py
```

## Future Enhancements

See `analyze_customer_frequency.py:6-12` for ML enhancement roadmap:
- Time series forecasting (ARIMA, Prophet, LSTM)
- Classification models for purchase likelihood
- Collaborative filtering
- Survival analysis for churn prediction

## License

Copyright © 2025 Pantree

## Support

For issues and questions, please open a GitHub issue or contact the development team.
