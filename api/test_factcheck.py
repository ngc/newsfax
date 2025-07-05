import asyncio
import json
import os
import sqlite3
import tempfile
from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from api import (
    app,
    init_database,
    get_fact_check_status,
    set_processing_status,
    save_fact_check_results,
    process_fact_checking,
    extract_content_from_url,
    analyze_facts_with_ai,
    CheckedFact,
    Source,
    DATABASE_PATH,
)


@pytest.fixture
def test_db():
    """Create a temporary database for testing."""
    # Create a temporary file for testing
    temp_fd, temp_path = tempfile.mkstemp()
    os.close(temp_fd)

    # Patch the DATABASE_PATH
    original_path = DATABASE_PATH
    import api

    api.DATABASE_PATH = temp_path

    # Initialize the test database
    init_database()

    yield temp_path

    # Cleanup
    api.DATABASE_PATH = original_path
    os.unlink(temp_path)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestDatabaseOperations:
    """Test database operations directly."""

    def test_init_database_creates_table(self, test_db):
        """Test that database initialization creates the correct table."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='fact_checks'
        """
        )
        result = cursor.fetchone()
        assert result is not None

        # Check table structure
        cursor.execute("PRAGMA table_info(fact_checks)")
        columns = cursor.fetchall()

        expected_columns = {
            "url": (
                "TEXT",
                0,
                1,
            ),  # (type, not_null, pk) - SQLite PRIMARY KEY implies NOT NULL
            "checked_fact_json": ("TEXT", 0, 0),
            "processed": ("INTEGER", 1, 0),  # NOT NULL with DEFAULT
        }

        assert len(columns) == 3

        for column in columns:
            name = column[1]
            col_type = column[2]
            not_null = column[3]
            pk = column[5]

            assert name in expected_columns
            expected_type, expected_not_null, expected_pk = expected_columns[name]
            assert col_type == expected_type
            assert not_null == expected_not_null
            assert pk == expected_pk

        conn.close()

    def test_get_fact_check_status_new_url(self, test_db):
        """Test getting status for a new URL returns None, False."""
        result_json, processed = get_fact_check_status("https://example.com")
        assert result_json is None
        assert processed is False

    def test_set_processing_status(self, test_db):
        """Test setting processing status."""
        url = "https://example.com"

        # Set processing to True
        set_processing_status(url, True)
        result_json, processed = get_fact_check_status(url)

        assert result_json is None
        assert processed is True

        # Set processing to False
        set_processing_status(url, False)
        result_json, processed = get_fact_check_status(url)

        assert result_json is None
        assert processed is False

    def test_save_fact_check_results(self, test_db):
        """Test saving fact check results."""
        url = "https://example.com"

        # First set as processing
        set_processing_status(url, True)

        # Create test facts
        facts = [
            CheckedFact(
                text="test fact",
                truthfulness="TRUE",
                summary="Test summary",
                sources=[
                    Source(
                        url="https://source.com",
                        favicon="https://source.com/favicon.ico",
                    )
                ],
            )
        ]

        # Save results
        save_fact_check_results(url, facts)

        # Check results
        result_json, processed = get_fact_check_status(url)
        assert result_json is not None
        assert processed is True

        # Parse and verify JSON
        parsed_facts = json.loads(result_json)
        assert len(parsed_facts) == 1
        assert parsed_facts[0]["text"] == "test fact"
        assert parsed_facts[0]["truthfulness"] == "TRUE"
        assert parsed_facts[0]["summary"] == "Test summary"
        assert len(parsed_facts[0]["sources"]) == 1
        assert parsed_facts[0]["sources"][0]["url"] == "https://source.com"


