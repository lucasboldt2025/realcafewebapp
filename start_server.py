import uvicorn

if __name__ == "__main__":
    # Troque "main" pelo nome do seu arquivo principal (sem o .py)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
