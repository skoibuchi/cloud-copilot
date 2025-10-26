# Cloud Copilot Backend

## Prerequisites
```
Python>=3.11
```

## Set Environment Variables
Create a `.env` file based on `.env.sample`.

## Install libraries
```sh
pip install -r requirements.txt
```

## Run
```sh
uvicorn main:app --reload --port 8000
```


## Memo
### Development Log
- (2025/10/24)Implemented and tested only for Google Cloud. Because safely try out with free plan...