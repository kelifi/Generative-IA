#!/usr/bin/env python
from source.services.es_vector_db_ingestion.es_vector_db_ingest_service import ingestion_service

if __name__ == "__main__":
    ingestion_service.ingest_data()
