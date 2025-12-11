"""Notion API integration service."""

from typing import List, Dict, Any, Optional
from notion_client import AsyncClient
import structlog
from datetime import datetime

from app.core.config import settings
from app.utils.text_processor import TextProcessor

logger = structlog.get_logger(__name__)


class NotionService:
    """Service for interacting with Notion API."""

    def __init__(self):
        """Initialize Notion service."""
        self.client = AsyncClient(auth=settings.notion_token)
        self.text_processor = TextProcessor()

    async def fetch_pages(self, page_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch pages from Notion.

        Args:
            page_ids: Optional list of specific page IDs to fetch.
                     If not provided, fetches all accessible pages.

        Returns:
            List of page objects with their content.
        """
        pages = []

        try:
            if page_ids:
                # Fetch specific pages
                for page_id in page_ids:
                    try:
                        page = await self.client.pages.retrieve(page_id=page_id)
                        pages.append(page)
                        logger.info("Fetched page", page_id=page_id)
                    except Exception as e:
                        logger.error("Failed to fetch page", page_id=page_id, error=str(e))
            else:
                # Fetch all pages from workspace or database
                if settings.notion_db_id:
                    # Fetch from specific database
                    response = await self.client.databases.query(
                        database_id=settings.notion_db_id
                    )
                    pages.extend(response.get("results", []))

                    # Handle pagination
                    while response.get("has_more"):
                        response = await self.client.databases.query(
                            database_id=settings.notion_db_id,
                            start_cursor=response.get("next_cursor")
                        )
                        pages.extend(response.get("results", []))
                else:
                    # Search for all pages in workspace
                    response = await self.client.search(
                        filter={"property": "object", "value": "page"}
                    )
                    pages.extend(response.get("results", []))

                    # Handle pagination
                    while response.get("has_more"):
                        response = await self.client.search(
                            filter={"property": "object", "value": "page"},
                            start_cursor=response.get("next_cursor")
                        )
                        pages.extend(response.get("results", []))

                logger.info("Fetched pages from workspace", count=len(pages))

        except Exception as e:
            logger.error("Failed to fetch pages", error=str(e))
            raise

        return pages

    async def extract_text(self, page: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract text content from a Notion page.

        Args:
            page: Notion page object.

        Returns:
            List of text chunks with metadata.
        """
        chunks = []

        try:
            page_id = page["id"]
            page_title = self._get_page_title(page)

            # Fetch all blocks from the page
            blocks = await self._fetch_all_blocks(page_id)

            # Extract text from blocks
            text_content = []
            for block in blocks:
                text = self._extract_text_from_block(block)
                if text:
                    text_content.append(text)

            # Join all text
            full_text = "\n\n".join(text_content)

            # Create chunks with metadata
            if full_text:
                raw_chunks = self.text_processor.create_chunks(
                    full_text,
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap
                )

                for i, chunk_text in enumerate(raw_chunks):
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "page_id": page_id,
                            "page_title": page_title,
                            "chunk_index": i,
                            "total_chunks": len(raw_chunks),
                            "created_at": page.get("created_time", ""),
                            "last_edited": page.get("last_edited_time", ""),
                            "url": page.get("url", "")
                        }
                    })

            logger.info("Extracted text from page",
                       page_id=page_id,
                       chunks_created=len(chunks))

        except Exception as e:
            logger.error("Failed to extract text from page",
                        page_id=page.get("id", "unknown"),
                        error=str(e))
            raise

        return chunks

    async def _fetch_all_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Recursively fetch all blocks from a page.

        Args:
            page_id: The ID of the page.

        Returns:
            List of all blocks in the page.
        """
        blocks = []

        try:
            response = await self.client.blocks.children.list(block_id=page_id)
            blocks.extend(response.get("results", []))

            # Handle pagination
            while response.get("has_more"):
                response = await self.client.blocks.children.list(
                    block_id=page_id,
                    start_cursor=response.get("next_cursor")
                )
                blocks.extend(response.get("results", []))

            # Recursively fetch children blocks
            for block in blocks[:]:  # Use slice to avoid modifying list during iteration
                if block.get("has_children"):
                    children = await self._fetch_all_blocks(block["id"])
                    blocks.extend(children)

        except Exception as e:
            logger.error("Failed to fetch blocks", page_id=page_id, error=str(e))

        return blocks

    def _extract_text_from_block(self, block: Dict[str, Any]) -> Optional[str]:
        """
        Extract text from a Notion block.

        Args:
            block: Notion block object.

        Returns:
            Extracted text or None if no text content.
        """
        block_type = block.get("type")
        if not block_type:
            return None

        text_parts = []

        # Handle different block types
        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3",
                         "bulleted_list_item", "numbered_list_item", "to_do",
                         "toggle", "quote", "callout"]:
            rich_text = block.get(block_type, {}).get("rich_text", [])
            text_parts.extend([t.get("plain_text", "") for t in rich_text])

        elif block_type == "code":
            code_block = block.get("code", {})
            rich_text = code_block.get("rich_text", [])
            language = code_block.get("language", "")
            code_text = "".join([t.get("plain_text", "") for t in rich_text])
            if language:
                text_parts.append(f"```{language}\n{code_text}\n```")
            else:
                text_parts.append(f"```\n{code_text}\n```")

        elif block_type == "table":
            # For tables, we'll just note that there's a table
            # Full table extraction would require more complex logic
            text_parts.append("[Table content]")

        elif block_type == "image":
            caption = block.get("image", {}).get("caption", [])
            if caption:
                text_parts.append("Image: " + "".join([t.get("plain_text", "") for t in caption]))

        # Join all text parts
        text = " ".join(text_parts).strip()
        return text if text else None

    def _get_page_title(self, page: Dict[str, Any]) -> str:
        """
        Extract title from a Notion page.

        Args:
            page: Notion page object.

        Returns:
            Page title or "Untitled" if not found.
        """
        properties = page.get("properties", {})

        # Try different common title property names
        for prop_name in ["Name", "Title", "title", "name"]:
            if prop_name in properties:
                prop = properties[prop_name]
                if prop.get("type") == "title":
                    title_array = prop.get("title", [])
                    if title_array:
                        return "".join([t.get("plain_text", "") for t in title_array])

        # If no title property found, check all properties for title type
        for prop in properties.values():
            if prop.get("type") == "title":
                title_array = prop.get("title", [])
                if title_array:
                    return "".join([t.get("plain_text", "") for t in title_array])

        return "Untitled"

    async def get_page_metadata(self, page_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific page.

        Args:
            page_id: The ID of the page.

        Returns:
            Page metadata including properties and timestamps.
        """
        try:
            page = await self.client.pages.retrieve(page_id=page_id)
            return {
                "id": page["id"],
                "title": self._get_page_title(page),
                "created_time": page.get("created_time", ""),
                "last_edited_time": page.get("last_edited_time", ""),
                "url": page.get("url", ""),
                "archived": page.get("archived", False),
                "properties": page.get("properties", {})
            }
        except Exception as e:
            logger.error("Failed to get page metadata", page_id=page_id, error=str(e))
            raise