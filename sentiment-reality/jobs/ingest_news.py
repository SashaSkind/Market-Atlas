import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import os
from pathlib import Path
from dotenv import load_dotenv
from newspaper import Article
import yfinance as yf

# Load .env from project root (one level up from jobs/)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


def get_stock_price_data(stock_symbol: str) -> Dict[str, Any]:
    """
    Fetch current stock price and related data using yfinance.
    
    Args:
        stock_symbol (str): Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
    
    Returns:
        Dict containing:
            - current_price (float): Current stock price
            - price_timestamp (str): ISO format timestamp of price
            - price_change (float): Dollar change from previous close
            - price_direction (str): 'up', 'down', or 'neutral'
    """
    try:
        ticker = yf.Ticker(stock_symbol)
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        previous_close = info.get('previousClose')
        
        if not current_price:
            return {
                'current_price': None,
                'price_timestamp': datetime.now(timezone.utc).isoformat(),
                'price_change': None,
                'price_direction': 'unknown'
            }
        
        # Calculate price change
        price_change = None
        price_direction = 'neutral'
        
        if previous_close:
            price_change = round(current_price - previous_close, 2)
            if price_change > 0:
                price_direction = 'up'
            elif price_change < 0:
                price_direction = 'down'
        
        return {
            'current_price': round(current_price, 2),
            'price_timestamp': datetime.now(timezone.utc).isoformat(),
            'price_change': price_change,
            'price_direction': price_direction
        }
    
    except Exception as e:
        print(f"Error fetching stock price for {stock_symbol}: {e}")
        return {
            'current_price': None,
            'price_timestamp': datetime.now(timezone.utc).isoformat(),
            'price_change': None,
            'price_direction': 'unknown'
        }


def get_news_data(stock_symbol: str, hours: int = 168) -> List[Dict[str, Any]]:
    """
    Fetch article information from NewsAPI for a given stock symbol from the specified timeframe.
    
    Args:
        stock_symbol (str): Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        hours (int): Number of hours to look back for articles (default: 168 = 7 days)
    
    Returns:
        List[Dict]: List of dictionaries containing:
            - url (str): Article URL
            - headline (str): Article title/headline
            - source (str): News source name
            - published_at (str): ISO format publication date
            - stock_symbol (str): The stock symbol searched
            - current_price (float): Stock price at time of fetch
            - price_timestamp (str): ISO format timestamp of price
            - price_change (float): Dollar change from previous close
            - price_direction (str): 'up', 'down', or 'neutral'
    
    Note:
        Requires NEWSAPI_KEY environment variable to be set.
        Get a free API key from https://newsapi.org/
    """
    # Get stock price data
    price_data = get_stock_price_data(stock_symbol)
    
    # Get API key from environment
    api_key = os.getenv('NEWSAPI_KEY')
    if not api_key:
        print("Error: NEWSAPI_KEY environment variable not set")
        print("Get a free API key from https://newsapi.org/")
        return []
    
    # NewsAPI endpoint
    api_url = "https://newsapi.org/v2/everything"
    
    # Calculate the date threshold based on hours parameter
    timeframe_start = (datetime.now(timezone.utc) - timedelta(hours=hours)).date().isoformat()
    
    articles_info = []
    
    try:
        # Parameters for the API request
        params = {
            'q': stock_symbol,  # Search for the stock symbol
            'from': timeframe_start,  # From specified hours ago
            'sortBy': 'publishedAt',  # Sort by published date
            'language': 'en',  # English only
            'apiKey': api_key
        }
        
        # Make the request
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Check if the request was successful
        if data.get('status') != 'ok':
            print(f"Error from NewsAPI: {data.get('message', 'Unknown error')}")
            return []
        
        # Extract article information
        articles = data.get('articles', [])
        for article in articles:
            article_url = article.get('url')
            if article_url:
                article_info = {
                    'url': article_url,
                    'headline': article.get('title', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'published_at': article.get('publishedAt', ''),
                    'stock_symbol': stock_symbol,
                    'current_price': price_data['current_price'],
                    'price_timestamp': price_data['price_timestamp'],
                    'price_change': price_data['price_change'],
                    'price_direction': price_data['price_direction']
                }
                articles_info.append(article_info)
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching articles from NewsAPI: {e}")
    except Exception as e:
        print(f"Error processing NewsAPI response: {e}")
    
    return articles_info


def get_article_text(url: str) -> str:
    """
    Extract the article text content from a given URL using newspaper3k.
    
    Args:
        url (str): The URL of the article to extract text from
    
    Returns:
        str: The article text content as plain text, or empty string if extraction fails
    """
    try:
        # Create an Article object from newspaper3k
        article = Article(url, keep_article_html=False)
        
        # Download the article
        article.download()
        
        # Parse the article content
        article.parse()
        
        # Return the extracted text
        text = article.text
        
        return text if text else ""
    
    except Exception:
        return ""


if __name__ == "__main__":
    # Example usage
    symbol = "AAPL"
    articles = get_news_data(symbol)
    
    if not articles:
        print("No articles found. Make sure NEWSAPI_KEY environment variable is set.")
        print("Get a free API key from https://newsapi.org/")
        exit(1)
    
    print(f"Found {len(articles)} articles for {symbol}\n")
    
    # Test get_article_text with the first few articles
    extracted_count = 0
    for i, article in enumerate(articles[:5]):
        print(f"Article {i + 1}:")
        print(f"  Headline: {article['headline']}")
        print(f"  Source: {article['source']}")
        print(f"  Published: {article['published_at']}")
        print(f"  Current Price: ${article['current_price']}")
        print(f"  Price Change: {article['price_change']} ({article['price_direction']})")
        print(f"  URL: {article['url']}")
        print("-" * 80)
        text = get_article_text(article['url'])
        if text:
            # Print the entire article text
            print(text)
            extracted_count += 1
        else:
            print("Could not extract article text")
        print()
        print("=" * 80)
        print()
    
    print(f"\nSuccessfully extracted {extracted_count} out of {min(5, len(articles))} articles")
