"""AI service using OpenAI for content analysis and categorization."""
import logging
from typing import List, Dict, Optional
import json

from openai import OpenAI
from fuzzywuzzy import fuzz

from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered content analysis."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def summarize_article(self, title: str, content: str) -> str:
        """
        Generate a concise summary of an article in the same language as the original.
        
        Args:
            title: Article title
            content: Article content
            
        Returns:
            Summary text in the original language
        """
        try:
            # Truncate content if too long (to save tokens)
            max_content_length = 3000
            truncated_content = content[:max_content_length] if len(content) > max_content_length else content
            
            prompt = f"""Summarize the following article in 2-3 sentences, focusing on the key points and news value.

IMPORTANT: Write the summary in the SAME LANGUAGE as the original article. If the article is in Arabic, write in Arabic. If in English, write in English. Match the original language exactly.

Title: {title}

Content: {truncated_content}

Summary (in the same language as above):"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes news articles concisely in the same language as the original text. Always preserve the original language."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary for article: {title[:50]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing article: {e}")
            return content[:200] + "..."  # Fallback to truncated content
    
    async def categorize_article(self, title: str, content: str, summary: str = None) -> Dict[str, List[str]]:
        """
        Categorize an article and extract tags in the same language as the original.
        
        Args:
            title: Article title
            content: Article content
            summary: Optional pre-generated summary
            
        Returns:
            Dictionary with 'categories' and 'tags' lists in original language
        """
        try:
            text_to_analyze = summary if summary else content[:1000]
            
            prompt = f"""Analyze the following article and provide:
1. Up to 3 broad categories (e.g., Technology, Business, Health, Politics, Science, etc.)
2. Up to 5 specific tags/topics mentioned

IMPORTANT: Provide categories and tags in the SAME LANGUAGE as the article. If the article is in Arabic, use Arabic. If in English, use English.

Article Title: {title}
Content: {text_to_analyze}

Respond in JSON format:
{{
  "categories": ["Category1", "Category2"],
  "tags": ["tag1", "tag2", "tag3"]
}}"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that categorizes news articles in the same language as the original text. Always respond with valid JSON and preserve the original language."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=150
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            result = json.loads(result_text)
            logger.info(f"Categorized article: {title[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error categorizing article: {e}")
            return {"categories": [], "tags": []}
    
    async def match_criteria(
        self, 
        article_title: str, 
        article_summary: str,
        criteria_keywords: List[str] = None,
        criteria_prompt: str = None
    ) -> float:
        """
        Calculate relevance score of an article against criteria using keyword matching.
        
        Args:
            article_title: Article title
            article_summary: Article summary
            criteria_keywords: List of keywords to match
            criteria_prompt: Natural language description (also used for keyword matching)
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        try:
            if not criteria_keywords and not criteria_prompt:
                return 0.0
            
            # Combine title and summary for matching (normalize spaces and punctuation)
            article_text = f"{article_title} {article_summary}".lower()
            # Normalize: replace non-alphanumeric with spaces for better matching
            import re
            article_text_normalized = re.sub(r'[^\w\s]', ' ', article_text)
            
            # Build list of all keywords to match
            all_keywords = []
            
            # Add explicit keywords (normalize them too)
            if criteria_keywords:
                normalized_keywords = []
                for kw in criteria_keywords:
                    # Normalize keyword: lowercase, replace dashes/underscores with spaces
                    normalized = re.sub(r'[-_]', ' ', kw.lower().strip())
                    normalized_keywords.append(normalized)
                all_keywords.extend(normalized_keywords)
            
            # Extract keywords from prompt (simple word extraction)
            if criteria_prompt:
                # Split prompt into words, filter out common words
                common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                               'of', 'with', 'by', 'from', 'about', 'as', 'is', 'are', 'was', 'were',
                               'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                               'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can',
                               'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
                               'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
                
                prompt_words = [word.lower().strip('.,!?;:()[]{}"\'-') 
                               for word in criteria_prompt.split()]
                prompt_keywords = [w for w in prompt_words 
                                  if len(w) > 2 and w not in common_words]
                all_keywords.extend(prompt_keywords)
            
            if not all_keywords:
                return 0.0
            
            # Count keyword matches with fuzzy matching
            matched_count = 0
            fuzzy_matched = 0
            
            for keyword in all_keywords:
                # Exact match (substring search)
                if keyword in article_text_normalized:
                    matched_count += 1
                else:
                    # Fuzzy match - check if similar phrases exist
                    article_words = article_text_normalized.split()
                    
                    # For multi-word keywords, check against word sequences
                    keyword_words = keyword.split()
                    if len(keyword_words) > 1:
                        # Check multi-word phrases
                        for i in range(len(article_words) - len(keyword_words) + 1):
                            phrase = ' '.join(article_words[i:i+len(keyword_words)])
                            ratio = fuzz.ratio(keyword, phrase)
                            if ratio >= 85:
                                fuzzy_matched += 1
                                break
                    else:
                        # Single word - check against individual words
                        best_ratio = 0
                        for word in article_words:
                            if len(word) > 3 and len(keyword) > 3:
                                ratio = fuzz.ratio(keyword, word)
                                if ratio > best_ratio:
                                    best_ratio = ratio
                        
                        if best_ratio >= 85:
                            fuzzy_matched += 1
            
            # Calculate score (exact matches count more than fuzzy)
            total_matches = matched_count + (fuzzy_matched * 0.7)
            score = total_matches / len(all_keywords)
            
            # Boost score if multiple matches (diminishing returns)
            if matched_count > 1:
                score = min(score * 1.2, 1.0)
            
            logger.debug(f"Keyword matching for '{article_title[:50]}...': {matched_count} exact, {fuzzy_matched} fuzzy/{len(all_keywords)} total, score={score:.2f}")
            return score
            
        except Exception as e:
            logger.error(f"Error matching criteria: {e}")
            return 0.0
    
    async def suggest_criteria(self, articles_sample: List[Dict]) -> List[Dict[str, str]]:
        """
        Suggest criteria based on scraped articles.
        
        Args:
            articles_sample: Sample of articles with title and summary
            
        Returns:
            List of suggested criteria with name and description
        """
        try:
            # Prepare sample text
            sample_text = ""
            for i, article in enumerate(articles_sample[:10], 1):  # Use up to 10 articles
                sample_text += f"{i}. {article.get('title', '')}\n"
                if article.get('summary'):
                    sample_text += f"   {article['summary'][:100]}...\n"
                sample_text += "\n"
            
            prompt = f"""Based on these news articles, suggest 5 interesting criteria/topics that someone might want to track:

{sample_text}

Respond in JSON format:
[
  {{"name": "Criteria Name", "description": "Brief description"}},
  ...
]"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that suggests search criteria. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            suggestions = json.loads(result_text)
            logger.info(f"Generated {len(suggestions)} criteria suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting criteria: {e}")
            return []
    
    async def batch_process_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Process multiple articles in batch (summarize + categorize).
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Articles with added AI-generated fields
        """
        processed = []
        
        for article in articles:
            try:
                # Generate summary
                summary = await self.summarize_article(
                    article.get('title', ''),
                    article.get('content', '')
                )
                
                # Categorize
                categorization = await self.categorize_article(
                    article.get('title', ''),
                    article.get('content', ''),
                    summary
                )
                
                # Add to article
                article['summary'] = summary
                article['categories'] = categorization.get('categories', [])
                article['tags'] = categorization.get('tags', [])
                
                processed.append(article)
                
            except Exception as e:
                logger.error(f"Error processing article {article.get('url', '')}: {e}")
                processed.append(article)
        
        return processed

