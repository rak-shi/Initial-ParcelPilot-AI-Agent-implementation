from backend.services.document_service import DocumentService


def main():

    print("\n" + "=" * 70)
    print("PARCELPILOT DOCUMENT INGESTION")
    print("=" * 70)

    service = DocumentService()

    service.ingest_documents()


if __name__ == "__main__":
    main()