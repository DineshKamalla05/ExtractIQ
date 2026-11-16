from app.main import extract_information


def test_extract_information():
    result = extract_information(
        "Jane Doe\njane@example.com\n+1 555-123-4567\nPython, SQL and FastAPI"
    )
    assert result["name"] == "Jane Doe"
    assert result["email"] == "jane@example.com"
    assert result["phone"] == "+1 555-123-4567"
    assert result["skills"] == ["Python", "SQL", "FastAPI"]
