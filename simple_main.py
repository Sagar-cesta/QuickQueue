from fastapi import FastAPI

app = FastAPI(title="QuickQueue", description="Ticketing/Helpdesk Queue System")

@app.get("/")
def read_root():
    return {"message": "Welcome to QuickQueue - Ticketing System"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
