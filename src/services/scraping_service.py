import re
from typing import List
import httpx
from bs4 import BeautifulSoup


class ScrapingService:
    def __init__(self):
        self.chunk_size = 1000  # Caracteres por chunk
        self.chunk_overlap = 200  # Overlap entre chunks

    async def scrape_url(self, url: str) -> str:
        """Scrapea el contenido de una URL"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
            except Exception as e:
                raise Exception(f"Error scraping URL {url}: {str(e)}")

    def clean_text(self, html: str) -> str:
        """Limpia y extrae texto del HTML"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remover scripts y styles
        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()

        # Extraer texto
        text = soup.get_text()

        # Limpiar espacios y saltos de línea
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        # Remover caracteres especiales excesivos
        text = re.sub(r'\s+', ' ', text)

        return text

    def chunk_text(self, text: str) -> List[str]:
        """Divide el texto en chunks para embeddings"""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Si no es el último chunk, intentar cortar en un punto o espacio
            if end < len(text):
                # Buscar último punto o espacio cercano
                last_period = text.rfind('.', start, end)
                last_space = text.rfind(' ', start, end)

                if last_period > start:
                    end = last_period + 1
                elif last_space > start:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Mover start con overlap
            start = end - self.chunk_overlap
            if start < 0:
                start = 0

        return chunks

    async def scrape_and_chunk(self, url: str) -> List[str]:
        """Scrapea una URL y retorna chunks de texto"""
        html = await self.scrape_url(url)
        text = self.clean_text(html)
        chunks = self.chunk_text(text)
        return chunks


scraping_service = ScrapingService()
