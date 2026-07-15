# 🤖 RAG Chatbot - Retrieval Augmented Generation AI System

A production-style **Retrieval Augmented Generation (RAG) chatbot** built from scratch using **Python, FastAPI, Sentence Transformers, and Vector Database technologies**.

This project demonstrates how modern AI applications are engineered:

```text
Documents
    |
    ↓
Text Extraction
    |
    ↓
Intelligent Chunking
    |
    ↓
Embedding Generation
    |
    ↓
Vector Database
    |
    ↓
Semantic Search
    |
    ↓
LLM Response Generation
```

The objective is to build a complete enterprise-grade AI knowledge assistant similar to systems used for:

- Internal company knowledge search
- Document intelligence platforms
- AI assistants
- Customer support automation

---

# 🚀 Project Vision

Large Language Models (LLMs) do not have access to private organizational data.

RAG solves this limitation by combining:

- Document processing
- Text extraction
- Intelligent chunking
- Embedding generation
- Vector similarity search
- Large Language Models


Example:

### User Question

```
What is the company leave policy?
```

### RAG Pipeline

```
User Question

        ↓

Convert question into embedding

        ↓

Search relevant document chunks

        ↓

Retrieve matching context

        ↓

Send context + question to LLM

        ↓

Generate accurate answer
```

---

# 🏗️ System Architecture

```
                         Client

                           |
                           |

                        FastAPI

                           |

              Document Processing Layer

                           |

        +------------------+------------------+

        |                  |                  |

   File Storage        Parser Service     Chunking Service


                           |

                  Embedding Generation


                           |

                  Vector Database


                           |

                   Semantic Retrieval


                           |

                         LLM


                           |

                       Final Answer
```

---

# ✨ Implementation Roadmap

The project is developed incrementally following production engineering practices.

---

# ✅ Sprint 1 - Project Setup

## Objective

Create a scalable backend foundation.

## Implemented

- FastAPI project initialization
- Application entry point
- Modular folder structure
- Dependency management
- Virtual environment setup


## Architecture

```
app

├── main.py

├── api

├── services

├── models

├── schemas

└── core
```

---

# ✅ Sprint 2 - Document Upload

## Objective

Allow users to upload documents.

## Implemented

- File upload API
- File validation
- File type checking
- Unique file naming
- Storage service


Supported formats:

```
.pdf
.docx
.txt
```


## API Flow

```
Upload File

    ↓

Validate Extension

    ↓

Generate UUID

    ↓

Save File

    ↓

Return Metadata
```

---

# ✅ Sprint 3 - Document Parsing

## Objective

Extract readable text from documents.


Implemented:

- PDF extraction
- DOCX extraction
- TXT extraction
- Parser abstraction
- Error handling


## Libraries Used


### PyMuPDF

Purpose:

Extract text from PDF files.


Why?

- Fast
- Production stable
- Handles complex PDFs


---

### python-docx

Purpose:

Read Microsoft Word documents.


---

## Parser Design

Before:

```
API

 |
 |
PDF Logic
DOCX Logic
TXT Logic
```


After:

```
API

 |

ParserService

 |

PDFParser
DOCXParser
TXTParser
```

Benefits:

- Easy testing
- Easy extension
- Separation of responsibilities

---

# ✅ Sprint 4 - Intelligent Chunking


## Objective

Convert large documents into smaller meaningful pieces.


Example:


Before:

```
10 page document
```

After:

```
Chunk 1

Chunk 2

Chunk 3

Chunk 4
```


Implemented:

- Recursive text splitting
- Configurable chunk size
- Chunk overlap
- Metadata support


## Library Used


### LangChain Text Splitters


Purpose:

Intelligent document splitting.


Why?

Because simple string splitting breaks context.


Example:


Bad:

```
"The company policy"

"allows employees"
```


Good:

```
"The company policy allows employees"
```


---

# ✅ Sprint 4.1 - Chunk Storage


Implemented:

- Document ID tracking
- Chunk models
- Chunk persistence
- Metadata storage


Each chunk contains:


```json
{
"text":"employee leave policy",
"document_id":"uuid",
"metadata":{
"type":"pdf"
}
}
```

---

# ✅ Sprint 5 - Embedding Generation


## Objective

Convert text into numerical vectors.


Example:


Input:

```
Artificial Intelligence
```


Output:


```
[
0.123,
-0.453,
0.782
]
```


These vectors represent semantic meaning.


---

## Library Used


### Sentence Transformers


Purpose:

Generate text embeddings.


Why?

Traditional keyword search:

```
car
```

does not understand:


```
automobile
vehicle
transport
```


Embedding search understands semantic relationships.


---

# ✅ Sprint 5.1 - AI Model Registry


## Problem


Loading AI models repeatedly is expensive.


Bad:

```
Request 1

Load Model


Request 2

Load Model


Request 3

Load Model
```


Solution:


