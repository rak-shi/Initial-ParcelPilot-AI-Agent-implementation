from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# =========================
# PROJECT PATHS
# =========================

DATA_DIR = BASE_DIR / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

DATABASE_DIR = BASE_DIR / "database"

DOCS_DIR = BASE_DIR / "docs"


# =========================
# SOURCE FILES
# =========================

EXCEL_FILE = (
    RAW_DATA_DIR
    / "ParcelPilot_Assessment_Data.xlsx"
)


# =========================
# DATABASE
# =========================

SQLITE_DB_PATH = (
    DATABASE_DIR
    / "parcelpilot.db"
)


# =========================
# DOCUMENT VECTOR STORE
# =========================

VECTOR_STORE_DIR = (
    PROCESSED_DATA_DIR
    / "vector_store"
)

EMBEDDINGS_FILE = (
    VECTOR_STORE_DIR
    / "document_embeddings.pkl"
)


# =========================
# AI
# =========================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)


# =========================
# CREATE REQUIRED DIRECTORIES
# =========================

PROCESSED_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

VECTOR_STORE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)