import os
import httpx

from app.core.config import settings


class PDFDownloadError(Exception):
    pass


async def download_pdf(paper_id: str, pdf_url: str) -> str:
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    local_path = os.path.join(settings.STORAGE_DIR, f"{paper_id}.pdf")

    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        try:
            resp = await client.get(pdf_url)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise PDFDownloadError(f"Failed to download PDF: {e}") from e

    with open(local_path, "wb") as f:
        f.write(resp.content)

    return local_path