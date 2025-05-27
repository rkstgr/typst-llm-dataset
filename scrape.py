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
from typing import Dict, List, Optional, Tuple

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
        # Process definitions content
        def_content = _process_definitions_section(content_elements)
        if def_content:
            lines.extend(def_content)
        return lines
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
    current_h3 = None
    for elem in content_elements:
        if elem.name == 'h3' and elem.get('id', '').startswith('parameters-'):
            current_h3 = elem
            param_md = _process_single_parameter_complete(elem, content_elements)
            if param_md:
                lines.extend(param_md)

    return lines

def _process_single_parameter_complete(param_header, all_elements) -> List[str]:
    """Process a single parameter with complete information."""
    lines = []

    # Extract parameter name
    code_elem = param_header.find('code')
    if not code_elem:
        return lines

    param_name = code_elem.get_text().strip()
    lines.append(f"### `{param_name}`")

    # Process additional info (type, required, etc.)
    # Look for the sibling div with class 'additional-info'
    additional_info = param_header.find_next_sibling('div', class_='additional-info')
    if additional_info:
        type_info = _extract_parameter_metadata_complete(additional_info)
        if type_info:
            lines.extend(type_info)

    # Get parameter description
    description_lines = []
    default_value = None
    current = param_header.next_sibling

    while current:
        if hasattr(current, 'name'):
            # Skip the additional-info div we already processed
            if current.name == 'div' and 'additional-info' in current.get('class', []):
                current = current.next_sibling
                continue

            # Stop at next parameter or major section
            if current.name in ['h3', 'h2'] and current.get('id', '').startswith(('parameters-', 'definitions-')):
                break

            if current.name == 'p':
                p_text = _process_paragraph_improved(current)
                if p_text.strip():
                    # Check for default value
                    default_match = re.search(r'Default:\s*`([^`]+)`', current.get_text())
                    if default_match:
                        default_value = default_match.group(1)
                        # Don't add the paragraph if it only contains the default value
                        if not p_text.replace(f"Default: `{default_value}`", "").strip():
                            current = current.next_sibling
                            continue
                    description_lines.append(p_text)

            elif current.name == 'details':
                # This is an example
                example = _process_example_details_improved(current)
                if example:
                    description_lines.append(f"\n{example}")

            elif current.name in ['ul', 'ol']:
                list_content = _process_list_improved(current)
                if list_content:
                    description_lines.append(list_content)

        current = current.next_sibling

    # Add description
    if description_lines:
        lines.append("")
        lines.extend(description_lines)

    # Add default value if found and not already added
    if default_value and not any('Default:' in line for line in lines):
        # Insert default value after type info
        insert_pos = 1  # After the parameter name
        for i, line in enumerate(lines):
            if line.startswith('- **'):
                insert_pos = i + 1

        # Only insert if we haven't already added it
        if insert_pos < len(lines):
            lines.insert(insert_pos, f"- **Default:** `{default_value}`")
        else:
            lines.append(f"- **Default:** `{default_value}`")

    lines.append("")  # Add spacing
    return lines

def _extract_parameter_metadata_complete(info_elem) -> List[str]:
    """Extract complete parameter metadata."""
    lines = []

    # Extract type information
    type_div = info_elem.find('div')
    if type_div:
        # Clean up type text
        type_parts = []
        for elem in type_div.children:
            if hasattr(elem, 'name'):
                if elem.name == 'a':
                    type_parts.append(elem.get_text().strip())
                elif elem.name not in ['svg', 'div'] and 'tooltip' not in elem.get('class', []):
                    type_parts.append(elem.get_text().strip())
            else:
                text = str(elem).strip()
                if text and text not in ['or', '|']:
                    type_parts.append(text)

        # Join with proper formatting
        type_text = ' or '.join([t for t in type_parts if t])
        if type_text:
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

    # Add properties with proper formatting
    for prop in properties:
        prop_lower = prop.lower()
        if prop_lower == 'required':
            lines.append(f"- **Required**")
        elif prop_lower == 'positional':
            lines.append(f"- **Positional**")
        elif prop_lower == 'settable':
            lines.append(f"- **Settable**")
        elif prop_lower in ['named', 'variadic']:
            lines.append(f"- **{prop.capitalize()}**")

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

    # Check if this is the first example that needs quadruple backticks
    if 'backticks' in code_text and 'Adding' in code_text:
        # This is the special case that needs quadruple backticks
        return f"````typst\n{code_text}\n````"

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
    # Get the raw text and clean it up
    signature_text = elem.get_text()

    # Clean up the signature
    signature_text = re.sub(r'\s+', ' ', signature_text)
    signature_text = re.sub(r'\s*,\s*', ', ', signature_text)
    signature_text = re.sub(r'\s*:\s*', ': ', signature_text)
    signature_text = re.sub(r'\s*\|\s*', ' | ', signature_text)
    signature_text = re.sub(r'\s*->\s*', ' -> ', signature_text)

    # Special handling for main raw function
    if 'raw(' in signature_text and 'block:' in signature_text:
        # This is the main raw function signature
        # Extract the components
        components = []

        # First parameter is the text (positional str)
        components.append('text: str')

        # Extract named parameters
        params_section = signature_text
        if 'block:' in params_section:
            components.append('block: bool')
        if 'lang:' in params_section:
            components.append('lang: none | str')
        if 'align:' in params_section:
            components.append('align: alignment')
        if 'syntaxes:' in params_section:
            components.append('syntaxes: str | bytes | array')
        if 'theme:' in params_section:
            components.append('theme: none | auto | str | bytes')
        if 'tab-size:' in params_section:
            components.append('tab-size: int')

        signature_text = f"raw({', '.join(components)}) -> content"

    # For raw.line, we need to handle the special case
    elif 'raw.line' in signature_text or 'line(' in signature_text:
        # Extract parameters more carefully
        params_match = re.search(r'\((.*?)\)', signature_text)
        if params_match:
            params = params_match.group(1)
            # These are positional parameters
            param_types = [p.strip() for p in params.split(',') if p.strip()]
            # For raw.line, parameters are (int, int, str, content)
            if len(param_types) >= 4:
                signature_text = f"raw.line(number: int, count: int, text: str, body: content) -> content"

    signature_text = signature_text.strip()

    if signature_text:
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

