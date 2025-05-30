#!/usr/bin/env python3
"""
Unified Typst Documentation Scraper with Async Support

Usage:
    python scrape.py --all                          # Scrape all docs
    python scrape.py --glob "reference/**"          # Scrape pattern
    python scrape.py --url <url>                    # Scrape single URL
    python scrape.py --retry                        # Retry failed URLs
    python scrape.py --output ./docs                # Set output directory
    python scrape.py --concurrent 5                 # Set concurrency
"""

import asyncio
import aiohttp
import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime
from fnmatch import fnmatch
from bs4 import BeautifulSoup
import logging
from dataclasses import dataclass
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ScrapeResult:
    """Result of scraping a single page."""
    url: str
    success: bool
    output_path: Optional[Path] = None
    error: Optional[str] = None
    duration: float = 0.0

class TypstScraper:
    """Async scraper for Typst documentation."""
    
    def __init__(self, output_dir: str = "typst-docs", concurrent: int = 3):
        self.output_dir = Path(output_dir)
        self.concurrent = concurrent
        self.base_url = "https://typst.app/docs/"
        self.visited_urls: Set[str] = set()
        self.failed_urls: Dict[str, str] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load previous state if exists
        self.state_file = self.output_dir / ".scraper_state.json"
        self.load_state()
    
    def load_state(self):
        """Load previous scraping state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.visited_urls = set(state.get('visited', []))
                    self.failed_urls = state.get('failed', {})
                logger.info(f"Loaded state: {len(self.visited_urls)} visited, {len(self.failed_urls)} failed")
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
    
    def save_state(self):
        """Save current scraping state."""
        state = {
            'visited': list(self.visited_urls),
            'failed': self.failed_urls,
            'last_run': datetime.now().isoformat()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    async def fetch_page(self, url: str) -> Tuple[str, str]:
        """Fetch a page asynchronously."""
        async with self.session.get(url) as response:
            response.raise_for_status()
            return url, await response.text()
    
    async def get_all_doc_links(self, pattern: Optional[str] = None) -> List[str]:
        """Get all documentation links, optionally filtered by pattern."""
        logger.info("Fetching documentation index...")
        
        _, html = await self.fetch_page(self.base_url)
        soup = BeautifulSoup(html, 'html.parser')
        
        links = []
        
        # Find all documentation links
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            if not href.startswith('/docs/') or href == '/docs/':
                continue
            
            full_url = urljoin(self.base_url, href)
            
            # Remove anchors
            if '#' in full_url:
                full_url = full_url.split('#')[0]
            
            # Apply pattern filter if provided
            if pattern:
                # Convert URL to relative path for pattern matching
                rel_path = full_url.replace(self.base_url, '')
                if not fnmatch(rel_path, pattern):
                    continue
            
            links.append(full_url)
        
        # Remove duplicates
        links = list(dict.fromkeys(links))
        logger.info(f"Found {len(links)} documentation pages")
        return links
    
    def url_to_path(self, url: str) -> Path:
        """Convert URL to output file path."""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p and p != 'docs']
        
        if path_parts:
            # Create file path
            file_path = self.output_dir / Path(*path_parts)
            
            # Ensure it ends with .typ (changed from .md)
            if not file_path.suffix:
                file_path = file_path.with_suffix('.typ')
            
            return file_path
        
        return self.output_dir / "index.typ" # Changed from .md
    
    def convert_html_to_markdown(self, html_content: str) -> str:
        """Convert Typst documentation HTML to Typst markup."""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove unwanted elements
        # Remove all div.tooltip-context
        for tooltip in soup.find_all('div', class_='tooltip-context'):
            tooltip.decompose()

        # Extract main content area
        main_content = soup.find('main')
        if not main_content:
            raise ValueError("Could not find main content area")

        # Get page title from h1
        title_elem = main_content.find('h1')
        if not title_elem:
            raise ValueError("Could not find page title")

        # Extract title text, handling code elements and badges
        title_text = self._extract_title(title_elem)

        # Start building Typst markup
        # Changed to Typst heading syntax: = Heading
        markdown_lines = [f"= {title_text}\n"]

        # Process content sequentially
        processed_elements = set()

        # Find all major sections (h1, h2)
        sections = main_content.find_all(['h1', 'h2'])

        for i, section in enumerate(sections):
            if section in processed_elements:
                continue

            # Determine next section boundary
            next_section = sections[i + 1] if i + 1 < len(sections) else None

            # Get section content
            section_content = self._get_section_content(section, next_section)

            # Process section
            section_md = self._process_section(section, section_content)
            if section_md:
                markdown_lines.extend(section_md)

            # Mark processed elements
            processed_elements.add(section)
            processed_elements.update(section_content)

        return "\n".join(markdown_lines)
    
    def _extract_title(self, title_elem) -> str:
        """Extract clean title from h1 element."""
        # Handle code elements in title
        code_elem = title_elem.find('code')
        if code_elem:
            title = code_elem.get_text().strip()
        else:
            title = title_elem.get_text().strip()

        # Clean up badges, tooltips, and extra text
        title = re.sub(r'\s*(Element|Function)\s*$', '', title)
        title = re.sub(r'Question mark.*', '', title)
        return title.strip()
    
    def _get_section_content(self, start_elem, end_elem) -> List:
        """Get all content between two section headers."""
        content = []
        current = start_elem.next_sibling

        while current and current != end_elem:
            if hasattr(current, 'name') and current.name:
                # Stop if we hit a new major section (h1 or h2) that is not the start_elem itself
                if current.name in ['h1', 'h2'] and current != start_elem:
                    break
                content.append(current)
            current = current.next_sibling

        return content
    
    def _process_section(self, header, content_elements) -> List[str]:
        """Process a section with all its content."""
        lines = []

        header_text = self._clean_text(header.get_text())
        header_level = int(header.name[1]) if header.name.startswith('h') else 2

        # Only add header for h2 and below. h1 is handled by the document title.
        if header.name != 'h1':
            # Changed to Typst heading syntax: = Heading
            lines.append(f"{'=' * header_level} {header_text}\n")

        # Process regular content
        for elem in content_elements:
            # Handle sub-headers for parameters/definitions (h3, h4)
            if elem.name.startswith('h') and elem != header:
                sub_header_level = int(elem.name[1])
                code_elem = elem.find('code')
                if code_elem:
                    param_name = code_elem.get_text().strip()
                    
                    type_text = ""
                    properties = []
                    
                    additional_info = elem.find('div', class_='additional-info')
                    if additional_info:
                        # Use the _extract_parameter_metadata method to get type and properties
                        extracted_metadata = self._extract_parameter_metadata(additional_info)
                        type_text = extracted_metadata[0]
                        properties = extracted_metadata[1] # This will be a list of properties

                    output_line = f"{'=' * sub_header_level} `{param_name}`" # Changed to Typst heading syntax
                    if type_text:
                        output_line += f": {type_text}"
                    
                    if properties:
                        output_line += f" ({', '.join(properties)})"
                    
                    lines.append(f"{output_line}\n")

            elif elem.name == 'p':
                text = self._process_paragraph(elem)
                if text.strip():
                    lines.append(f"{text}\n")

            elif elem.name == 'div' and 'previewed-code' in elem.get('class', []):
                code_block = self._process_code_block(elem)
                if code_block:
                    lines.append(f"{code_block}\n")

            # Handle the function signature block (e.g., block(...) -> content)
            elif elem.name == 'div' and 'code-definition' in elem.get('class', []):
                signature = self._process_function_signature(elem)
                if signature:
                    lines.append(f"{signature}\n")

            elif elem.name == 'details':
                example = self._process_example_details(elem)
                if example:
                    lines.append(f"{example}\n")

            elif elem.name in ['ul', 'ol']:
                list_content = self._process_list(elem)
                if list_content:
                    lines.append(f"{list_content}\n")

        return lines
    
    def _clean_text(self, text: str) -> str:
        """Clean text from tooltips and extra content."""
        # Remove tooltip text and question marks
        text = re.sub(r'Question mark.*?(?=\w|$)', '', text, flags=re.DOTALL)
        text = re.sub(r'Element functions.*?rules\.', '', text)
        text = re.sub(r'Settable parameters.*?rule\.', '', text)
        text = re.sub(r'Parameters are.*?name\.', '', text)
        text = re.sub(r'Positional parameters.*?names\.', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted phrases
        text = re.sub(r'\s*(Element|Function)\s*$', '', text)
        
        return text
    
    def _process_paragraph(self, elem) -> str:
        """Process paragraph element."""
        text = ""

        for content in elem.children:
            if hasattr(content, 'name'):
                if content.name == 'code':
                    code_text = content.get_text()
                    text += f"`{code_text}`"
                elif content.name == 'a':
                    link_text = content.get_text()
                    href = content.get('href', '')
                    if href and 'tooltip' not in link_text.lower():
                        text += f"#link(\"{href}\")[{link_text}]"
                    else:
                        text += link_text
                elif content.name == 'em':
                    text += f"_{content.get_text()}_" # Changed to Typst italic syntax
                elif content.name == 'strong':
                    text += f"*{content.get_text()}*" # Changed to Typst bold syntax
                elif content.name in ['div', 'span'] and 'tooltip' in content.get('class', []):
                    continue  # Skip tooltip content
                else:
                    inner_text = content.get_text()
                    if 'Question mark' not in inner_text:
                        text += inner_text
            else:
                content_str = str(content)
                if not content_str.startswith('<') and 'Question mark' not in content_str:
                    text += content_str

        return self._clean_text(text)
    
    def _process_code_block(self, elem) -> Optional[str]:
        """Process code block element."""
        pre_elem = elem.find('pre')
        if not pre_elem:
            return None

        code_elem = pre_elem.find('code')
        if not code_elem:
            return None

        # Extract code text
        code_text = code_elem.get_text()
        
        # Clean up
        lines = code_text.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        # Remove trailing empty lines
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        code_text = '\n'.join(cleaned_lines)
        
        # Typst raw blocks use backticks, similar to Markdown.
        # The `typst` language specifier is also standard.
        # So, this part remains largely the same.
        if 'backticks' in code_text and 'Adding' in code_text:
            return f"```typst\n{code_text}\n```"

        return f"```typst\n{code_text}\n```"
    
    def _process_function_signature(self, elem) -> Optional[str]:
        """Process function signature."""
        func_name_elem = elem.find('span', class_='typ-func')
        if not func_name_elem:
            return None
        func_name = func_name_elem.get_text().strip()
        
        arguments_div = elem.find('div', class_='arguments')
        if not arguments_div:
            return None
        
        params = []
        for param_span in arguments_div.find_all('span', class_='overview-param'):
            param_name = ""
            param_type_str = ""

            # Try to get parameter name from the 'a' tag's text or href
            param_name_link = param_span.find('a')
            if param_name_link:
                # Get name from text first
                name_from_text = param_name_link.get_text().replace(':', '').strip()
                if name_from_text:
                    param_name = name_from_text
                elif param_name_link.get('href'):
                    # If text is empty, try to get from href (e.g., for 'body')
                    href_id = param_name_link.get('href').lstrip('#')
                    if href_id.startswith('parameters-'):
                        param_name = href_id.replace('parameters-', '')

            # Extract types for this parameter
            types = []
            # Iterate through children of param_span to find type elements (a or span.pill)
            # and raw text that is not "or" or "|"
            for child in param_span.children:
                if hasattr(child, 'name'):
                    if child.name == 'a' and 'pill' in child.get('class', []): # Only consider 'a' tags that are pills
                        types.append(child.get_text().strip())
                    elif child.name == 'span' and 'pill' in child.get('class', []):
                        types.append(child.get_text().strip())
                    elif child.name == 'small' and child.get_text().strip().lower() == 'or':
                        # Ignore "or" text from small tags, it's handled by joining
                        pass
                elif isinstance(child, str) and child.strip() and child.strip().lower() not in ['or', '|']:
                    types.append(child.strip())
            
            param_type_str = ' | '.join([t for t in types if t]) # Join with " | "

            if param_name and param_type_str:
                params.append(f"{param_name}: {param_type_str}")
            elif param_type_str: # For cases where there's no explicit name but a type (e.g., last content parameter)
                params.append(param_type_str)
            elif param_name: # If only name is found, but no type (shouldn't happen for these signatures)
                params.append(param_name)

        # Find the return type (it's usually the last 'a' tag with class 'pill' outside the arguments div)
        return_type_elem = elem.find_all('a', class_='pill')[-1] if elem.find_all('a', class_='pill') else None
        return_type = return_type_elem.get_text().strip() if return_type_elem else ''

        # Assemble the final signature string with proper indentation and newlines
        formatted_params = ",\n  ".join(params)
        
        signature_text = f"{func_name}(\n  {formatted_params}\n) -> {return_type}"

        return f"```\n{signature_text}\n```"
    
    def _process_example_details(self, elem) -> Optional[str]:
        """Process example in details element."""
        summary = elem.find('summary')
        if not summary:
            return None

        # Clean up summary text
        title = self._clean_text(summary.get_text()).replace('View example', 'Example')

        # Find code block
        code_div = elem.find('div', class_='previewed-code')
        if code_div:
            code_block = self._process_code_block(code_div)
            if code_block:
                return f"*{title}:*\n{code_block}"

        return None
    
    def _process_list(self, elem) -> Optional[str]:
        """Process list element."""
        items = []
        for li in elem.find_all('li', recursive=False):
            item_text = self._process_paragraph(li)
            if item_text.strip():
                marker = "-" if elem.name == 'ul' else "1."
                items.append(f"{marker} {item_text}")

        return '\n'.join(items) if items else None
    
    def _extract_parameter_metadata(self, info_elem) -> List[str]:
        """Extract parameter metadata."""
        type_text = ""
        properties = []

        # Extract type information
        type_div = info_elem.find('div')
        if type_div:
            type_parts = []
            for elem in type_div.children:
                if hasattr(elem, 'name'):
                    if elem.name == 'a' or (elem.name == 'span' and 'pill' in elem.get('class', [])):
                        type_parts.append(elem.get_text().strip())
                elif str(elem).strip() and str(elem).strip().lower() not in ['or', '|']:
                    type_parts.append(str(elem).strip())
            
            type_text = ' | '.join([t for t in type_parts if t])

        # Extract other properties
        for small in info_elem.find_all('small'):
            text = self._clean_text(small.get_text())
            if text and text.lower() in ['required', 'settable', 'positional', 'variadic']:
                properties.append(text)

        return [type_text, properties] # Return as a list: [type_string, [prop1, prop2]]
    
    async def scrape_page(self, url: str) -> ScrapeResult:
        """Scrape a single page."""
        start_time = time.time()
        
        try:
            # Skip if already visited (unless retrying)
            if url in self.visited_urls and url not in self.failed_urls:
                return ScrapeResult(url, True, duration=0)
            
            # Fetch page
            _, html = await self.fetch_page(url)
            
            # Convert to markdown
            markdown = self.convert_html_to_markdown(html)
            
            # Save to file
            output_path = self.url_to_path(url)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            # Update state
            self.visited_urls.add(url)
            if url in self.failed_urls:
                del self.failed_urls[url]
            
            duration = time.time() - start_time
            logger.info(f"✓ {url} -> {output_path} ({duration:.2f}s)")
            
            return ScrapeResult(url, True, output_path, duration=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            error = str(e)
            self.failed_urls[url] = error
            logger.error(f"✗ {url}: {error}")
            return ScrapeResult(url, False, error=error, duration=duration)
    
    async def scrape_pages(self, urls: List[str]) -> List[ScrapeResult]:
        """Scrape multiple pages concurrently."""
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.concurrent)
        
        async def scrape_with_limit(url: str) -> ScrapeResult:
            async with semaphore:
                return await self.scrape_page(url)
        
        # Create tasks
        tasks = [scrape_with_limit(url) for url in urls]
        
        # Run with progress updates
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks), 1):
            result = await task
            results.append(result)
            
            if i % 10 == 0 or i == len(tasks):
                logger.info(f"Progress: {i}/{len(tasks)} pages")
                self.save_state()
        
        return results
    
    async def run_all(self) -> List[ScrapeResult]:
        """Scrape all documentation pages."""
        async with aiohttp.ClientSession() as self.session:
            urls = await self.get_all_doc_links()
            return await self.scrape_pages(urls)
    
    async def run_glob(self, pattern: str) -> List[ScrapeResult]:
        """Scrape pages matching glob pattern."""
        async with aiohttp.ClientSession() as self.session:
            urls = await self.get_all_doc_links(pattern)
            return await self.scrape_pages(urls)
    
    async def run_url(self, url: str) -> ScrapeResult:
        """Scrape a single URL."""
        async with aiohttp.ClientSession() as self.session:
            return await self.scrape_page(url)
    
    async def run_retry(self) -> List[ScrapeResult]:
        """Retry failed URLs."""
        if not self.failed_urls:
            logger.info("No failed URLs to retry")
            return []
        
        logger.info(f"Retrying {len(self.failed_urls)} failed URLs")
        async with aiohttp.ClientSession() as self.session:
            urls = list(self.failed_urls.keys())
            return await self.scrape_pages(urls)
    
    def create_index(self):
        """Create an index file of all scraped documents."""
        index_path = self.output_dir / "INDEX.typ" # Changed from .md
        
        with open(index_path, 'w') as f:
            f.write("= Typst Documentation Index\n\n") # Changed to Typst heading
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Organize by directory
            files_by_dir = defaultdict(list)
            
            for typ_file in self.output_dir.rglob("*.typ"): # Changed from .md
                if typ_file.name in ["INDEX.typ", ".scraper_state.json"]: # Changed from .md
                    continue
                
                rel_path = typ_file.relative_to(self.output_dir)
                dir_path = rel_path.parent
                files_by_dir[dir_path].append(rel_path)
            
            # Write organized index
            for dir_path in sorted(files_by_dir.keys()):
                if str(dir_path) != ".":
                    f.write(f"\n== {dir_path}\n\n") # Changed to Typst heading
                
                for file_path in sorted(files_by_dir[dir_path]):
                    title = file_path.stem.replace('-', ' ').title()
                    f.write(f"- [{title}]({file_path})\n")
            
            # Stats
            f.write(f"\n== Statistics\n\n") # Changed to Typst heading
            f.write(f"- Total pages: {len(self.visited_urls)}\n")
            f.write(f"- Failed pages: {len(self.failed_urls)}\n")
            
            if self.failed_urls:
                f.write(f"\n=== Failed URLs\n\n") # Changed to Typst heading
                for url, error in self.failed_urls.items():
                    f.write(f"- {url}\n")
                    f.write(f"  - Error: {error[:100]}...\n")
        
        logger.info(f"Index created: {index_path}")


async def main():
    parser = argparse.ArgumentParser(description="Scrape Typst documentation")
    
    # Actions
    parser.add_argument('--all', action='store_true', 
                        help='Scrape all documentation pages')
    parser.add_argument('--glob', type=str, 
                        help='Scrape pages matching pattern (e.g., "reference/**")')
    parser.add_argument('--url', type=str, 
                        help='Scrape a single URL')
    parser.add_argument('--retry', action='store_true', 
                        help='Retry previously failed URLs')
    
    # Options
    parser.add_argument('--output', type=str, default='typst-docs',
                        help='Output directory (default: typst-docs)')
    parser.add_argument('--concurrent', type=int, default=3,
                        help='Number of concurrent requests (default: 3)')
    
    args = parser.parse_args()
    
    # Validate arguments
    actions = sum([bool(args.all), bool(args.glob), bool(args.url), bool(args.retry)])
    if actions == 0:
        parser.error('Must specify one of: --all, --glob, --url, or --retry')
    elif actions > 1:
        parser.error('Can only specify one action at a time')
    
    # Create scraper
    scraper = TypstScraper(output_dir=args.output, concurrent=args.concurrent)
    
    # Run appropriate action
    start_time = time.time()
    
    try:
        if args.all:
            results = await scraper.run_all()
        elif args.glob:
            results = await scraper.run_glob(args.glob)
        elif args.url:
            results = [await scraper.run_url(args.url)]
        elif args.retry:
            results = await scraper.run_retry()
        
        # Save state and create index
        scraper.save_state()
        scraper.create_index()
        
        # Summary
        duration = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Completed in {duration:.2f} seconds")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total visited: {len(scraper.visited_urls)}")
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        scraper.save_state()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        scraper.save_state()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
