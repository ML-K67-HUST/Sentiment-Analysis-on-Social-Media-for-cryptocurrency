# 🤝 Contributing to Sentiment Analysis System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community

---

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/Sentiment-Analysis-on-Social-Media-for-cryptocurrency.git
cd Sentiment-Analysis-on-Social-Media-for-cryptocurrency

# Add upstream remote
git remote add upstream https://github.com/ML-K67-HUST/Sentiment-Analysis-on-Social-Media-for-cryptocurrency.git
```

### 2. Set Up Development Environment

```bash
# Copy environment template
cp .env.example .env

# Add your API keys to .env

# Start services
docker-compose up -d

# Install frontend dependencies
cd frontend
npm install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding tests

---

## Development Workflow

### Project Structure

```
├── airflow/           # Airflow DAGs and configurations
│   └── dags/         # DAG definitions
├── backend/          # Backend API service
│   ├── LLM/         # LLM integration
│   ├── ML/          # Machine learning models
│   ├── services/    # API endpoints
│   └── database/    # Database connections
├── frontend/         # Frontend dashboard
│   ├── style/       # CSS and assets
│   └── *.js         # JavaScript files
├── docs/            # Documentation
├── scripts/         # Helper scripts
└── docker-compose.yaml  # Docker orchestration
```

### Making Changes

#### Backend Changes (Python/FastAPI)

1. **Edit code** in `backend/` directory
2. **Rebuild container:**
   ```bash
   docker-compose up -d --build backend-api
   ```
3. **Check logs:**
   ```bash
   docker logs -f sentiman_backend_api
   ```

#### Frontend Changes (Node.js)

1. **Edit code** in `frontend/` directory
2. **Restart server:**
   ```bash
   pkill -f "node server.js"
   cd frontend && node server.js &
   ```

#### Airflow DAG Changes

1. **Edit DAG** in `airflow/dags/`
2. **DAGs auto-reload** (no rebuild needed)
3. **Check for errors:**
   ```bash
   docker exec sentiman_airflow_webserver airflow dags list-import-errors
   ```

#### Docker Configuration Changes

1. **Edit** `docker-compose.yaml`
2. **Apply changes:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## Coding Standards

### Python (Backend)

Follow **PEP 8** style guide:

```python
# Good
def calculate_sentiment_score(text: str, model: str = "gemini") -> float:
    """
    Calculate sentiment score for given text.
    
    Args:
        text: Input text to analyze
        model: LLM model to use (default: "gemini")
        
    Returns:
        Sentiment score between -1.0 and 1.0
    """
    # Implementation
    pass


# Use type hints
def process_data(
    data: List[Dict[str, Any]], 
    threshold: float = 0.5
) -> Dict[str, int]:
    pass
```

**Key points:**
- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black formatter)
- Add docstrings for all functions
- Use type hints

### JavaScript (Frontend)

Follow **Airbnb JavaScript Style Guide**:

```javascript
// Good
const fetchChartData = async (symbol, timeframe = '24h') => {
  try {
    const response = await fetch(`/api/chart?symbol=${symbol}&timeframe=${timeframe}`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to fetch chart data:', error);
    throw error;
  }
};

// Use const/let, not var
// Use async/await over promises
// Add error handling
```

### Python Dependencies

Add new dependencies to `requirements.txt`:

```bash
# Add package
echo "new-package==1.0.0" >> backend/requirements.txt

# Sort alphabetically
sort -u backend/requirements.txt -o backend/requirements.txt
```

### JavaScript Dependencies

```bash
cd frontend
npm install --save new-package
```

---

## Testing

### Backend Testing

Create tests in `backend/tests/`:

```python
# backend/tests/test_sentiment_agent.py
import pytest
from backend.LLM.sentiment_agent import analyze_sentiment


def test_analyze_sentiment_positive():
    text = "Bitcoin is amazing!"
    result = analyze_sentiment(text)
    assert result["sentiment"] == "positive"
    assert 0 <= result["confidence"] <= 1


def test_analyze_sentiment_negative():
    text = "Bitcoin crashed badly"
    result = analyze_sentiment(text)
    assert result["sentiment"] == "negative"
```

