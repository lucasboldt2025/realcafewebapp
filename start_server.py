import uvicorn

if __name__ == "__main__":
    # Rode o app permitindo conexões externas
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