class TestFactCheckEndpoint:
    """Test the /factcheck endpoint."""

    @pytest.mark.asyncio
    @patch("api.process_fact_checking")
    async def test_first_request_starts_processing(self, mock_process, test_db, client):
        """Test that first request to new URL starts processing and returns 202."""
        url = "https://example.com/article"

        # Mock the background processing to prevent it from completing immediately
        mock_process.return_value = AsyncMock()

        response = client.post("/factcheck", json={"url": url})

        assert response.status_code == 202
        assert response.json()["message"] == "Fact checking started"

        # Verify database state
        result_json, processed = get_fact_check_status(url)
        assert result_json is None
        assert processed is True

    @pytest.mark.asyncio
    async def test_polling_while_processing_returns_202(self, test_db, client):
        """Test that polling while processing returns 202."""
        url = "https://example.com/article"

        # Set as processing
        set_processing_status(url, True)

        response = client.post("/factcheck", json={"url": url})

        assert response.status_code == 202
        assert response.json()["message"] == "Fact checking in progress"

    @pytest.mark.asyncio
    async def test_completed_processing_returns_200_with_facts(self, test_db, client):
        """Test that completed processing returns 200 with facts."""
        url = "https://example.com/article"

        # Create and save test facts
        facts = [
            CheckedFact(
                text="climate change",
                truthfulness="TRUE",
                summary="Well established science",
                sources=[
                    Source(
                        url="https://nasa.gov", favicon="https://nasa.gov/favicon.ico"
                    ),
                    Source(
                        url="https://noaa.gov", favicon="https://noaa.gov/favicon.ico"
                    ),
                ],
            ),
            CheckedFact(
                text="vaccines cause autism",
                truthfulness="FALSE",
                summary="Thoroughly debunked",
                sources=[
                    Source(url="https://cdc.gov", favicon="https://cdc.gov/favicon.ico")
                ],
            ),
        ]

        # Set as processing first, then save results
        set_processing_status(url, True)
        save_fact_check_results(url, facts)

        response = client.post("/factcheck", json={"url": url})

        assert response.status_code == 200
        response_facts = response.json()

        assert len(response_facts) == 2

        # Verify first fact
        assert response_facts[0]["text"] == "climate change"
        assert response_facts[0]["truthfulness"] == "TRUE"
        assert response_facts[0]["summary"] == "Well established science"
        assert len(response_facts[0]["sources"]) == 2

        # Verify second fact
        assert response_facts[1]["text"] == "vaccines cause autism"
        assert response_facts[1]["truthfulness"] == "FALSE"
        assert response_facts[1]["summary"] == "Thoroughly debunked"
        assert len(response_facts[1]["sources"]) == 1

    @pytest.mark.asyncio
    async def test_invalid_request_format(self, client):
        """Test that invalid request format is handled properly."""
        # Missing URL
        response = client.post("/factcheck", json={})
        assert response.status_code == 422  # Validation error

        # Invalid JSON
        response = client.post("/factcheck", json={"invalid": "field"})
        assert response.status_code == 422


class TestExternalDependencies:
    """Test the external dependency functions that will be implemented later."""

    @pytest.mark.asyncio
    async def test_extract_content_from_url(self, test_db):
        """Test that extract_content_from_url works as expected."""
        url = "https://example.com/article"

        # Call the function (currently returns mock content)
        content = await extract_content_from_url(url)

        # Verify it returns something
        assert content is not None
        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_analyze_facts_with_ai(self, test_db):
        """Test that analyze_facts_with_ai works as expected."""
        content = "This is a test article about climate change and vaccines."

        # Call the function (currently returns mock facts)
        facts = await analyze_facts_with_ai(content)

        # Verify it returns a list of CheckedFact objects
        assert isinstance(facts, list)
        assert len(facts) > 0

        for fact in facts:
            assert isinstance(fact, CheckedFact)
            assert fact.text
            assert fact.truthfulness in ["TRUE", "FALSE", "SOMEWHAT TRUE"]
            assert fact.summary
            assert isinstance(fact.sources, list)
            assert all(isinstance(source, Source) for source in fact.sources)

    @pytest.mark.asyncio
    async def test_process_fact_checking_error_handling(self, test_db):
        """Test that process_fact_checking handles errors gracefully."""
        url = "https://example.com/article"

        # Set as processing first
        set_processing_status(url, True)

        # Mock external function to raise an error
        with patch(
            "api.extract_content_from_url", side_effect=Exception("Network error")
        ):
            await process_fact_checking(url)

        # Verify that empty results were saved (marking as processed)
        result_json, processed = get_fact_check_status(url)
        assert result_json is not None
        assert processed is True

        # Verify empty results
        facts = json.loads(result_json)
        assert len(facts) == 0


