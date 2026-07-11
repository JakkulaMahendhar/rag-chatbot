from pathlib import Path

import fitz
from docx import Document


class ParserService:

    @staticmethod
    def parse(file_path: Path) -> str:

        extension = file_path.suffix.lower()

        if extension == ".pdf":
            return ParserService.parse_pdf(file_path)

        if extension == ".docx":
            return ParserService.parse_docx(file_path)

        if extension == ".txt":
            return ParserService.parse_txt(file_path)

        raise ValueError("Unsupported document type")

    @staticmethod
    def parse_pdf(file_path: Path) -> str:

        document = fitz.open(file_path)

        text = ""

        for page in document:
            text += page.get_text() # type: ignore

        document.close()

        return text

    @staticmethod
    def parse_docx(file_path: Path) -> str:

        document = Document(file_path) # pyright: ignore[reportArgumentType]

        paragraphs = []

        for paragraph in document.paragraphs:
            paragraphs.append(paragraph.text)

        return "\n".join(paragraphs)

    @staticmethod
    def parse_txt(file_path: Path) -> str:

        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()