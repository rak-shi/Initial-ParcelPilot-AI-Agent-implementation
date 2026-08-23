from fastapi import FastAPI

from backend.routers.chat import router as chat_router


app = FastAPI(
    title="ParcelPilot AI Agent API",
    description=(
        "AI-powered ParcelPilot support agent with "
        "document retrieval, structured data access, "
        "access control and confirmation-based actions."
    ),
    version="1.0.0",
)


# --------------------------------------------------------------
# ROUTERS
# --------------------------------------------------------------

app.include_router(chat_router)


# --------------------------------------------------------------
# ROOT
# --------------------------------------------------------------

@app.get("/")
def root():

    return {
        "message": "ParcelPilot AI Agent API is running."
    }