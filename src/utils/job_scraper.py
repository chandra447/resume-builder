import re
from typing import Optional

from langchain_community.document_loaders import FireCrawlLoader
from langchain_core.documents import Document

from src.config.settings import settings


async def scrape_job_details(url: str, api_key: Optional[str] = None) -> str:
    """
    Scrape job details from a given URL using FireCrawlLoader.

    Args:
        url: The job posting URL
        api_key: Optional FireCrawl API key. If not provided, will use the one from settings.

    Returns:
        str: Extracted job description
    """
    try:
        # Initialize FireCrawlLoader
        loader = FireCrawlLoader(
            url=url,
            mode="scrape",  # We only need to scrape the single URL
            api_key=api_key or settings.firecrawl_api_key,
        )

        # Load the document
        docs = loader.load()

        if not docs:
            raise Exception("No content found at the URL")

        # Get the first document (since we're in scrape mode, there should only be one)
        doc: Document = docs[0]

        # Extract the content
        content = doc.page_content

        # Basic cleaning
        content = re.sub(r"\s+", " ", content)  # Remove multiple spaces
        content = re.sub(r"\n\s*\n", "\n\n", content)  # Remove multiple newlines
        content = content.strip()

        return content

    except Exception as e:
        raise Exception(f"Error scraping job details: {str(e)}")
