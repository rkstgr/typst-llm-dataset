#!/usr/bin/env python3
"""
Typst Documentation Scraper

Usage:
    python scrape.py <url>

Example:
    python scrape.py https://typst.app/docs/reference/text/raw/

This will create a markdown file based on the URL structure.
"""

import sys
import requests
import re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

def convert_typst_html_to_markdown(html_content: str) -> str:
    """
    Convert Typst documentation HTML to clean, LLM-friendly markdown.

    Args:
        html_content: Raw HTML content from Typst documentation

    Returns:
        Clean markdown formatted string
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract main content area
    main_content = soup.find('main')
    if not main_content:
        raise ValueError("Could not find main content area")

    # Get page title from h1
    title_elem = main_content.find('h1')
    if not title_elem:
        raise ValueError("Could not find page title")

    # Extract title text, handling code elements and badges
    title_text = _extract_title(title_elem)

    # Start building markdown
    markdown_lines = [f"# {title_text} – Typst Documentation\n"]

    # Process content sequentially
    processed_elements = set()

    # Find all major sections
    sections = main_content.find_all(['h1', 'h2'])

    for i, section in enumerate(sections):
        if section in processed_elements:
            continue

        # Determine next section boundary
        next_section = sections[i + 1] if i + 1 < len(sections) else None

        # Get section content
        section_content = _get_section_content_improved(section, next_section)

        # Process section
        section_md = _process_section_improved(section, section_content)
        if section_md:
            markdown_lines.extend(section_md)

        # Mark processed elements
        processed_elements.add(section)
        processed_elements.update(section_content)

    # Add footer
    markdown_lines.append("\n---\n")
    markdown_lines.append("*This documentation is for Typst, a modern markup language for typesetting.*")

    return "\n".join(markdown_lines)

def _extract_title(title_elem) -> str:
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

def _get_section_content_improved(start_elem, end_elem) -> List:
    """Get all content between two section headers, with better boundary detection."""
    content = []
    current = start_elem.next_sibling

    while current and current != end_elem:
        if hasattr(current, 'name') and current.name:
            # Skip nested h1/h2 that might be in the content
            if current.name in ['h1', 'h2'] and current != start_elem:
                break
            content.append(current)
        current = current.next_sibling

    return content

def _process_section_improved(header, content_elements) -> List[str]:
    """Process a section with improved handling of parameters and structure."""
    lines = []

    # Extract header info
    header_id = header.get('id', '')
    header_text = _clean_text_improved(header.get_text())
    header_level = int(header.name[1]) if header.name.startswith('h') else 2

    # Handle special sections
    if header.name == 'h1' and 'summary' in header_id:
        lines.append("## Summary\n")
    elif header_id == 'parameters':
        lines.append("## Parameters\n")
        # Process parameters section specially
        param_content = _process_parameters_section(content_elements)
        if param_content:
            lines.extend(param_content)
        return lines
    elif header_id == 'definitions':
        lines.append("## Definitions\n")
        lines.append("Functions and types and can have associated definitions. These are accessed by specifying the function or type, followed by a period, and then the definition's name.\n")
    elif header.name != 'h1':
        lines.append(f"{'#' * header_level} {header_text}\n")

    # Process regular content
    for elem in content_elements:
        if elem.name == 'p':
            text = _process_paragraph_improved(elem)
            if text.strip():
                lines.append(f"{text}\n")

        elif elem.name == 'div' and 'previewed-code' in elem.get('class', []):
            code_block = _process_code_block_improved(elem)
            if code_block:
                lines.append(f"{code_block}\n")

        elif elem.name == 'div' and 'code-definition' in elem.get('class', []):
            signature = _process_function_signature_improved(elem)
            if signature:
                lines.append(f"{signature}\n")

        elif elem.name == 'details':
            example = _process_example_details_improved(elem)
            if example:
                lines.append(f"{example}\n")

        elif elem.name in ['ul', 'ol']:
            list_content = _process_list_improved(elem)
            if list_content:
                lines.append(f"{list_content}\n")

    return lines

def _process_parameters_section(content_elements) -> List[str]:
    """Process the parameters section with proper formatting."""
    lines = []

    # Look for function signature first
    for elem in content_elements:
        if elem.name == 'div' and 'code-definition' in elem.get('class', []):
            signature = _process_function_signature_improved(elem)
            if signature:
                lines.append(f"{signature}\n")
            break

    # Process individual parameters
    for elem in content_elements:
        if elem.name == 'h3' and elem.get('id', '').startswith('parameters-'):
            param_md = _process_single_parameter(elem)
            if param_md:
                lines.extend(param_md)

    return lines

def _process_single_parameter(param_header) -> List[str]:
    """Process a single parameter with proper formatting."""
    lines = []

    # Extract parameter name
    code_elem = param_header.find('code')
    if not code_elem:
        return lines

    param_name = code_elem.get_text().strip()
    lines.append(f"### `{param_name}`")

    # Process additional info (type, required, etc.)
    additional_info = param_header.find_next_sibling('div', class_='additional-info')
    if additional_info:
        type_info = _extract_parameter_metadata(additional_info)
        if type_info:
            lines.extend(type_info)

    # Get parameter description
    current = param_header.next_sibling
    while current:
        if hasattr(current, 'name'):
            if current.name == 'p':
                desc = _process_paragraph_improved(current)
                if desc.strip():
                    lines.append(f"\n{desc}")
                break
            elif current.name in ['h3', 'h4'] and current.get('id', '').startswith('parameters-'):
                break
            elif current.name == 'div' and 'additional-info' in current.get('class', []):
                pass  # Skip, already processed
            elif current.name == 'details':
                example = _process_example_details_improved(current)
                if example:
                    lines.append(f"\n{example}")
                break
        current = current.next_sibling

    lines.append("")  # Add spacing
    return lines

def _extract_parameter_metadata(info_elem) -> List[str]:
    """Extract clean parameter metadata."""
    lines = []

    # Extract type information
    type_div = info_elem.find('div')
    if type_div:
        type_text = _clean_text_improved(type_div.get_text())
        lines.append(f"- **Type:** `{type_text}`")

    # Extract other properties
    properties = []
    small_elems = info_elem.find_all('small')
    for small in small_elems:
        # Get text but avoid tooltip content
        text_content = ""
        for content in small.children:
            if hasattr(content, 'name'):
                if content.name == 'span' and 'tooltip' not in content.get('class', []):
                    text_content += content.get_text()
                elif content.name not in ['div', 'svg'] and 'tooltip' not in str(content):
                    text_content += content.get_text()
            else:
                text_str = str(content).strip()
                if not text_str.startswith('<') and 'tooltip' not in text_str:
                    text_content += text_str

        text_content = text_content.strip()
        if text_content and text_content not in ['Question mark']:
            properties.append(text_content)

    # Add properties
    for prop in properties:
        if prop.lower() in ['required', 'settable', 'positional', 'named', 'variadic']:
            lines.append(f"- **{prop}**")

    # Look for default values
    default_text = info_elem.get_text()
    default_match = re.search(r'Default:\s*`([^`]+)`', default_text)
    if default_match:
        lines.append(f"- **Default:** `{default_match.group(1)}`")

    return lines

def _clean_text_improved(text: str) -> str:
    """Improved text cleaning that handles tooltips and extra content."""
    # Remove tooltip text and question marks
    text = re.sub(r'Question mark.*?(?=\w|$)', '', text, flags=re.DOTALL)
    text = re.sub(r'Element functions.*?rules\.', '', text)
    text = re.sub(r'Settable parameters.*?rule\.', '', text)
    text = re.sub(r'Parameters are.*?name\.', '', text)
    text = re.sub(r'Positional parameters.*?names\.', '', text)
    text = re.sub(r'Variadic parameters.*?times\.', '', text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())

    # Remove common unwanted phrases
    text = re.sub(r'\s*(Element|Function)\s*$', '', text)

    return text

def _process_paragraph_improved(elem) -> str:
    """Improved paragraph processing that avoids tooltip content."""
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
                    text += f"[{link_text}]({href})"
                else:
                    text += link_text
            elif content.name == 'em':
                text += f"*{content.get_text()}*"
            elif content.name == 'strong':
                text += f"**{content.get_text()}**"
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

    return _clean_text_improved(text)

def _process_code_block_improved(elem) -> Optional[str]:
    """Improved code block processing."""
    pre_elem = elem.find('pre')
    if not pre_elem:
        return None

    code_elem = pre_elem.find('code')
    if not code_elem:
        return None

    # Extract code text, preserving structure
    code_text = _extract_code_text_improved(code_elem)

    # Determine language
    lang = "typst"  # Default for Typst docs

    return f"```{lang}\n{code_text}\n```"

def _extract_code_text_improved(code_elem) -> str:
    """Extract code text with better formatting preservation."""
    # Get text content while preserving line breaks
    text = code_elem.get_text()

    # Clean up and normalize
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # Remove excessive whitespace but preserve indentation
        cleaned_line = line.rstrip()
        cleaned_lines.append(cleaned_line)

    # Remove trailing empty lines
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()

    return '\n'.join(cleaned_lines)

def _process_function_signature_improved(elem) -> Optional[str]:
    """Improved function signature processing."""
    signature_text = elem.get_text()

    # Clean up the signature
    signature_text = _clean_text_improved(signature_text)

    # Remove excessive spacing
    signature_text = re.sub(r'\s*,\s*', ', ', signature_text)
    signature_text = re.sub(r'\s*:\s*', ': ', signature_text)
    signature_text = re.sub(r'\s*\|\s*', ' | ', signature_text)

    if signature_text.strip():
        return f"**Syntax:** `{signature_text}`"
    return None

def _process_example_details_improved(elem) -> Optional[str]:
    """Improved example processing."""
    summary = elem.find('summary')
    if not summary:
        return None

    # Clean up summary text
    title = _clean_text_improved(summary.get_text()).replace('View example', 'Example')

    # Find code block
    code_div = elem.find('div', class_='previewed-code')
    if code_div:
        code_block = _process_code_block_improved(code_div)
        if code_block:
            return f"**{title}:**\n{code_block}"

    return None

def _process_list_improved(elem) -> Optional[str]:
    """Improved list processing."""
    items = []
    for li in elem.find_all('li', recursive=False):
        item_text = _process_paragraph_improved(li)
        if item_text.strip():
            marker = "-" if elem.name == 'ul' else "1."
            items.append(f"{marker} {item_text}")

    return '\n'.join(items) if items else None

def generate_filename_from_url(url: str) -> str:
    """
    Generate a markdown filename from the Typst documentation URL.

    Args:
        url: The documentation URL

    Returns:
        Generated filename (e.g., "reference-text-raw.md")
    """
    parsed = urlparse(url)
    path = parsed.path.strip('/')

    # Remove /docs/ prefix if present
    if path.startswith('docs/'):
        path = path[5:]

    # Split path and create filename
    parts = [part for part in path.split('/') if part]

    if not parts:
        return "typst-docs.md"

    # Join with hyphens and add .md extension
    filename = '-'.join(parts) + '.md'

    # Clean up any invalid filename characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    return filename

def fetch_html_content(url: str) -> str:
    """
    Fetch HTML content from the given URL.

    Args:
        url: The URL to fetch

    Returns:
        HTML content as string
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        return response.text

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch URL {url}: {e}")

def main():
    """Main function to handle command line arguments and orchestrate the scraping."""
    if len(sys.argv) != 2:
        print("Usage: python scrape.py <url>")
        print("Example: python scrape.py https://typst.app/docs/reference/text/raw/")
        sys.exit(1)

    url = sys.argv[1]

    # Validate URL
    if not url.startswith(('http://', 'https://')):
        print(f"Error: Invalid URL '{url}'. Must start with http:// or https://")
        sys.exit(1)

    if 'typst.app/docs' not in url:
        print(f"Warning: URL doesn't appear to be a Typst documentation page: {url}")

    try:
        print(f"Fetching content from: {url}")
        html_content = fetch_html_content(url)

        print("Converting HTML to markdown...")
        markdown_content = convert_typst_html_to_markdown(html_content)

        # Generate filename
        filename = generate_filename_from_url(url)

        print(f"Writing to: {filename}")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"✅ Successfully created {filename}")

        # Show some stats
        lines = len(markdown_content.split('\n'))
        chars = len(markdown_content)
        print(f"📊 Stats: {lines} lines, {chars} characters")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
