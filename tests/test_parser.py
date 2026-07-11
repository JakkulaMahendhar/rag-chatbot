from pathlib import Path

from app.services.parser import ParserService


def test_txt_parser():

    file = Path("tests/sample.txt")

    text = ParserService.parse(file)

    assert "Artificial Intelligence" in text