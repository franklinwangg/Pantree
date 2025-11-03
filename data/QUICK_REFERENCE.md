# Quick Reference Card

## What Each Step Does

### Step 2: Simulation Component
**Input:** Seed purchase (items + customer archetype)
**Output:** 6 months of realistic purchase history
**Files:** `simulation/purchase_simulator.py`, `simulation/streaming_service.py`

```python
# Generate history
simulator = PurchaseSimulator()
history = simulator.generate_purchase_history(
    seed_items=[{"name": "Bananas", "price": 1.99}],
    archetype="health_conscious",
    months=6
)
```

### Step 3: Vector DB Pipeline
**Input:** Purchase history (receipts)
**Output:** Embeddings stored in Vector DB
**Files:** `vectordb/db_client.py`, `vectordb/embedding_service.py`, `vectordb/data_pipeline.py`

```python
# Initialize Vector DB
pipeline = DataPipeline(db_client, embedding_service)
stats = pipeline.initialize_from_simulation(receipts)
```

### Step 4: Frequency Analysis
**Input:** Purchase receipts
**Output:** Items with confidence scores and statistics
**Files:** `analyze_customer_frequency.py`, `frequency_analysis/llama_integration.py`

```python
# Analyze frequency
stats = calculate_item_statistics(dates, reference_date)
# Returns: confidence, consistency, trend, recency, etc.
```

### Step 5: Sagemaker Recommendations
**Input:** High-confidence items from frequency analysis
**Output:** ML-powered recommendations
**File:** `recommendations/sagemaker_client.py`

```python
# Get recommendations
rec_service = RecommendationService(sagemaker_client)
recs = rec_service.generate_recommendations(
    customer_id="cust_001",
    frequency_analysis=items
)
```

## Command Quick Reference

```bash
# Test system structure
python test_system.py

# Run complete demo
python orchestrator.py

# Start API server
python api/server.py

# Test individual components
python simulation/purchase_simulator.py
python vectordb/db_client.py
python frequency_analysis/llama_integration.py
python recommendations/sagemaker_client.py
```

## API Quick Reference

### REST Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_001",
    "items": [{"name": "Bananas", "price": 1.99}]
  }'
```

### WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream/cust_001');
ws.send(JSON.stringify({items: [...], archetype: "health_conscious"}));
ws.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  if (msg.type === 'monthly_update') { /* handle */ }
  if (msg.type === 'completed') { /* show results */ }
};
```

## Configuration Quick Reference

```bash
# Minimal (works out of box)
# No configuration needed

# Production
VECTORDB_HOST=your-vectordb
LLAMA_NIM_ENDPOINT=https://your-llama
SAGEMAKER_ENDPOINT=your-endpoint
AWS_ACCESS_KEY_ID=***
AWS_SECRET_ACCESS_KEY=***
```

## Customer Archetypes

- `health_conscious` - Organic, fresh, 8-day shopping cycle
- `busy_family` - Bulk, convenience, 12-day cycle
- `budget_conscious` - Value items, 12-day cycle
- `single_professional` - Small quantities, 6-day cycle

## File Locations

| Component | File |
|-----------|------|
| Config | `config/settings.py` |
| Simulation | `simulation/purchase_simulator.py` |
| Streaming | `simulation/streaming_service.py` |
| Vector DB | `vectordb/db_client.py` |
| Embeddings | `vectordb/embedding_service.py` |
| Data Pipeline | `vectordb/data_pipeline.py` |
| Frequency | `analyze_customer_frequency.py` |
| Llama NIM | `frequency_analysis/llama_integration.py` |
| Sagemaker | `recommendations/sagemaker_client.py` |
| Orchestrator | `orchestrator.py` |
| API Server | `api/server.py` |

## Documentation

| Document | Purpose |
|----------|---------|
| `README_SUBSCRIBE_SAVE.md` | Quick start guide |
| `SYSTEM_DOCUMENTATION.md` | Complete technical docs |
| `IMPLEMENTATION_SUMMARY.md` | Implementation overview |
| `QUICK_REFERENCE.md` | This file |
| `.env.example` | Configuration template |

## Troubleshooting

**Problem:** Dependencies missing
**Solution:** `pip install -r requirements.txt`

**Problem:** Vector DB connection fails
**Solution:** System auto-falls back to mock mode

**Problem:** Llama/Sagemaker unavailable
**Solution:** System uses fallback heuristics

**Problem:** Port 8000 in use
**Solution:** Set `API_PORT=8001` in .env

## Next Steps

1. ✓ System built and validated
2. → Install dependencies: `pip install -r requirements.txt`
3. → Run demo: `python orchestrator.py`
4. → Start API: `python api/server.py`
5. → Integrate with frontend
6. → Deploy to production
