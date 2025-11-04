# mini-rag

This is a minimal implementation of the RAG model for question answering

## Requiements
- Python 3.11 

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

## Run the FastAPI server
```bash 
$ uvicorn main:app --reload 0.0.0.0 ---port 5000
```

Dowanlod the POSTMAN from [https://www.postman.com/downloads/]
Dawnload the POSTMAN collections from [/assets/mini-rag-app.postman_collection.json](/assets/mini-rag-app.postman_collection.json)