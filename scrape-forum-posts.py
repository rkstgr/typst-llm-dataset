#!/usr/bin/env python3
"""
Typst Forum Posts Scraper
Scrapes all posts from topics with accepted answers using the Discourse API.
Saves both raw markdown and cooked HTML content for each post.
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

class TypstForumPostsScraper:
    def __init__(self):
        self.base_url = "https://forum.typst.app"
        self.delay = 0.5  # 1 second delay between requests
        self.questions_file = "typst-forum/questions.json"
        self.output_dir = "typst-forum/questions"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TypstForumPostsScraper/1.0 (Educational Purpose)'
        })

    def ensure_output_directory(self):
        """Create output directory if it doesn't exist."""
        os.makedirs(self.output_dir, exist_ok=True)

    def load_questions_data(self) -> Dict:
        """Load the questions.json file containing all topics."""
        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data.get('topics', []))} topics from {self.questions_file}")
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Could not load questions data: {e}")
            raise

    def get_topics_with_accepted_answers(self, data: Dict) -> List[Dict]:
        """Filter topics that have accepted answers."""
        topics = data.get('topics', [])
        accepted_topics = [topic for topic in topics if topic.get('has_accepted_answer', False)]
        logger.info(f"Found {len(accepted_topics)} topics with accepted answers out of {len(topics)} total")
        return accepted_topics

    def get_existing_topic_files(self) -> Set[int]:
        """Get set of topic IDs that have already been scraped."""
        existing = set()
        if os.path.exists(self.output_dir):
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.json'):
                    try:
                        topic_id = int(filename.replace('.json', ''))
                        existing.add(topic_id)
                    except ValueError:
                        continue
        logger.info(f"Found {len(existing)} existing topic files")
        return existing

    def fetch_topic_posts(self, topic_id: int) -> Dict:
        """Fetch all posts for a topic using the posts endpoint with raw content."""
        try:
            # First, get the topic to understand the structure
            topic_url = f"{self.base_url}/t/{topic_id}.json"
            topic_response = self.session.get(topic_url, timeout=30)
            topic_response.raise_for_status()
            topic_data = topic_response.json()

            # Get the post stream info
            post_stream = topic_data.get('post_stream', {})
            all_post_ids = post_stream.get('stream', [])

            if not all_post_ids:
                logger.warning(f"Topic {topic_id}: No posts found in stream")
                return None

            # Fetch posts in batches of 20 with raw content
            all_posts = []
            for i in range(0, len(all_post_ids), 20):
                batch_ids = all_post_ids[i:i+20]
                posts_url = f"{self.base_url}/t/{topic_id}/posts.json"
                params = {
                    'include_raw': 'true',
                    'post_ids[]': batch_ids
                }

                logger.debug(f"Topic {topic_id}: Fetching batch {i//20 + 1} ({len(batch_ids)} posts)")
                posts_response = self.session.get(posts_url, params=params, timeout=30)
                posts_response.raise_for_status()
                posts_data = posts_response.json()

                batch_posts = posts_data.get('post_stream', {}).get('posts', [])
                all_posts.extend(batch_posts)

                # Delay between batches if more to fetch
                if i + 20 < len(all_post_ids):
                    time.sleep(self.delay)

            # Extract core fields and organize data
            processed_posts = []
            for post in all_posts:
                processed_post = {
                    'id': post.get('id'),
                    'post_number': post.get('post_number'),
                    'username': post.get('username'),
                    'name': post.get('name'),
                    'created_at': post.get('created_at'),
                    'updated_at': post.get('updated_at'),
                    'cooked': post.get('cooked'),
                    'raw': post.get('raw'),
                    'reply_to_post_number': post.get('reply_to_post_number'),
                    'reply_count': post.get('reply_count'),
                    'quote_count': post.get('quote_count'),
                    'like_count': post.get('actions_summary', [{}])[0].get('count', 0) if post.get('actions_summary') else 0,
                    'reads': post.get('reads'),
                    'score': post.get('score'),
                    'accepted_answer': post.get('accepted_answer', False),
                    'trust_level': post.get('trust_level'),
                    'user_id': post.get('user_id')
                }
                processed_posts.append(processed_post)

            # Create final topic data structure
            topic_with_posts = {
                'topic_metadata': {
                    'id': topic_data.get('id'),
                    'title': topic_data.get('title'),
                    'slug': topic_data.get('slug'),
                    'posts_count': topic_data.get('posts_count'),
                    'created_at': topic_data.get('created_at'),
                    'last_posted_at': topic_data.get('last_posted_at'),
                    'views': topic_data.get('views'),
                    'like_count': topic_data.get('like_count'),
                    'reply_count': topic_data.get('reply_count'),
                    'has_accepted_answer': topic_data.get('accepted_answer', {}).get('post_number') is not None,
                    'accepted_answer_post_number': topic_data.get('accepted_answer', {}).get('post_number'),
                    'accepted_answer_username': topic_data.get('accepted_answer', {}).get('username'),
                    'tags': topic_data.get('tags', []),
                    'category_id': topic_data.get('category_id'),
                    'participant_count': topic_data.get('participant_count'),
                    'word_count': topic_data.get('word_count')
                },
                'posts': processed_posts,
                'scraped_at': datetime.now().isoformat()
            }

            logger.info(f"Topic {topic_id}: Successfully fetched {len(processed_posts)} posts")
            return topic_with_posts

        except requests.RequestException as e:
            logger.error(f"Topic {topic_id}: Network error - {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Topic {topic_id}: Data parsing error - {e}")
            return None

    def save_topic_posts(self, topic_id: int, topic_data: Dict):
        """Save topic posts to individual JSON file."""
        self.ensure_output_directory()
        output_path = os.path.join(self.output_dir, f"{topic_id}.json")

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(topic_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved topic {topic_id} to {output_path}")
        except IOError as e:
            logger.error(f"Error saving topic {topic_id}: {e}")
            raise

    def scrape_all_posts(self):
        """Main scraping function."""
        # Load questions data
        questions_data = self.load_questions_data()

        # Get topics with accepted answers
        topics_to_scrape = self.get_topics_with_accepted_answers(questions_data)

        if not topics_to_scrape:
            logger.warning("No topics with accepted answers found!")
            return

        # Get existing topic files to skip
        existing_topic_ids = self.get_existing_topic_files()

        # Filter out already scraped topics
        remaining_topics = [
            topic for topic in topics_to_scrape
            if topic.get('id') not in existing_topic_ids
        ]

        logger.info(f"Need to scrape {len(remaining_topics)} topics "
                   f"({len(topics_to_scrape) - len(remaining_topics)} already exist)")

        if not remaining_topics:
            logger.info("All topics with accepted answers have already been scraped!")
            return

        # Start scraping
        successful = 0
        failed = 0

        for i, topic in enumerate(remaining_topics, 1):
            topic_id = topic.get('id')
            topic_title = topic.get('title', 'Unknown')

            try:
                logger.info(f"[{i}/{len(remaining_topics)}] Scraping topic {topic_id}: {topic_title[:60]}...")

                # Fetch posts for this topic
                topic_with_posts = self.fetch_topic_posts(topic_id)

                if topic_with_posts:
                    # Save to file
                    self.save_topic_posts(topic_id, topic_with_posts)
                    successful += 1
                else:
                    failed += 1
                    logger.error(f"Failed to fetch posts for topic {topic_id}")

                # Rate limiting delay
                if i < len(remaining_topics):  # Don't delay after the last topic
                    time.sleep(self.delay)

            except KeyboardInterrupt:
                logger.info("Scraping interrupted by user.")
                break
            except Exception as e:
                failed += 1
                logger.error(f"Unexpected error scraping topic {topic_id}: {e}")
                continue

        # Final summary
        logger.info("="*60)
        logger.info("SCRAPING COMPLETED")
        logger.info(f"Successfully scraped: {successful} topics")
        logger.info(f"Failed: {failed} topics")
        logger.info(f"Already existed: {len(topics_to_scrape) - len(remaining_topics)} topics")
        logger.info(f"Total topics with accepted answers: {len(topics_to_scrape)}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("="*60)

def main():
    """Main function to run the scraper."""
    scraper = TypstForumPostsScraper()

    try:
        scraper.scrape_all_posts()
        print("\nScraping completed! Check the logs above for details.")

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