def _process_definitions_section(content_elements) -> List[str]:
    """Process the definitions section with proper subsection handling."""
    lines = []

    # Look for definition subsections (h3 elements with class="scoped-function")
    for elem in content_elements:
        if elem.name == 'h3' and 'scoped-function' in elem.get('class', []):
            def_content = _process_definition_subsection(elem, content_elements)
            if def_content:
                lines.extend(def_content)

    return lines

def _process_definition_subsection(def_header, all_elements) -> List[str]:
    """Process a definition subsection like raw.line."""
    lines = []

    # Extract definition name
    code_elem = def_header.find('code')
    if code_elem:
        def_name = code_elem.get_text().strip()
        lines.append(f"### `{def_name}`")

        # Check for Element badge
        if def_header.find('small'):
            lines.append("*Element function*\n")

    # Collect all content for this definition until the next h3/h2
    current = def_header.next_sibling
    description_paragraphs = []
    signature = None

    while current:
        if hasattr(current, 'name'):
            if current.name in ['h3', 'h2']:
                break  # Next section

            if current.name == 'p':
                desc = _process_paragraph_improved(current)
                if desc.strip():
                    description_paragraphs.append(desc)

            elif current.name == 'div' and 'code-definition' in current.get('class', []):
                signature = _process_function_signature_improved(current)

        current = current.next_sibling

    # Add description paragraphs (avoid duplicates)
    unique_descriptions = []
    for desc in description_paragraphs:
        if desc not in unique_descriptions:
            unique_descriptions.append(desc)

    for desc in unique_descriptions:
        lines.append(f"{desc}\n")

    # Add signature
    if signature:
        lines.append(f"{signature}\n")

    # Now process parameters
    current = def_header.next_sibling
    while current:
        if hasattr(current, 'name'):
            if current.name in ['h3', 'h2']:
                break  # Next section

            if current.name == 'h4' and current.get('id', '').startswith('definitions-'):
                # Process definition parameters
                param_content = _process_definition_parameter(current, all_elements)
                if param_content:
                    lines.extend(param_content)

        current = current.next_sibling

    return lines

def _process_definition_parameter(param_header, all_elements) -> List[str]:
    """Process a parameter within a definition."""
    lines = []

    # Extract parameter name
    code_elem = param_header.find('code')
    if code_elem:
        param_name = code_elem.get_text().strip()
        lines.append(f"#### `{param_name}`")

        # Get metadata from additional-info div
        additional_info = param_header.find_next_sibling('div', class_='additional-info')
        if additional_info:
            type_info = _extract_parameter_metadata_complete(additional_info)
            if type_info:
                lines.extend(type_info)

        # Get description - collect all paragraphs until next h4/h3/h2
        current = param_header.next_sibling
        description_paragraphs = []

        while current:
            if hasattr(current, 'name'):
                # Skip additional-info div
                if current.name == 'div' and 'additional-info' in current.get('class', []):
                    current = current.next_sibling
                    continue

                if current.name in ['h4', 'h3', 'h2']:
                    break

                if current.name == 'p':
                    desc = _process_paragraph_improved(current)
                    if desc.strip():
                        description_paragraphs.append(desc)

            current = current.next_sibling

        # Add unique descriptions
        if description_paragraphs:
            lines.append("")
            # Only add the first description to avoid duplicates
            lines.append(f"{description_paragraphs[0]}\n")

    return lines

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
