import re

from bs4 import BeautifulSoup
from firecrawl import FireCrawl


async def scrape_job_details(url: str) -> str:
    """
    Scrape job details from a given URL using Firecrawl.

    Args:
        url: The job posting URL

    Returns:
        str: Extracted job description
    """
    try:
        # Initialize FireCrawl
        crawler = FireCrawl()

        # Fetch the page
        response = await crawler.get(url)

        if not response.ok:
            raise Exception(f"Failed to fetch URL: {response.status_code}")

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Common job description container classes/IDs
        job_desc_selectors = [
            "job-description",
            "description",
            "jobDescription",
            "job-details",
            "jobDetails",
            "job-posting",
            "jobPosting",
        ]

        # Try to find the job description container
        job_desc = None
        for selector in job_desc_selectors:
            # Try ID
            job_desc = soup.find(id=selector)
            if job_desc:
                break
            # Try class
            job_desc = soup.find(class_=selector)
            if job_desc:
                break

        # If no specific container found, try to find the largest text block
        if not job_desc:
            # Find all paragraph tags
            paragraphs = soup.find_all("p")
            if paragraphs:
                # Get the largest text block
                job_desc = max(paragraphs, key=lambda p: len(p.get_text()))

        if not job_desc:
            raise Exception("Could not find job description in the page")

        # Extract and clean text
        text = job_desc.get_text()

        # Basic cleaning
        text = re.sub(r"\s+", " ", text)  # Remove multiple spaces
        text = re.sub(r"\n\s*\n", "\n\n", text)  # Remove multiple newlines
        text = text.strip()

        return text

    except Exception as e:
        raise Exception(f"Error scraping job details: {str(e)}")
    finally:
        await crawler.close()
