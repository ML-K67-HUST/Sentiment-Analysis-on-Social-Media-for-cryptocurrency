# 📁 Project Structure

Clean and organized directory structure for the Cryptocurrency Sentiment Analysis System.

## Root Directory

```
Sentiment-Analysis-on-Social-Media-for-cryptocurrency/
├── README.md                   # Main project documentation
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── docker-compose.yaml         # Docker orchestration (all services)
├── Makefile                    # Helper commands
│
├── airflow/                    # Airflow service
│   ├── dags/                   # DAG definitions
│   │   ├── projects/           # Main project DAGs
│   │   │   └── cmc_news_1h.py  # CoinMarketCap crawler
│   │   ├── common/             # Shared utilities
│   │   ├── constants/          # Configuration constants
│   │   ├── crawler/            # Crawler modules
│   │   ├── database/           # DB connections
│   │   ├── services/           # Business logic
│   │   └── utils/              # Helper functions
│   ├── Dockerfile              # Airflow container config
│   └── docker-compose.yaml     # Standalone Airflow setup (legacy)
│
├── backend/                    # Backend API service
│   ├── config.py               # Centralized configuration
│   ├── consumer.py             # Kafka consumer
│   ├── data_constructor.py     # Dataset builder
│   ├── LLM/                    # LLM integration
│   │   └── sentiment_agent.py  # Gemini/Together AI
│   ├── ML/                     # Machine learning
│   │   └── push_training.py    # Model training
│   ├── services/               # API endpoints
│   │   ├── api.py              # Main API router
│   │   ├── chart_api.py        # Chart data endpoints
│   │   ├── cmc_api.py          # CoinMarketCap API
│   │   ├── ml_api.py           # ML prediction API
│   │   ├── sentiment_api.py    # Sentiment analysis API
│   │   └── twitter_api.py      # Twitter data API
│   ├── database/               # Database connections
│   │   └── mongodb.py          # MongoDB client
│   ├── notebook/               # Jupyter notebooks (dev)
│   ├── Dockerfile              # Backend container config
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # Frontend service
│   ├── main.html               # Main page
│   ├── server.js               # Express server
│   ├── chart.js                # Chart visualization
│   ├── news.js                 # News display
│   ├── status_btc.js           # Bitcoin status widget
│   ├── status_ml.js            # ML prediction widget
│   ├── status_positive.js      # Sentiment widget
│   ├── style/                  # CSS and assets
│   │   ├── main.css            # Main stylesheet
│   │   └── assets/             # Images, icons, SVGs
│   ├── package.json            # Node.js dependencies
│   └── node_modules/           # Installed packages (gitignored)
│
├── kafka/                      # Kafka service (standalone)
│   ├── consumer.py             # Test consumer
│   ├── producer.py             # Test producer
│   └── docker-compose.yml      # Standalone Kafka setup (legacy)
│
├── mlflow/                     # MLflow service (standalone)
│   ├── docker-compose.yaml     # Standalone MLflow setup (legacy)
│   ├── mlflow/                 # MLflow configs
│   ├── minio/                  # MinIO bucket setup
│   ├── postgres/               # PostgreSQL init scripts
│   └── test_experiment/        # MLflow experiments (dev)
│
├── scripts/                    # Helper scripts
│   ├── start-all.sh            # Start all services
│   ├── stop-all.sh             # Stop all services
│   ├── restart-all.sh          # Restart all services
│   └── quick-start.sh          # Interactive setup wizard
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md         # System architecture
│   ├── SETUP.md                # Setup guide
│   ├── API.md                  # API reference
│   ├── TROUBLESHOOTING.md      # Common issues
│   ├── CONTRIBUTING.md         # Contributing guide
│   ├── PROJECT_STRUCTURE.md    # This file
│   ├── ENV_TEMPLATES.md        # Environment templates
│   ├── VIETNAMESE_SUMMARY.md   # Vietnamese docs
│   └── archive/                # Historical documentation
│       ├── PROJECT_ANALYSIS.md
│       ├── REFACTORING_SUMMARY.md
│       ├── GEMINI_MIGRATION.md
│       ├── KAFKA_FIX.md
│       └── ...
│
├── asset/                      # Static assets (screenshots)
│   ├── airflow_dag.png
│   ├── airflow_home.png
│   ├── docker_images.png
│   └── ...
│
└── logs/                       # Application logs (gitignored)
    └── frontend.log
```

---

## Service Details

### Airflow (`airflow/`)

**Purpose**: Workflow orchestration and scheduling

**Key Files:**
- `dags/projects/cmc_news_1h.py` - Main DAG for news crawling
- `dags/common/` - Shared utilities (Twitter, processors)
- `dags/database/` - Kafka and MongoDB connectors

**Environment:**
- Python 3.10
- Apache Airflow 2.7.2
- CeleryExecutor with Redis

---

### Backend (`backend/`)

