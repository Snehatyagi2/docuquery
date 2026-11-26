import os
import tempfile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


class TestDocuQueryAPI(unittest.TestCase):
    """Integration tests for DocuQuery REST API endpoints."""

    @classmethod
    def setUpClass(cls):
        cls._tmp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(cls._tmp_dir.name, "test_docuquery.db")
        cls.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()
        cls._tmp_dir.cleanup()

    def test_01_health_check(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_02_ingest_list_query_and_delete(self):
        payload = {
            "title": "Q3 Financial Risk Policy",
            "source_type": "pdf",
            "pages": [
                {"page_number": 1, "text": "Credit risk scoring weights financial ratios at 70 percent."},
                {"page_number": 2, "text": "Normalized spending behaviour accounts for 30 percent of the composite score."},
            ],
        }
        ingest_res = self.client.post("/api/v1/documents", json=payload)
        self.assertEqual(ingest_res.status_code, 201)
        doc = ingest_res.json()
        self.assertEqual(doc["page_count"], 2)
        self.assertGreaterEqual(doc["chunk_count"], 2)

        list_res = self.client.get("/api/v1/documents")
        self.assertEqual(list_res.status_code, 200)
        self.assertTrue(any(d["id"] == doc["id"] for d in list_res.json()))

        query_res = self.client.post(
            "/api/v1/query",
            json={"question": "How much weight is given to financial ratios?", "top_k": 2, "document_id": doc["id"]},
        )
        self.assertEqual(query_res.status_code, 200)
        body = query_res.json()
        self.assertGreaterEqual(len(body["citations"]), 1)
        self.assertEqual(body["citations"][0]["page_number"], 1)

        del_res = self.client.delete(f"/api/v1/documents/{doc['id']}")
        self.assertEqual(del_res.status_code, 204)

    def test_03_rag_evaluation_metrics(self):
        ingest_res = self.client.post(
            "/api/v1/documents",
            json={
                "title": "Logistics SLA",
                "pages": [
                    {"page_number": 1, "text": "Warehouse dispatch SLA is 4 hours for Tier-1 hubs."},
                    {"page_number": 2, "text": "Cold chain telemetry runs every 15 minutes."},
                ],
            },
        )
        self.assertEqual(ingest_res.status_code, 201)
        doc_id = ingest_res.json()["id"]

        eval_res = self.client.post(
            "/api/v1/evaluate",
            json={
                "document_id": doc_id,
                "top_k": 2,
                "cases": [
                    {
                        "question": "What is the warehouse dispatch SLA?",
                        "expected_page": 1,
                        "expected_keyword": "4 hours",
                    },
                    {
                        "question": "How often does cold chain telemetry run?",
                        "expected_page": 2,
                        "expected_keyword": "15 minutes",
                    },
                ],
            },
        )
        self.assertEqual(eval_res.status_code, 200)
        metrics = eval_res.json()
        self.assertEqual(metrics["total_cases"], 2)
        self.assertEqual(metrics["hit_rate_at_k"], 1.0)
        self.assertEqual(metrics["mrr"], 1.0)


if __name__ == "__main__":
    unittest.main()
