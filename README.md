<!-- # RAG Application for Documents

A Retrieval-Augmented Generation (RAG) application that combines document retrieval with AI-generated responses to provide accurate, context-aware answers based on your specific document collection.

## Requiements
- Python 3.11 

### Install Dependencies 

```bash
sudo apt update
sudo apt install libpq-dev gcc python3-dev
```

#### Install python using Miniconda 

1) Download and install MiniConda from [here](https://www.anaconda.com/docs/getting-started/miniconda/install#quickstart-install-instructions)
2) Create a new environment using following command:
```bash 
$ conda create -n mini-rag-app python=3.11
```
3) Acrivate the environment:
```bash
$ conda activate mini-rag-app
```

### (Optional) Setup you command line interface for better readability
```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

## Installation 

### Install the required packages

```bash
$ pip install -r requirments.txt
```

### Setup the environment variable
```bash 
$ cp .env.example .env
```

Set your environment variable in the `env` file like `OPENAI_API_KEY` value.

## Run Docker Compose Services

```bash
$ cd docker 
$ cp .env.example .env

```
- Update `.env` with your credentials


## Run the FastAPI server
```bash 
$ uvicorn main:app --reload 0.0.0.0 ---port 5000
```

Download Postman from [https://www.postman.com/downloads/].  
Download the Postman collection from [/assets/mini-rag-app.postman_collection.json](/assets/mini-rag-app.postman_collection.json).
 -->

# RAG Application for Documents

A Retrieval-Augmented Generation (RAG) application that combines document retrieval with AI-generated responses to provide accurate, context-aware answers based on your specific document collection.

## 🌟 Features

- **Multi-Language Support**: Full support for English and Arabic languages
- **Multiple LLM Providers**: Integration with OpenAI and Cohere
- **Vector Search**: High-performance semantic search capabilities
- **Document Processing**: Intelligent chunking and embedding storage
- **RESTful API**: FastAPI-based backend with comprehensive endpoints
- **Project Management**: Organize documents into projects
- **Docker Support**: Containerized services for easy deployment

## 🏗️ Architecture

This application follows a clean architecture with separation of concerns:

```
mini-rag-app/
├── README.md
├── docker/
│   ├── docker-compose.yml       # Docker services configuration
│   └── mongodb/                 # Legacy MongoDB data (migrated to PostgreSQL)
│
└── src/
    ├── main.py                  # FastAPI application entry point
    │
    ├── controllers/             # Business logic layer
    │   ├── BaseController.py    # Base controller with common functionality
    │   ├── DataController.py    # Data management operations
    │   ├── NLPController.py     # NLP and LLM operations
    │   ├── ProcessController.py # Document processing logic
    │   └── ProjectController.py # Project management
    │
    ├── models/                  # Data models and schemas
    │   ├── AssetModel.py        # Document/file asset model
    │   ├── BaseDataModel.py     # Base model with common fields
    │   ├── ChunkModel.py        # Document chunk model
    │   ├── ProjectModel.py      # Project organization model
    │   ├── db_schemas/          # Database schema definitions
    │   └── enums/               # Enumerations and constants
    │
    ├── routes/                  # API endpoints
    │   ├── base.py              # Base/health endpoints
    │   ├── data.py              # Data management endpoints
    │   ├── nlp.py               # NLP/query endpoints
    │   └── schemas/             # Request/response schemas
    │
    ├── stores/                  # External service integrations
    │   ├── llm/                 # LLM provider implementations
    │   │   ├── openai/          # OpenAI integration
    │   │   └── cohere/          # Cohere integration
    │   └── vectordb/            # Vector database clients
    │
    ├── helpers/                 # Utility functions
    │   └── config.py            # Configuration management
    │
    ├── assets/                  # Static assets and data
    │   ├── database/            # Database files/backups
    │   ├── files/               # Uploaded documents
    │   └── mini-rag-app.postman_collection.json
    │
    └── requirements.txt         # Python dependencies
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL with pgvector extension
- **Vector Storage**: pgvector (integrated with PostgreSQL) and first vesion i use Qdrant with MongoDB

### AI/ML
- **LLM Providers**: 
  - OpenAI (GPT models)
  - Cohere (Command models)
- **Embeddings**: Support for multiple embedding models
- **Languages**: English and Arabic

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Services**:
  - PostgreSQL with pgvector extension
  - FastAPI application server

## 💾 Database Evolution

### Phase 1: MongoDB (Initial Implementation)
Initially, the application was built using MongoDB for storing documents and chunks. This provided:
- Flexible schema for document storage
- Easy to get started with
- Good for initial prototyping

### Phase 2: PostgreSQL + pgvector (Current)
The application was migrated to PostgreSQL with the **pgvector extension**, which provides:
- **Unified Storage**: Both data and vector embeddings in a single database
- **Native Vector Operations**: pgvector extension adds vector similarity search capabilities directly in PostgreSQL
- **ACID Compliance**: Better data integrity and transaction support
- **Simplified Architecture**: No need for separate vector database service
- **Cost Efficiency**: Reduced infrastructure complexity
- **Better Performance**: Optimized queries combining relational and vector operations

The pgvector extension enables:
- Storing embeddings as native vector types
- Efficient similarity search using indexes
- Combining vector search with traditional SQL queries
- Cosine similarity

## 📋 Requirements

- Python 3.11
- Docker & Docker Compose
- PostgreSQL 15+ with pgvector extension

