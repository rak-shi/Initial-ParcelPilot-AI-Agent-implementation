import pickle
import re

import numpy as np
import pdfplumber

from backend.config import DOCS_DIR, PROCESSED_DATA_DIR


class DocumentService:
    """
    Handles PDF extraction, text chunking, embedding generation,
    vector-store persistence, semantic search and document access control.
    """

    def __init__(self):
        # The model is loaded only when semantic search or document
        # ingestion needs it. This keeps Streamlit startup fast.
        self.model = None

        self.vector_store_dir = (
            PROCESSED_DATA_DIR / "vector_store"
        )

        self.vector_store_path = (
            self.vector_store_dir
            / "document_embeddings.pkl"
        )

        self.vector_store_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.documents = []
        self.embeddings = None

        self.load_vector_store()

    # ============================================================
    # LAZY MODEL LOADING
    # ============================================================

    def _get_model(self):
        """
        Load and cache the embedding model only when required.

        Importing sentence-transformers inside this method prevents
        Torch and Transformers from loading during Streamlit startup.
        """

        if self.model is None:
            print("Loading embedding model...")

            from sentence_transformers import (
                SentenceTransformer,
            )

            self.model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )

            print("Embedding model loaded.")

        return self.model

    # ============================================================
    # DOCUMENT METADATA
    # ============================================================

    def get_document_metadata(self, filename):
        """
        Assign reliability, authority and access scope based on
        the supplied ParcelPilot documents.
        """

        metadata_map = {
            "01_Support_Policy_v3_CURRENT.pdf": {
                "source_type": "support_policy",
                "status": "CURRENT",
                "authority": 90,
                "authoritative": True,
                "scope": "GLOBAL",
                "account_id": "GLOBAL",
            },
            "02_Support_Policy_v2_DEPRECATED.pdf": {
                "source_type": "support_policy",
                "status": "DEPRECATED",
                "authority": 0,
                "authoritative": False,
                "scope": "GLOBAL",
                "account_id": "GLOBAL",
            },
            "03_Cancellation_and_Service_Credit_SOP_v4.pdf": {
                "source_type": "sop",
                "status": "CURRENT",
                "authority": 90,
                "authoritative": True,
                "scope": "GLOBAL",
                "account_id": "GLOBAL",
            },
            "04_Product_Operations_Guide_and_Known_Issues.pdf": {
                "source_type": "product_documentation",
                "status": "CURRENT",
                "authority": 80,
                "authoritative": True,
                "scope": "GLOBAL",
                "account_id": "GLOBAL",
            },
            "05_Northstar_Logistics_Enterprise_Agreement.pdf": {
                "source_type": "customer_agreement",
                "status": "ACTIVE",
                "authority": 100,
                "authoritative": True,
                "scope": "ACCOUNT",
                "account_id": "ACCT-001",
            },
            "06_LumenWorks_Service_Agreement.pdf": {
                "source_type": "customer_agreement",
                "status": "ACTIVE",
                "authority": 100,
                "authoritative": True,
                "scope": "ACCOUNT",
                "account_id": "ACCT-002",
            },
        }

        default_metadata = {
            "source_type": "unknown",
            "status": "UNKNOWN",
            "authority": 0,
            "authoritative": False,
            "scope": "GLOBAL",
            "account_id": "GLOBAL",
        }

        return metadata_map.get(
            filename,
            default_metadata,
        ).copy()

    # ============================================================
    # PDF EXTRACTION
    # ============================================================

    def extract_pages(self, pdf_path):
        """
        Extract and clean text from every page in a PDF.
        """

        pages = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(
                pdf.pages,
                start=1,
            ):
                text = page.extract_text()

                if text:
                    text = self.clean_text(text)

                    if text.strip():
                        pages.append(
                            {
                                "page": page_number,
                                "text": text,
                            }
                        )

        return pages

    # ============================================================
    # TEXT CLEANING
    # ============================================================

    def clean_text(self, text):
        """
        Normalize whitespace extracted from PDFs.
        """

        if not text:
            return ""

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ============================================================
    # TEXT CHUNKING
    # ============================================================

    def chunk_text(
        self,
        text,
        chunk_size=1200,
        overlap=200,
    ):
        """
        Split text into overlapping chunks.
        """

        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(
                start + chunk_size,
                text_length,
            )

            chunk = text[start:end]

            # Avoid cutting a sentence in the middle when possible.
            if end < text_length:
                last_period = chunk.rfind(". ")

                if last_period > chunk_size * 0.5:
                    end = start + last_period + 1
                    chunk = text[start:end]

            chunk = chunk.strip()

            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            next_start = end - overlap

            if next_start <= start:
                next_start = end

            start = next_start

        return chunks

    # ============================================================
    # INGEST DOCUMENTS
    # ============================================================

    def ingest_documents(
        self,
        reset_collection=True,
    ):
        """
        Extract PDFs, create chunks and generate embeddings.
        """

        if reset_collection:
            self.documents = []
            self.embeddings = None

        pdf_files = sorted(
            DOCS_DIR.glob("*.pdf")
        )

        print()
        print(f"Found {len(pdf_files)} PDF files.")

        if not pdf_files:
            raise FileNotFoundError(
                f"No PDF files found in: {DOCS_DIR}"
            )

        all_documents = []

        for pdf_path in pdf_files:
            print()
            print(f"Processing: {pdf_path.name}")

            metadata = self.get_document_metadata(
                pdf_path.name
            )

            pages = self.extract_pages(pdf_path)
            file_chunk_count = 0

            for page_data in pages:
                page_number = page_data["page"]
                page_text = page_data["text"]

                chunks = self.chunk_text(page_text)

                for chunk_index, chunk in enumerate(
                    chunks
                ):
                    document = {
                        "id": (
                            f"{pdf_path.stem}"
                            f"_page_{page_number}"
                            f"_chunk_{chunk_index}"
                        ),
                        "content": chunk,
                        "source": pdf_path.name,
                        "page": page_number,
                        "chunk_index": chunk_index,
                        "source_type": metadata[
                            "source_type"
                        ],
                        "status": metadata["status"],
                        "authority": metadata[
                            "authority"
                        ],
                        "authoritative": metadata[
                            "authoritative"
                        ],
                        "scope": metadata["scope"],
                        "account_id": metadata[
                            "account_id"
                        ],
                    }

                    all_documents.append(document)
                    file_chunk_count += 1

            print(
                f"  Added {file_chunk_count} chunks"
            )

        if not all_documents:
            raise ValueError(
                "No document chunks were created."
            )

        print()
        print("Creating embeddings...")

        texts = [
            document["content"]
            for document in all_documents
        ]

        # Load the model only when ingestion requires it.
        model = self._get_model()

        embeddings = model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
        )

        self.documents = all_documents

        self.embeddings = np.array(
            embeddings,
            dtype=np.float32,
        )

        self.save_vector_store()

        print()
        print(
            f"SUCCESS: Created embeddings for "
            f"{len(self.documents)} chunks."
        )

        return {
            "success": True,
            "documents": len(self.documents),
            "vector_store": str(
                self.vector_store_path
            ),
        }

    # ============================================================
    # SAVE VECTOR STORE
    # ============================================================

    def save_vector_store(self):
        """
        Save documents and embeddings locally.
        """

        data = {
            "documents": self.documents,
            "embeddings": self.embeddings,
        }

        with open(
            self.vector_store_path,
            "wb",
        ) as file:
            pickle.dump(data, file)

        print()
        print("Saved vector store to:")
        print(self.vector_store_path)

    # ============================================================
    # LOAD VECTOR STORE
    # ============================================================

    def load_vector_store(self):
        """
        Load previously generated documents and embeddings.
        """

        if not self.vector_store_path.exists():
            print("No existing vector store found.")
            print("Run document ingestion first.")
            return False

        try:
            with open(
                self.vector_store_path,
                "rb",
            ) as file:
                data = pickle.load(file)

            self.documents = data.get(
                "documents",
                [],
            )

            embeddings = data.get("embeddings")

            if embeddings is not None:
                self.embeddings = np.array(
                    embeddings,
                    dtype=np.float32,
                )
            else:
                self.embeddings = None

            print(
                f"Loaded {len(self.documents)} "
                f"document chunks."
            )

            return True

        except Exception as error:
            print("Failed to load vector store:")
            print(error)

            self.documents = []
            self.embeddings = None

            return False

    # ============================================================
    # ACCESS CONTROL
    # ============================================================

    def is_document_accessible(
        self,
        document,
        account_id=None,
        user_context=None,
    ):
        """
        Enforce global and account-level document access.
        """

        scope = document.get(
            "scope",
            "GLOBAL",
        )

        document_account_id = document.get(
            "account_id",
            "GLOBAL",
        )

        if scope == "GLOBAL":
            return True

        if scope == "ACCOUNT":
            role = None

            if user_context:
                role = user_context.get("role")

            # Authorized internal users can access agreements.
            if role in [
                "support",
                "admin",
                "operations",
            ]:
                return True

            # Customers can access only their own account.
            if user_context:
                user_account_id = user_context.get(
                    "account_id"
                )

                return (
                    user_account_id
                    == document_account_id
                )

            return account_id == document_account_id

        return False

    # ============================================================
    # COSINE SIMILARITY
    # ============================================================

    def cosine_similarity(
        self,
        query_embedding,
        document_embeddings,
    ):
        """
        Calculate cosine similarity.
        """

        if (
            document_embeddings is None
            or len(document_embeddings) == 0
        ):
            return np.array([])

        query_norm = np.linalg.norm(
            query_embedding
        )

        document_norms = np.linalg.norm(
            document_embeddings,
            axis=1,
        )

        denominator = document_norms * query_norm

        denominator = np.where(
            denominator == 0,
            1e-10,
            denominator,
        )

        similarities = np.dot(
            document_embeddings,
            query_embedding,
        ) / denominator

        return similarities

    # ============================================================
    # SEARCH
    # ============================================================

    def search(
        self,
        query,
        account_id=None,
        user_context=None,
        top_k=5,
    ):
        """
        Perform account-aware semantic document search.
        """

        if not query or not query.strip():
            return []

        if (
            not self.documents
            or self.embeddings is None
        ):
            loaded = self.load_vector_store()

            if (
                not loaded
                or not self.documents
                or self.embeddings is None
            ):
                return []

        # The embedding model is loaded only when search is used.
        model = self._get_model()

        query_embedding = model.encode(
            query,
            convert_to_numpy=True,
        )

        query_embedding = np.array(
            query_embedding,
            dtype=np.float32,
        )

        similarities = self.cosine_similarity(
            query_embedding,
            self.embeddings,
        )

        if len(similarities) == 0:
            return []

        ranked_indices = np.argsort(
            similarities
        )[::-1]

        results = []

        try:
            top_k = int(top_k)
        except (TypeError, ValueError):
            top_k = 5

        if top_k < 1:
            top_k = 1

        # Examine additional results because access control can
        # reject some high-ranking documents.
        for index in ranked_indices:
            document = self.documents[int(index)]

            if not self.is_document_accessible(
                document=document,
                account_id=account_id,
                user_context=user_context,
            ):
                continue

            result = {
                "id": document.get("id"),
                "source": document.get("source"),
                "page": document.get("page"),
                "chunk_index": document.get(
                    "chunk_index"
                ),
                "content": document.get("content"),
                "source_type": document.get(
                    "source_type"
                ),
                "status": document.get("status"),
                "authority": document.get(
                    "authority",
                    0,
                ),
                "authoritative": document.get(
                    "authoritative",
                    False,
                ),
                "scope": document.get("scope"),
                "account_id": document.get(
                    "account_id"
                ),
                "similarity": float(
                    similarities[index]
                ),
            }

            results.append(result)

            if len(results) >= top_k:
                break

        return results