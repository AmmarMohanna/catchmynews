"""AI service using OpenAI for content analysis and categorization."""
import logging
from typing import List, Dict, Optional
import json

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered content analysis."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def summarize_article(self, title: str, content: str) -> str:
        """
        Generate a concise summary of an article.
        
        Args:
            title: Article title
            content: Article content
            
        Returns:
            Summary text
        """
        try:
            # Truncate content if too long (to save tokens)
            max_content_length = 3000
            truncated_content = content[:max_content_length] if len(content) > max_content_length else content
            
            prompt = f"""Summarize the following article in 2-3 sentences, focusing on the key points and news value:

Title: {title}

Content: {truncated_content}

Summary:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes news articles concisely."},
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
        Categorize an article and extract tags.
        
        Args:
            title: Article title
            content: Article content
            summary: Optional pre-generated summary
            
        Returns:
            Dictionary with 'categories' and 'tags' lists
        """
        try:
            text_to_analyze = summary if summary else content[:1000]
            
            prompt = f"""Analyze the following article and provide:
1. Up to 3 broad categories (e.g., Technology, Business, Health, Politics, Science, etc.)
2. Up to 5 specific tags/topics mentioned

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
                    {"role": "system", "content": "You are a helpful assistant that categorizes news articles. Always respond with valid JSON."},
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
        Calculate relevance score of an article against criteria.
        
        Args:
            article_title: Article title
            article_summary: Article summary
            criteria_keywords: List of keywords to match
            criteria_prompt: Natural language description of interests
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        try:
            # Build criteria description
            criteria_desc = ""
            if criteria_keywords:
                criteria_desc += f"Keywords: {', '.join(criteria_keywords)}\n"
            if criteria_prompt:
                criteria_desc += f"Interest: {criteria_prompt}"
            
            if not criteria_desc:
                return 0.0
            
            prompt = f"""Rate how relevant this article is to the given criteria on a scale of 0.0 to 1.0:

Article Title: {article_title}
Article Summary: {article_summary}

Criteria:
{criteria_desc}

Respond with ONLY a number between 0.0 and 1.0, where:
- 0.0 = completely irrelevant
- 0.5 = somewhat relevant
- 1.0 = highly relevant

Relevance score:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that rates article relevance. Always respond with only a number."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            score_text = response.choices[0].message.content.strip()
            score = float(score_text)
            score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
            
            logger.debug(f"Relevance score for '{article_title[:50]}...': {score}")
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