```
Application Startup

        ↓

Load Model Once

        ↓

Reuse Everywhere
```


Implemented:

- Singleton model loading
- Central AI registry
- Shared model instance


---

# ✅ Sprint 5.2 - Configuration Management


Implemented:

- Environment based configuration
- Pydantic settings
- External model configuration


Example:


`.env`

```env
EMBEDDING_MODEL=all-MiniLM-L6-v2

CHUNK_SIZE=1000

CHUNK_OVERLAP=200
```


Benefits:

- No hardcoded values
- Environment flexibility
- Production ready

---

# 🛠️ Tech Stack


## Backend

| Technology | Purpose |
|---|---|
| Python | Programming Language |
| FastAPI | Backend Framework |
| Uvicorn | ASGI Server |
| Pydantic | Data Validation |


---

## AI / ML

| Technology | Purpose |
|---|---|
| Sentence Transformers | Embeddings |
| HuggingFace Models | NLP Models |
| LangChain | Text Processing |


---

## Document Processing


| Library | Purpose |
|---|---|
| PyMuPDF | PDF Extraction |
| python-docx | DOCX Extraction |


---

## Testing


| Tool | Purpose |
|---|---|
| PyTest | Unit Testing |

---

# 📂 Project Structure


```
rag-chatbot

│

├── app

│   ├── main.py

│   │

│   ├── api

│   │

│   ├── core

│   │   ├── config.py

│   │   └── ai_registry.py

│   │

│   ├── services

│   │   ├── storage.py

│   │   ├── parser.py

│   │   ├── chunker.py

│   │   └── embedding.py

│   │

│   ├── models

│   │

│   └── schemas


├── tests


├── docs


├── requirements.txt


├── .env.example


├── README.md


└── .gitignore
```

---

# ⚙️ Local Setup


## Requirements


- Python 3.11+
- Git
- VS Code


---

## Clone Repository


```bash
git clone <repository-url>

cd rag-chatbot
```


---

## Create Virtual Environment


```bash
python -m venv venv
```


Activate:


### macOS/Linux

```bash
source venv/bin/activate
```


### Windows

```bash
venv\Scripts\activate
```


---

## Install Dependencies


```bash
pip install --upgrade pip

pip install -r requirements.txt
```

---

# Environment Configuration


Create:


```
.env
```


Example:


```env
EMBEDDING_MODEL=all-MiniLM-L6-v2

CHUNK_SIZE=1000

CHUNK_OVERLAP=200
```

---

# ▶️ Run Application


```bash
uvicorn app.main:app --reload
```


Server:

```
http://localhost:8000
```


Swagger:

```
http://localhost:8000/docs
```

---

# 📡 API Example


## Upload Document


Endpoint:


```
POST /upload
```


Response:


```json
{
 "filename":"document.pdf",
 "document_id":"uuid",
 "size":33302,
 "extracted_characters":666,
 "total_chunks":1,
 "total_embeddings":1,
 "message":"File uploaded successfully"
}
```

---

# 🧪 Testing


Run:


```bash
pytest
```


Testing covers:

- Parser services
- Chunking services
- Embedding generation
- AI registry


---

# 🧠 Engineering Principles


## SOLID Principles


### Single Responsibility Principle


Each service handles one responsibility.


Example:


```
StorageService

ParserService

ChunkingService

EmbeddingService
```


---

## Separation of Concerns


API Layer:

```
Request handling
```


Service Layer:

```
Business logic
```


Models:

```
Data representation
```


---

# Design Patterns Used


## Singleton Pattern


Used for AI model loading.


Purpose:

- Reduce memory usage
- Improve performance


---

## Registry Pattern


Central management of AI resources.


---

## Configuration Pattern


Environment driven configuration.


---

# 🗺️ Future Roadmap


## Sprint 6

Vector Database Integration

- ChromaDB
- Persistent storage
- Similarity search


---

## Sprint 7

Semantic Retrieval

- Query embeddings
- Top-K search
- Ranking


---

## Sprint 8

LLM Integration


Support:

- OpenAI
- Gemini
- Ollama


---

## Sprint 9

Complete RAG Pipeline


```
Question

 ↓

Retriever

 ↓

Context

 ↓

LLM

 ↓

Answer
```


---

## Sprint 10

Enterprise Features

- Authentication
- PostgreSQL
- User management


---

## Sprint 11

Production Engineering

- Docker
- CI/CD
- Automated tests


---

## Sprint 12

Deployment


Targets:

- AWS
- Azure
- Render


---

# 🎯 Learning Outcomes


This project demonstrates:


✅ AI Engineering

✅ LLM Application Development

✅ RAG Architecture

✅ NLP Pipelines

✅ Vector Search

✅ Backend Engineering

✅ Production AI System Design


---

# 👨‍💻 Author


Built as an AI Engineering portfolio project.

---

⭐ If this project helped you, consider starring the repository.
