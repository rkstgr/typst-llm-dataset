#!/usr/bin/env python3
"""
Typst Forum Questions Category Scraper
Scrapes all topics from the questions category with pagination support,
resume capability, and duplicate handling.
"""

import json
import os
import time
import requests
from datetime import datetime
from typing import Dict, List, Set
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TypstForumScraper:
    def __init__(self):
        self.base_url = "https://forum.typst.app"
        self.delay = 1  # 1 second delay between requests
        self.output_file = "typst-forum/questions.json"
        self.session = requests.Session()

    def ensure_output_directory(self):
        """Create output directory if it doesn't exist."""
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

    def load_existing_data(self) -> Dict:
        """Load existing data from file if it exists."""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded existing data with {len(data.get('topics', []))} topics")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load existing data: {e}")

        return {
            'scraped_at': None,
            'total_topics': 0,
            'topics': [],
            'metadata': {
                'base_url': self.base_url,
                'category': 'questions',
                'category_id': 5
            }
        }

    def get_existing_topic_ids(self, data: Dict) -> Set[int]:
        """Get set of existing topic IDs to avoid duplicates."""
        return {topic['id'] for topic in data.get('topics', [])}

    def fetch_page(self, page: int = 0) -> Dict:
        """Fetch a single page of topics."""
        url = f"{self.base_url}/c/questions/5.json"
        params = {'page': page} if page > 0 else {}

        try:
            logger.info(f"Fetching page {page}...")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            raise

    def save_data(self, data: Dict):
        """Save data to JSON file."""
        self.ensure_output_directory()
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {data['total_topics']} topics to {self.output_file}")
        except IOError as e:
            logger.error(f"Error saving data: {e}")
            raise

    def scrape_all_topics(self):
        """Main scraping function with pagination and resume support."""
        # Load existing data
        data = self.load_existing_data()
        existing_ids = self.get_existing_topic_ids(data)
        new_topics_count = 0

        page = 0
        has_more_pages = True

        logger.info("Starting scrape...")

        while has_more_pages:
            try:
                # Fetch current page
                page_data = self.fetch_page(page)

                # Extract topics from current page
                topics = page_data.get('topic_list', {}).get('topics', [])

                if not topics:
                    logger.info("No topics found on this page, stopping.")
                    break

                # Process topics and add new ones
                page_new_topics = 0
                for topic in topics:
                    topic_id = topic.get('id')
                    if topic_id and topic_id not in existing_ids:
                        data['topics'].append(topic)
                        existing_ids.add(topic_id)
                        page_new_topics += 1
                        new_topics_count += 1

                logger.info(f"Page {page}: Found {len(topics)} topics, {page_new_topics} new")

                # Check if there are more pages
                more_topics_url = page_data.get('topic_list', {}).get('more_topics_url')
                has_more_pages = bool(more_topics_url)

                if has_more_pages:
                    page += 1
                    # Respectful delay between requests
                    time.sleep(self.delay)
                else:
                    logger.info("No more pages available.")

            except KeyboardInterrupt:
                logger.info("Scraping interrupted by user. Saving current progress...")
                break
            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                logger.info("Saving current progress before stopping...")
                break

        # Update metadata
        data['scraped_at'] = datetime.now().isoformat()
        data['total_topics'] = len(data['topics'])

        # Sort topics by creation date (newest first)
        data['topics'].sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # Save final data
        self.save_data(data)

        logger.info(f"Scraping completed! Added {new_topics_count} new topics.")
        logger.info(f"Total topics in dataset: {data['total_topics']}")

        return data

def main():
    """Main function to run the scraper."""
    scraper = TypstForumScraper()

    try:
        result = scraper.scrape_all_topics()
        print(f"\nScraping completed successfully!")
        print(f"Total topics: {result['total_topics']}")
        print(f"Output file: {scraper.output_file}")

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
