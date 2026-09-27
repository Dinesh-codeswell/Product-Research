"""Tests for Office SDK Bridge & Router"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.entities import ResearchSession, InsightCluster, EvidenceQuote
from app.models.seo_entities import SeoAuditSession
from app.core.database import get_db

@pytest.mark.anyio
async def test_office_documents_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. List initially empty or existing
        res = await ac.get("/api/v1/office/documents")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

        # 2. Save a new document
        payload = {
            "title": "Q3 Product Discovery Workbook",
            "doc_type": "sheets",
            "source_type": "research",
            "source_id": "test-res-123",
            "snapshot": {
                "id": "wb-test",
                "name": "Q3 Product Discovery",
                "sheets": {}
            },
            "summary": "Live testing workbook"
        }
        res_post = await ac.post("/api/v1/office/documents", json=payload)
        assert res_post.status_code == 200
        data = res_post.json()
        assert data["status"] == "saved"
        doc_id = data["id"]

        # 3. Retrieve document
        res_get = await ac.get(f"/api/v1/office/documents/{doc_id}")
        assert res_get.status_code == 200
        assert res_get.json()["title"] == "Q3 Product Discovery Workbook"

        # 4. Delete document
        res_del = await ac.delete(f"/api/v1/office/documents/{doc_id}")
        assert res_del.status_code == 200
        assert res_del.json()["status"] == "deleted"

@pytest.mark.anyio
async def test_office_sources():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/office/sources")
        assert res.status_code == 200
        data = res.json()
        assert "research" in data
        assert "seo" in data
