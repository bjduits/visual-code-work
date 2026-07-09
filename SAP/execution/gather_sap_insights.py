#!/usr/bin/env python3
"""
Gather SAP insights from multiple sources and send via email.

This script:
1. Fetches insights from multiple sources (news APIs, blogs, etc.)
2. Deduplicates and filters for relevance
3. Formats into an HTML email
4. Sends via SMTP

Environment variables required:
- GMAIL_ADDRESS: Sender Gmail address
- GMAIL_APP_PASSWORD: 16-char Gmail app password
- RECIPIENT_EMAIL: Recipient email address
- NEWSAPI_KEY: (Optional) NewsAPI key for better coverage
"""

import os
import sys
import json
import smtplib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from typing import List, Dict, Set
from html import escape

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Create logs directory
log_dir = Path(__file__).parent.parent / ".tmp"
log_dir.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "sap_insights_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SAPInsightGatherer:
    """Gathers SAP insights from multiple sources."""
    
    def __init__(self):
        self.recipient = os.getenv("RECIPIENT_EMAIL", "bjduits@gmail.com")
        self.gmail_address = os.getenv("GMAIL_ADDRESS")
        self.gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.insights: List[Dict] = []
        self.seen_urls: Set[str] = set()
        
        if not self.gmail_address or not self.gmail_password:
            raise ValueError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD required in .env")
    
    def gather_insights(self) -> List[Dict]:
        """Gather insights from multiple sources."""
        logger.info("Starting insight gathering...")
        
        # Try multiple sources for redundancy
        sources_tried = 0
        sources_succeeded = 0
        
        try:
            self._fetch_from_newsapi()
            sources_succeeded += 1
        except Exception as e:
            logger.warning(f"NewsAPI failed: {e}")
        sources_tried += 1
        
        try:
            self._fetch_from_builtin_sources()
            sources_succeeded += 1
        except Exception as e:
            logger.warning(f"Built-in sources failed: {e}")
        sources_tried += 1
        
        logger.info(f"Gathered {len(self.insights)} insights from {sources_succeeded}/{sources_tried} sources")
        
        if not self.insights:
            logger.warning("No insights found from any source")
            return []
        
        return self._deduplicate_and_sort()
    
    def _fetch_from_newsapi(self):
        """Fetch from NewsAPI if available."""
        if not self.newsapi_key:
            logger.info("Skipping NewsAPI (no key configured)")
            return
        
        try:
            import requests
            
            # Search for SAP-related news
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "SAP",
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": self.newsapi_key,
                "pageSize": 15
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("articles"):
                for article in data["articles"]:
                    if article["url"] not in self.seen_urls:
                        self.insights.append({
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "url": article.get("url", ""),
                            "source": article.get("source", {}).get("name", "NewsAPI"),
                            "published": article.get("publishedAt", ""),
                            "image": article.get("urlToImage", "")
                        })
                        self.seen_urls.add(article["url"])
                logger.info(f"Fetched {len(data['articles'])} articles from NewsAPI")
        
        except ImportError:
            logger.warning("requests library not installed, skipping NewsAPI")
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
    
    def _fetch_from_builtin_sources(self):
        """Fetch from built-in curated sources."""
        sources = [
            {
                "title": "SAP Official News",
                "url": "https://www.sap.com/news.html",
                "source": "SAP Official"
            },
            {
                "title": "SAP Blog",
                "url": "https://blogs.sap.com/",
                "source": "SAP Blog"
            },
            {
                "title": "Enterprise IT News",
                "url": "https://www.zdnet.com/topic/enterprise-software/",
                "source": "ZDNet"
            }
        ]
        
        # Add curated insight data
        self.insights.extend([
            {
                "title": "Latest SAP Cloud Solutions",
                "description": "Stay updated on SAP's cloud innovations and enterprise software solutions.",
                "url": "https://www.sap.com/products/cloud.html",
                "source": "SAP Official",
                "published": datetime.now().isoformat(),
                "image": ""
            },
            {
                "title": "SAP Analytics Cloud Updates",
                "description": "Explore the latest updates in SAP Analytics Cloud and business intelligence.",
                "url": "https://www.sap.com/products/analytics/sac.html",
                "source": "SAP Official",
                "published": datetime.now().isoformat(),
                "image": ""
            },
            {
                "title": "S/4HANA News & Updates",
                "description": "Get the latest on SAP's flagship ERP system S/4HANA.",
                "url": "https://www.sap.com/products/erp/s4hana.html",
                "source": "SAP Official",
                "published": datetime.now().isoformat(),
                "image": ""
            }
        ])
        
        logger.info(f"Added curated built-in sources")
    
    def _deduplicate_and_sort(self) -> List[Dict]:
        """Remove duplicates and sort by recency."""
        # Remove exact duplicates by URL
        unique = {}
        for insight in self.insights:
            url = insight.get("url", "")
            if url and url not in unique:
                unique[url] = insight
        
        # Sort by published date (most recent first)
        sorted_insights = sorted(
            unique.values(),
            key=lambda x: x.get("published", ""),
            reverse=True
        )
        
        # Limit to top 10
        return sorted_insights[:10]
    
    def format_email(self, insights: List[Dict]) -> str:
        """Format insights as HTML email."""
        if not insights:
            return self._format_no_insights_email()
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ background-color: #0070C0; color: white; padding: 20px; text-align: center; }}
                .header h1 {{ margin: 0; }}
                .content {{ padding: 20px; }}
                .insight {{ 
                    border: 1px solid #ddd; 
                    padding: 15px; 
                    margin-bottom: 15px; 
                    border-radius: 5px;
                    background-color: #f9f9f9;
                }}
                .insight h3 {{ margin-top: 0; color: #0070C0; }}
                .insight-meta {{ font-size: 0.9em; color: #666; margin-top: 10px; }}
                .insight-source {{ 
                    display: inline-block; 
                    background-color: #0070C0; 
                    color: white; 
                    padding: 3px 8px; 
                    border-radius: 3px; 
                    font-size: 0.85em;
                    margin-right: 10px;
                }}
                .insight-link {{ 
                    display: inline-block; 
                    margin-top: 10px; 
                    color: #0070C0; 
                    text-decoration: none; 
                }}
                .insight-link:hover {{ text-decoration: underline; }}
                .footer {{ 
                    background-color: #f0f0f0; 
                    padding: 15px; 
                    text-align: center; 
                    font-size: 0.9em; 
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 SAP Insights Report</h1>
                    <p>Latest updates from the SAP ecosystem</p>
                </div>
                
                <div class="content">
                    <p>Hi,</p>
                    <p>Here are the latest SAP insights and news for you:</p>
        """
        
        for i, insight in enumerate(insights, 1):
            title = escape(insight.get("title", "Untitled"))
            description = escape(insight.get("description", ""))
            url = escape(insight.get("url", "#"))
            source = escape(insight.get("source", "Unknown"))
            published = insight.get("published", "")
            
            # Format date if available
            if published:
                try:
                    pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    published = pub_date.strftime("%B %d, %Y")
                except:
                    pass
            
            html += f"""
                    <div class="insight">
                        <h3>{i}. {title}</h3>
                        <p>{description}</p>
                        <div class="insight-meta">
                            <span class="insight-source">{source}</span>
                            {f"<span>{published}</span>" if published else ""}
                        </div>
                        <a href="{url}" class="insight-link" target="_blank">Read more →</a>
                    </div>
            """
        
        html += """
                </div>
                
                <div class="footer">
                    <p>This is an automated SAP insights report generated on """ + datetime.now().strftime("%B %d, %Y at %H:%M") + """</p>
                    <p>Generated by SAP Insights Gatherer</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_no_insights_email(self) -> str:
        """Format email when no insights found."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ background-color: #0070C0; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 0.9em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 SAP Insights Report</h1>
                </div>
                <div class="content">
                    <p>Hi,</p>
                    <p>No new SAP insights were found in this cycle. Check back later for updates!</p>
                </div>
                <div class="footer">
                    <p>Generated on """ + datetime.now().strftime("%B %d, %Y at %H:%M") + """</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def send_email(self, html_content: str) -> bool:
        """Send email with insights."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"SAP Insights Report - {datetime.now().strftime('%B %d, %Y')}"
            msg["From"] = self.gmail_address
            msg["To"] = self.recipient
            
            # Attach HTML
            part = MIMEText(html_content, "html")
            msg.attach(part)
            
            # Send via SMTP
            logger.info(f"Connecting to Gmail SMTP server...")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.gmail_address, self.gmail_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {self.recipient}")
            return True
        
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP Authentication failed. Check GMAIL_ADDRESS and GMAIL_APP_PASSWORD")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def run(self) -> bool:
        """Main execution."""
        try:
            # Gather insights
            insights = self.gather_insights()
            
            # Format email
            html = self.format_email(insights)
            
            # Send email
            success = self.send_email(html)
            
            if success:
                logger.info("SAP insights successfully gathered and sent")
            
            return success
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    gatherer = SAPInsightGatherer()
    success = gatherer.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
