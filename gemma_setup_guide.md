# Complete Gemma Setup Guide for Email Processing

## Setup Options Overview

| Option | Cost | Complexity | Performance | Best For |
|--------|------|------------|-------------|----------|
| **Google AI Studio** | Free (with limits) | Easy | Good | Testing & Development |
| **Vertex AI** | Pay-per-use | Medium | Excellent | Production |
| **Ollama (Local)** | Free | Medium | Good | Full control |
| **Hugging Face** | Free/Paid | Easy | Good | Quick prototyping |

## Option 1: Google AI Studio (Easiest - Recommended for Testing)

### Step 1: Get API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key" → "Create API Key"
4. Copy your API key

### Step 2: Install Required Packages
```bash
pip install google-generativeai
```

### Step 3: Create Gemma Agent
Create file: `gemma_ai_agent.py`

### Step 4: Test the Setup
Create file: `test_gemma_setup.py`

---

## Option 2: Vertex AI (Best for Production)

### Step 1: Setup Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Vertex AI API
4. Create service account and download JSON key

### Step 2: Install Vertex AI SDK
```bash
pip install google-cloud-aiplatform
```

### Step 3: Set Environment Variables
```bash
set GOOGLE_APPLICATION_CREDENTIALS=path\to\your\service-account-key.json
set GOOGLE_CLOUD_PROJECT=your-project-id
```

### Step 4: Create Vertex AI Agent
Create file: `vertex_gemma_agent.py`

---

## Option 3: Ollama (Local/Free - Best for Privacy)

### Step 1: Install Ollama
1. Download from [Ollama.ai](https://ollama.ai/)
2. Install on Windows
3. Open PowerShell/CMD

### Step 2: Download Gemma Model
```bash
ollama pull gemma:7b
# or for smaller version
ollama pull gemma:2b
```

### Step 3: Install Python Client
```bash
pip install ollama
```

### Step 4: Create Ollama Agent
Create file: `ollama_gemma_agent.py`

---

## Option 4: Hugging Face (Quick Testing)

### Step 1: Get API Token
1. Go to [Hugging Face](https://huggingface.co/)
2. Sign up/Login → Settings → Access Tokens
3. Create new token with "Read" permissions

### Step 2: Install Transformers
```bash
pip install transformers torch accelerate
```

### Step 3: Create HF Agent
Create file: `huggingface_gemma_agent.py`