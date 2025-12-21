import re
from typing import List
import httpx
from bs4 import BeautifulSoup


class ScrapingService:
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 200

    async def scrape_url(self, url: str) -> str:
        """Scrape the content of a URL"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
            except Exception as e:
                raise Exception(f"Error scraping URL {url}: {str(e)}")

    def clean_text(self, html: str) -> str:
        """Clean and extract text from HTML"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remove scripts and styles
        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()

        # Extract the text
        text = soup.get_text()

        # Clean spaces and line breaks and remove special characters
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        # Remove excessive special characters
        text = re.sub(r'\s+', ' ', text)

        return text

    def chunk_text(self, text: str) -> List[str]:
        """Divide the text into chunks for embeddings"""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # If not the last chunk, try to cut at a period or space
            if end < len(text):
                # Find last period or space nearby
                last_period = text.rfind('.', start, end)
                last_space = text.rfind(' ', start, end)

                if last_period > start:
                    end = last_period + 1
                elif last_space > start:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - self.chunk_overlap
            if start < 0:
                start = 0

        return chunks

    async def scrape_and_chunk(self, url: str) -> List[str]:
        """Scrape a URL and return chunks of text"""
        html = await self.scrape_url(url)
        text = self.clean_text(html)
        chunks = self.chunk_text(text)
        return chunks


scraping_service = ScrapingService()
