import os
import tempfile

from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader


async def parse_resume_pdf(file: UploadFile) -> str:
    """
    Parse a PDF file and extract its text content using langchain's PyPDFLoader.

    Args:
        file: FastAPI UploadFile object containing the PDF

    Returns:
        str: Extracted text from the PDF
    """
    try:
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Use PyPDFLoader to load the PDF
        loader = PyPDFLoader(temp_path)
        pages = []

        # Load pages asynchronously
        async for page in loader.alazy_load():
            pages.append(page)

        # Extract and combine text from all pages
        text_content = []
        for page in pages:
            text_content.append(page.page_content)

        # Join all pages
        full_text = "\n\n".join(text_content)

        return full_text.strip()

    except Exception as e:
        raise Exception(f"Error parsing PDF: {str(e)}")
    finally:
        # Clean up the temporary file
        await file.close()
        if "temp_path" in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
