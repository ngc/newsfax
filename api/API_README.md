# Newsfax Fact Checker API

A FastAPI-based fact-checking service that processes web URLs and returns fact-checked information with sources.

## Features

- **Async Processing**: Fact-checking runs in background to handle long-running operations
- **Real AI Fact-Checking**: Uses OpenAI GPT models + Tavily search for authentic fact verification
- **Intelligent Fallback**: Works in mock mode when API keys aren't available
- **SQLite Database**: Persistent storage for fact-check results and processing status
- **Polling-Based**: Clients poll the endpoint until processing is complete
- **Modular Architecture**: Clean separation between API, fact-checking logic, and database
- **Comprehensive Testing**: Full test suite with TDD approach + integration tests

## API Endpoint

### POST `/factcheck`

Fact-check a webpage URL.

**Request Body:**
```json
{
  "url": "https://example.com/article"
}
```

**Responses:**

#### 202 - Processing Started/In Progress
```json
{
  "message": "Fact checking started"
}
```
or
```json
{
  "message": "Fact checking in progress"
}
```

#### 200 - Processing Complete
```json
[
  {
    "text": "climate change",
    "truthfulness": "TRUE",
    "summary": "Climate change is well-established by scientific consensus.",
    "sources": [
      {
        "url": "https://www.nasa.gov/climate",
        "favicon": "https://www.nasa.gov/favicon.ico"
      },
      {
        "url": "https://www.noaa.gov/climate", 
        "favicon": "https://www.noaa.gov/favicon.ico"
      }
    ]
  }
]
```

#### 422 - Validation Error
Invalid request format.

## Workflow

1. **First Request**: Client sends URL → Server returns 202 and starts background processing
2. **Polling**: Client continues to poll same endpoint → Server returns 202 while processing
3. **Completion**: Processing finishes → Server returns 200 with fact-checked data
4. **Subsequent Requests**: Same URL returns cached 200 response with same data

## Database Schema

```sql
CREATE TABLE fact_checks (
    url TEXT PRIMARY KEY,
    checked_fact_json TEXT NULL,
    processed BOOLEAN NOT NULL DEFAULT FALSE
);
```

- `url`: The webpage URL being fact-checked
- `checked_fact_json`: JSON string of CheckedFact[] or NULL if not ready
- `processed`: Boolean to prevent duplicate processing workflows

## Data Types

### CheckedFact
```typescript
interface CheckedFact {
  text: string;
  truthfulness: "TRUE" | "FALSE" | "SOMEWHAT TRUE";
  summary: string;
  sources: Source[];
}
```

### Source
```typescript
interface Source {
  url: string;
  favicon: string;
}
```

## Installation & Setup

1. **Install dependencies with uv:**
   ```bash
   cd api
   # Activate virtual environment
   source .venv/bin/activate.fish  # For Fish shell
   # or
   source .venv/bin/activate       # For Bash/Zsh
   
   # Install dependencies
   uv sync --dev
   ```

2. **Configure API keys (for real fact checking):**
   ```bash
   # Copy the template and add your API keys
   cp env.template .env
   
   # Edit .env file to add your API keys:
   # OPENAI_API_KEY=your_openai_api_key_here
   # TAVILY_API_KEY=your_tavily_api_key_here
   ```
   
   **Note:** The API will work in mock mode without API keys, but for real fact-checking you need:
   - OpenAI API key from https://platform.openai.com/api-keys
   - Tavily API key from https://tavily.com/

3. **Run the server:**
   ```bash
   python hello.py
   ```
   or
   ```bash
   python run.py
   ```
   or
   ```bash
   uvicorn api:app --reload
   ```

4. **Test the setup:**
   ```bash
   # Run integration tests
   python test_integration.py
   
   # Run full test suite
   python run.py test
   ```

5. **Access API:**
   - Server: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - OpenAPI spec: http://localhost:8000/openapi.json

## Testing

### Run Tests
```bash
cd api
python -m pytest test_factcheck.py -v
```
or
```bash
python run.py test
```

### Test Structure
- `TestDatabaseOperations`: Direct database function testing
- `TestFactCheckEndpoint`: API endpoint behavior testing  
- `TestBackgroundProcessing`: Async processing workflow testing
- `TestIntegrationWorkflow`: End-to-end workflow testing

### Test Coverage
- ✅ Database initialization and operations
- ✅ Status code handling (200, 202, 422)
- ✅ Background task processing
- ✅ Complete polling workflow
- ✅ Data validation and serialization
- ✅ Error handling

## Example Usage

### Using curl

```bash
# Start fact-checking
curl -X POST "http://localhost:8000/factcheck" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/article"}'

# Response: {"message": "Fact checking started"}
# Status: 202

# Poll for completion
curl -X POST "http://localhost:8000/factcheck" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/article"}'

# Eventually returns facts with status 200
```

### Using Python

```python
import requests
import time

url = "http://localhost:8000/factcheck"
payload = {"url": "https://example.com/article"}

# Start processing
response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")

# Poll until complete
while response.status_code == 202:
    time.sleep(1)
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")

# Get results
facts = response.json()
print(f"Found {len(facts)} facts")
```

## Architecture

### Component Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    hello.py     │    │     api.py      │    │ fact_checker.py │
│   Entry Point   │───▶│   FastAPI App   │───▶│  AI Logic      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Database      │    │  External APIs  │
                       │   (SQLite)      │    │ OpenAI + Tavily │
                       └─────────────────┘    └─────────────────┘
```

### File Structure

- **`hello.py`** - Entry point that starts the FastAPI server
- **`api.py`** - Main FastAPI application with endpoints and database logic
- **`fact_checker.py`** - AI-powered fact checking using LangChain + Tavily
- **`test_factcheck.py`** - Comprehensive test suite
- **`test_integration.py`** - Integration tests for end-to-end functionality

### How It Works

1. **Content Extraction**: Uses Tavily API to extract clean text content from URLs
2. **Fact Extraction**: LangChain agent identifies factual statements in the content
3. **Fact Verification**: For each fact, searches for supporting/contradicting evidence
4. **Result Compilation**: Aggregates sources and determines truthfulness levels
5. **Database Storage**: Caches results to avoid re-processing the same URLs

### Async Design

- All external API calls run in thread pools to avoid blocking the FastAPI event loop
- Background tasks handle long-running fact-checking processes
- Clients poll the API until processing completes

## Development

### TDD Approach
This API was built using Test-Driven Development:

1. **Tests First**: Comprehensive test suite written before implementation
2. **Red-Green-Refactor**: Tests fail → Implementation → Tests pass → Refactor
3. **Mock External Dependencies**: AI and Tavily API calls are mocked in tests
4. **Isolated Testing**: Each test uses temporary database

### Real vs Mock Mode

- **Real Mode**: With API keys configured, uses actual OpenAI + Tavily APIs
- **Mock Mode**: Without API keys, returns predefined fact-checking results
- **Graceful Fallback**: Automatically switches to mock mode if APIs fail

### Future Enhancements
- Rate limiting and authentication
- Caching layer (Redis)
- Webhook notifications for completion
- Batch processing of multiple URLs
- Content extraction optimization
- Advanced fact verification algorithms 