Run tests:
```bash
docker exec sentiman_backend_api pytest tests/ -v
```

### Integration Testing

Test full workflow:
```bash
# 1. Trigger DAG
docker exec sentiman_airflow_webserver airflow dags trigger cmc_news_24h

# 2. Wait and check results
sleep 60

# 3. Verify data in MongoDB
docker exec sentiman_mongodb mongosh --eval "
  use twitter_crawler
  db.coinmarketcap_news.find().limit(1)
"
```

---

## Documentation

### Code Documentation

- **Add docstrings** to all functions
- **Add comments** for complex logic
- **Update README** if adding new features

### API Documentation

Update `docs/API.md` when adding new endpoints:

```markdown
#### `GET /new_endpoint/`

Description of the endpoint.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| param1    | str  | Yes      | Description |

**Example Request:**
\`\`\`bash
curl http://localhost:8000/new_endpoint/?param1=value
\`\`\`

**Response:**
\`\`\`json
{
  "result": "data"
}
\`\`\`
```

---

## Pull Request Process

### Before Submitting

1. **Sync with upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests:**
   ```bash
   # Backend tests
   docker exec sentiman_backend_api pytest

   # Check code style
   docker exec sentiman_backend_api black --check .
   docker exec sentiman_backend_api flake8 .
   ```

3. **Update documentation** if needed

4. **Commit with clear messages:**
   ```bash
   git commit -m "feat: Add new sentiment analysis model"
   # or
   git commit -m "fix: Resolve Kafka connection issue"
   ```

   **Commit message format:**
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance

### Submitting PR

1. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request** on GitHub

3. **Fill in PR template:**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   Describe how you tested the changes

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] All tests pass
   ```

### PR Review Process

1. **Wait for review** from maintainers
2. **Address feedback** if requested
3. **Rebase if needed:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   git push -f origin feature/your-feature-name
   ```
4. **Merge** - Maintainers will merge when approved

---

## Development Tips

### Hot Reload

Enable hot reload for faster development:

**Backend:**
```yaml
# docker-compose.yaml
backend-api:
  volumes:
    - ./backend:/app
  command: uvicorn main:app --reload --host 0.0.0.0
```

**Frontend:**
Use `nodemon`:
```bash
cd frontend
npm install -g nodemon
nodemon server.js
```

### Debugging

**Python debugger:**
```python
import pdb; pdb.set_trace()  # Add breakpoint
```

**View container logs:**
```bash
docker logs -f sentiman_backend_api
```

**Interactive shell:**
```bash
docker exec -it sentiman_backend_api bash
```

### Performance Profiling

```python
# Add to your code
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)
```

---

## Areas for Contribution

We welcome contributions in these areas:

### High Priority
- 🐛 Bug fixes (see GitHub issues)
- 📝 Documentation improvements
- ✅ Test coverage
- 🚀 Performance optimizations

### Feature Ideas
- 🔔 Real-time WebSocket notifications
- 📊 More ML models (LSTM, Transformer)
- 🌍 Multi-language support
- 📱 Mobile-responsive frontend
- 🔐 User authentication
- 📈 Advanced analytics dashboard
- 🤖 More social media platforms
- 🎨 UI/UX improvements

### Documentation Needs
- Video tutorials
- Architecture deep-dives
- Deployment guides (AWS, GCP, Azure)
- API examples in more languages

---

## Questions?

- **GitHub Issues**: https://github.com/ML-K67-HUST/Sentiment-Analysis-on-Social-Media-for-cryptocurrency/issues
- **Discussions**: https://github.com/ML-K67-HUST/Sentiment-Analysis-on-Social-Media-for-cryptocurrency/discussions

---

Thank you for contributing! 🎉