class TestBackgroundProcessing:
    """Test the background processing workflow."""

    @pytest.mark.asyncio
    @patch("api.process_fact_checking")
    async def test_background_task_is_called(self, mock_process, test_db, client):
        """Test that background task is properly started."""
        url = "https://example.com/article"
        mock_process.return_value = AsyncMock()

        response = client.post("/factcheck", json={"url": url})

        assert response.status_code == 202
        # Note: In real tests, we'd need to wait for background tasks
        # For now, we just verify the response is correct

    @pytest.mark.asyncio
    @patch("api.extract_content_from_url")
    @patch("api.analyze_facts_with_ai")
    async def test_process_fact_checking_saves_results(
        self, mock_analyze, mock_extract, test_db
    ):
        """Test that process_fact_checking properly saves results."""
        url = "https://example.com/article"

        # Set as processing first
        set_processing_status(url, True)

        # Mock external dependencies
        mock_extract.return_value = "Mock extracted content from article"
        mock_analyze.return_value = [
            CheckedFact(
                text="climate change",
                truthfulness="TRUE",
                summary="Climate change is well-established by scientific consensus.",
                sources=[
                    Source(
                        url="https://www.nasa.gov/climate",
                        favicon="https://www.nasa.gov/favicon.ico",
                    )
                ],
            ),
            CheckedFact(
                text="vaccines cause autism",
                truthfulness="FALSE",
                summary="This claim has been thoroughly debunked by multiple studies.",
                sources=[
                    Source(
                        url="https://www.cdc.gov/",
                        favicon="https://www.cdc.gov/favicon.ico",
                    )
                ],
            ),
        ]

        # Run the processing with mocked external dependencies
        await process_fact_checking(url)

        # Verify external functions were called
        mock_extract.assert_called_once_with(url)
        mock_analyze.assert_called_once_with("Mock extracted content from article")

        # Check that results were saved
        result_json, processed = get_fact_check_status(url)
        assert result_json is not None
        assert processed is True

        # Verify the mock facts were saved
        facts = json.loads(result_json)
        assert len(facts) == 2
        assert any(fact["text"] == "climate change" for fact in facts)
        assert any(fact["text"] == "vaccines cause autism" for fact in facts)


class TestIntegrationWorkflow:
    """Test the complete workflow integration."""

    @pytest.mark.asyncio
    @patch("api.process_fact_checking")
    async def test_complete_workflow(self, mock_process, test_db, client):
        """Test the complete fact-checking workflow."""
        url = "https://example.com/test-article"

        # Mock the background processing to prevent it from completing immediately
        mock_process.return_value = AsyncMock()

        # Step 1: First request should start processing
        response1 = client.post("/factcheck", json={"url": url})
        assert response1.status_code == 202
        assert "started" in response1.json()["message"]

        # Step 2: Immediate second request should return processing
        response2 = client.post("/factcheck", json={"url": url})
        assert response2.status_code == 202
        assert "in progress" in response2.json()["message"]

        # Step 3: Manually complete the processing (simulate)
        mock_facts = [
            CheckedFact(
                text="integration test",
                truthfulness="SOMEWHAT TRUE",
                summary="Testing the integration",
                sources=[
                    Source(
                        url="https://test.com", favicon="https://test.com/favicon.ico"
                    )
                ],
            )
        ]
        save_fact_check_results(url, mock_facts)

        # Step 4: Next request should return completed results
        response3 = client.post("/factcheck", json={"url": url})
        assert response3.status_code == 200
        facts = response3.json()
        assert len(facts) == 1
        assert facts[0]["text"] == "integration test"
        assert facts[0]["truthfulness"] == "SOMEWHAT TRUE"

        # Step 5: Subsequent requests should continue returning the same results
        response4 = client.post("/factcheck", json={"url": url})
        assert response4.status_code == 200
        assert response4.json() == facts


if __name__ == "__main__":
    pytest.main([__file__])