## 🚀 Installation

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install libpq-dev gcc python3-dev
```

### 2. Setup Python Environment using Miniconda

1. Download and install MiniConda from [here](https://www.anaconda.com/docs/getting-started/miniconda/install#quickstart-install-instructions)

2. Create a new environment:
```bash
conda create -n mini-rag-app python=3.11
```

3. Activate the environment:
```bash
conda activate mini-rag-app
```

### 3. (Optional) Setup CLI for Better Readability

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

### 4. Install Python Dependencies

```bash
cd src
pip install -r requirements.txt
```

### 5. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file and set your configuration:

```env
# LLM Provider API Keys
OPENAI_API_KEY=your_openai_api_key_here
COHERE_API_KEY=your_cohere_api_key_here

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=mini_rag_app
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Application Settings
DEFAULT_LANGUAGE=en  # en or ar
DEFAULT_LLM_PROVIDER=openai  # openai or cohere
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

## 🐳 Docker Services Setup

### 1. Configure Docker Environment

```bash
cd docker
cp .env.example .env
```

Update `docker/.env` with your credentials.

### 2. Start Docker Services

```bash
docker-compose up -d
```

This will start:
- **PostgreSQL with pgvector extension** for unified data and vector storage
- All necessary database services

## 🎯 Running the Application

Start the FastAPI server:

```bash
cd src
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

The API will be available at: `http://localhost:5000`

API Documentation: `http://localhost:5000/docs`

## 📮 API Testing with Postman

1. Download Postman from [https://www.postman.com/downloads/](https://www.postman.com/downloads/)
2. Import the Postman collection: `src/assets/mini-rag-app.postman_collection.json`
3. Start testing the API endpoints

## 🔧 Core Components

### Controllers

The application uses a controller-based architecture:

- **BaseController**: Provides common functionality and utilities for all controllers
- **ProjectController**: Manages project creation, updates, and organization
- **DataController**: Handles document upload, storage, and management
- **ProcessController**: Processes documents into chunks and generates embeddings
- **NLPController**: Handles query processing and LLM response generation

### Models

Data models define the structure of stored information:

- **BaseDataModel**: Base model with common fields (id, timestamps, metadata)
- **ProjectModel**: Project organization and settings
- **AssetModel**: Uploaded documents and files
- **ChunkModel**: Processed document chunks with vector embeddings (stored in PostgreSQL)
- **Enums**: Type-safe constants for languages, providers, document types, etc.
- **db_schemas**: PostgreSQL schema definitions for tables with vector columns

### Routes

RESTful API endpoints organized by functionality:

- **Base Routes**: Health checks and system information
- **Data Routes**: Document upload and management endpoints
- **NLP Routes**: Query submission and response generation
- **Schemas**: Pydantic models for request/response validation

### Stores

Integration layer for external services:

- **LLM Store**: 
  - OpenAI provider implementation
  - Cohere provider implementation
  - Unified interface for prompt templates and generation
  
- **VectorDB Store**: 
  - PostgreSQL pgvector client implementation
  - Vector similarity search using pgvector operations
  - Embedding storage and retrieval with native vector types
  - Support for different distance metrics (cosine, L2, inner product)

### Helpers

Utility functions and configuration:

- **config.py**: Centralized configuration management from environment variables
- Helper functions for common operations

## 🤖 LLM Provider System

The application supports multiple LLM providers through a unified interface in `stores/llm/`:

### OpenAI Provider
- Support for GPT-3.5, GPT-4, and newer models
- Custom prompt templates for RAG
- Streaming support

### Cohere Provider
- Support for Command and Command-Light models
- Multilingual capabilities optimized for English and Arabic
- Efficient for RAG use cases

Each provider includes:
- **System Prompt**: Defines AI behavior and capabilities
- **Document Prompt**: Formats retrieved document context
- **Footer Prompt**: Provides response guidelines and constraints

## 🌍 Multi-Language Support

Native support for both English and Arabic:
- Language-specific prompt templates
- Appropriate tokenization and embedding
- RTL (Right-to-Left) text handling for Arabic
- Language detection and routing

## 📊 Data Flow

### Document Ingestion Flow

1. **Upload**: User uploads document via `/data` endpoints
2. **Storage**: Document stored in PostgreSQL with metadata
3. **Processing**: ProcessController chunks document based on configuration
4. **Embedding**: Text chunks converted to vector embeddings
5. **Indexing**: Chunks and embeddings stored together in PostgreSQL using pgvector's native vector type

### Query Processing Flow

1. **Query**: User submits natural language query via `/nlp` endpoints
2. **Embedding**: Query converted to vector embedding
3. **Retrieval**: pgvector similarity search finds relevant chunks using vector operations
4. **Context Assembly**: Top-k chunks assembled with metadata
5. **Generation**: LLM generates response using retrieved context
6. **Response**: Answer returned with source citations

## 🧪 Development

### Project Structure Best Practices

- **Controllers**: Keep business logic focused and testable
- **Models**: Use Pydantic for validation and MongoDB for persistence
- **Routes**: Thin routing layer, delegate to controllers
- **Stores**: Abstract external services for easy swapping

### Adding a New LLM Provider

1. Create new provider class in `src/stores/llm/`
2. Implement standard interface (generate, embed, etc.)
3. Add provider templates (system, document, footer prompts)
4. Update configuration in `helpers/config.py`
5. Add enum entry in `models/enums/`

### Working with pgvector

The application uses PostgreSQL's pgvector extension for vector operations:

1. **Vector Columns**: Embeddings stored as `vector(dimension)` type
2. **Similarity Search**: Uses `<=>` (cosine), `<->` (L2), or `<#>` (inner product) operators
3. **Indexing**: Create IVFFlat or HNSW indexes for faster searches
4. **Hybrid Queries**: Combine vector similarity with traditional SQL filters

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- OpenAI for GPT models
- Cohere for multilingual AI capabilities
- FastAPI for the excellent web framework
- PostgreSQL team for the powerful database and pgvector extension

---