**Purpose**: REST API for data access and ML predictions

**Key Files:**
- `config.py` - Centralized environment config
- `services/api.py` - Main FastAPI application
- `LLM/sentiment_agent.py` - LLM integration (Gemini/Together)
- `ML/push_training.py` - Model training pipeline

**Environment:**
- Python 3.10
- FastAPI
- PyMongo, kafka-python
- scikit-learn, pandas

**Endpoints:** See [API.md](./API.md)

---

### Frontend (`frontend/`)

**Purpose**: Web dashboard for visualization

**Key Files:**
- `server.js` - Express server
- `main.html` - Main dashboard
- `chart.js` - Chart.js integration
- `style/main.css` - Custom styles

**Environment:**
- Node.js 16+
- Express
- Chart.js

**URL:** http://localhost:3000

---

### Scripts (`scripts/`)

**Purpose**: Automation and convenience

| Script | Description |
|--------|-------------|
| `start-all.sh` | Start all Docker services + frontend |
| `stop-all.sh` | Stop all services (with --clean option) |
| `restart-all.sh` | Restart all services |
| `quick-start.sh` | Interactive setup wizard |

**Usage:**
```bash
./scripts/start-all.sh
./scripts/stop-all.sh --clean
```

---

### Documentation (`docs/`)

**Purpose**: Project documentation

| File | Description |
|------|-------------|
| `ARCHITECTURE.md` | System design & components |
| `SETUP.md` | Installation & configuration |
| `API.md` | REST API reference |
| `TROUBLESHOOTING.md` | Common issues & solutions |
| `CONTRIBUTING.md` | Contribution guidelines |
| `PROJECT_STRUCTURE.md` | This file |
| `ENV_TEMPLATES.md` | Environment variable templates |
| `VIETNAMESE_SUMMARY.md` | Vietnamese documentation |

**Archive:** Historical documentation in `docs/archive/`

---

## Configuration Files

### Docker

- **`docker-compose.yaml`** (root) - Main orchestration file for ALL services
- **`airflow/docker-compose.yaml`** - Standalone Airflow (legacy)
- **`kafka/docker-compose.yml`** - Standalone Kafka (legacy)
- **`mlflow/docker-compose.yaml`** - Standalone MLflow (legacy)

> ⚠️ **Use root `docker-compose.yaml` for production**

### Environment

- **`.env.example`** - Template with all required variables
- **`.env`** - Your actual config (gitignored)

**Required Variables:**
```bash
GEMINI_API_KEY=...
COINRANKING_API_KEY=...
LLM_PROVIDER=gemini
MONGODB_CONNECTION_STRING=mongodb://mongodb:27017
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

### Python Dependencies

- **`backend/requirements.txt`** - Backend Python packages
- **`airflow/dags/requirements.txt`** - Airflow DAG dependencies

### JavaScript Dependencies

- **`frontend/package.json`** - Frontend Node.js packages

---

## Data Flow

```
1. Data Collection:
   Twitter/CoinMarketCap → Airflow DAGs → Kafka Topics

2. Data Storage:
   Kafka → Backend Consumer → MongoDB

3. Data Labeling:
   MongoDB → Airflow DAG → Gemini API → MongoDB (labeled)

4. Model Training:
   MongoDB → Data Constructor → MLflow → Trained Models

5. Prediction:
   Frontend → Backend API → ML Model → Frontend Display
```

---

## Important Notes

### Gitignored Directories

These directories are not tracked by git:

- `__pycache__/` - Python bytecode
- `node_modules/` - Node.js packages
- `logs/` - Application logs
- `backend/notebook/` - Development notebooks
- `mlruns/` - MLflow experiment data
- `kafka-data/` - Kafka data files

### Standalone Services

The following directories contain standalone Docker Compose files for individual services (legacy):

- `airflow/docker-compose.yaml`
- `kafka/docker-compose.yml`
- `mlflow/docker-compose.yaml`
- `backend/docker-compose.yaml`

> These are kept for reference but **NOT USED** in production. Use root `docker-compose.yaml` instead.

### Scripts Execution

All scripts in `scripts/` should be executable:

```bash
chmod +x scripts/*.sh
```

---

## Clean Architecture Principles

This project follows clean architecture:

1. **Separation of Concerns**: Each service has a clear responsibility
2. **Dependency Injection**: Configuration via environment variables
3. **Modular Design**: Reusable components in `common/` and `utils/`
4. **Documentation**: Comprehensive docs in `docs/`
5. **Testing**: Unit tests (future) in `tests/`

---

## Future Improvements

- [ ] Move legacy standalone Docker Compose files to `legacy/`
- [ ] Add `tests/` directory for unit/integration tests
- [ ] Add `migrations/` for database schema changes
- [ ] Add `configs/` for service-specific configs
- [ ] Add GitHub Actions workflows in `.github/workflows/`

---

For more details, see individual documentation files in `docs/`.

