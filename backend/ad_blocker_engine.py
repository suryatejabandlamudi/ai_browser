"""
AI-Powered Ad Blocker Engine
Uses local AI to detect and block ads, trackers, and unwanted content
"""

import re
import json
import asyncio
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class BlockRule:
    pattern: str
    rule_type: str  # "domain", "url", "element", "ai_detected"
    category: str   # "ads", "tracking", "malware", "annoyance"
    confidence: float = 1.0
    source: str = "manual"

class AIAdBlocker:
    """Privacy-first ad blocker with AI enhancement"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        
        # Core blocking lists
        self.domain_blocklist: Set[str] = set()
        self.url_patterns: List[re.Pattern] = []
        self.element_selectors: Set[str] = set()
        self.ai_rules: List[BlockRule] = []
        
        # Statistics
        self.blocked_requests = 0
        self.blocked_elements = 0
        self.ai_detections = 0
        
        # Load default rules
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load comprehensive ad blocking rules"""
        
        # Major ad/tracking domains
        ad_domains = [
            "googleadservices.com", "googlesyndication.com", "doubleclick.net",
            "facebook.com/tr", "analytics.google.com", "google-analytics.com",
            "scorecardresearch.com", "quantserve.com", "outbrain.com",
            "taboola.com", "amazon-adsystem.com", "adsystem.amazon.com",
            "bing.com/fd/ls/GLinkPing.aspx", "bat.bing.com", "clarity.ms",
            "hotjar.com", "fullstory.com", "loggly.com", "bugsnag.com",
            "sentry.io", "rollbar.com", "trackjs.com", "errorception.com"
        ]
        self.domain_blocklist.update(ad_domains)
        
        # URL patterns for ads
        url_patterns = [
            r'/ads?[/\?]', r'/advertisement', r'/adsense', r'/adnxs',
            r'/googlesyndication', r'/googleadservices', r'/doubleclick',
            r'/facebook\.com/tr', r'/analytics', r'/tracking', r'/metrics',
            r'/telemetry', r'/beacon', r'/collect\?', r'/track\?',
            r'/pixel\.gif', r'/clear\.gif', r'/1x1\.gif', r'/spacer\.gif',
            r'/adform', r'/adsystem', r'/adserver', r'/adservice',
            r'/pubads', r'/pagead', r'/ads\.yahoo', r'/yads\.yahoo'
        ]
        self.url_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in url_patterns]
        
        # CSS selectors for ad elements
        ad_selectors = {
            '[id*="ad"]', '[class*="ad"]', '[id*="banner"]', '[class*="banner"]',
            '[id*="sponsor"]', '[class*="sponsor"]', '.advertisement', '#advertisement',
            '.ads', '#ads', '.ad-container', '.ad-wrapper', '.ad-banner',
            '.google-ads', '.amazon-ads', '.facebook-ads', '.twitter-ads',
            '[data-ad]', '[data-ads]', '[data-advertisement]'
        }
        self.element_selectors.update(ad_selectors)
        
        logger.info("Loaded default ad blocking rules", 
                   domains=len(self.domain_blocklist),
                   patterns=len(self.url_patterns), 
                   selectors=len(self.element_selectors))
    
    async def should_block_request(self, url: str, request_type: str = "other") -> Dict[str, any]:
        """Check if a request should be blocked"""
        
        # Quick domain check
        domain_result = self._check_domain_blocklist(url)
        if domain_result["blocked"]:
            self.blocked_requests += 1
            return domain_result
        
        # URL pattern check
        pattern_result = self._check_url_patterns(url)
        if pattern_result["blocked"]:
            self.blocked_requests += 1
            return pattern_result
        
        # AI-enhanced detection for suspicious requests
        if self.ai_client and self._looks_suspicious(url):
            ai_result = await self._ai_analyze_request(url, request_type)
            if ai_result["blocked"]:
                self.ai_detections += 1
                return ai_result
        
        return {"blocked": False, "reason": "allowed", "rule_type": None}
    
    def _check_domain_blocklist(self, url: str) -> Dict[str, any]:
        """Check against known ad/tracking domains"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
            
            for blocked_domain in self.domain_blocklist:
                if blocked_domain in domain:
                    return {
                        "blocked": True,
                        "reason": f"Blocked domain: {blocked_domain}",
                        "rule_type": "domain",
                        "category": "ads/tracking"
                    }
        except Exception:
            pass
        
        return {"blocked": False}
    
    def _check_url_patterns(self, url: str) -> Dict[str, any]:
        """Check against suspicious URL patterns"""
        for pattern in self.url_patterns:
            if pattern.search(url):
                return {
                    "blocked": True,
                    "reason": f"Matched pattern: {pattern.pattern}",
                    "rule_type": "url_pattern",
                    "category": "ads"
                }
        
        return {"blocked": False}
    
    def _looks_suspicious(self, url: str) -> bool:
        """Quick heuristic to identify suspicious requests for AI analysis"""
        suspicious_indicators = [
            "track", "analytic", "metric", "telemetry", "beacon",
            "pixel", "impression", "click", "conversion", "attribution"
        ]
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in suspicious_indicators)
    
    async def _ai_analyze_request(self, url: str, request_type: str) -> Dict[str, any]:
        """Use AI to analyze potentially suspicious requests"""
        try:
            analysis_prompt = f"""Analyze this web request for ad/tracking behavior:

URL: {url}
Request Type: {request_type}

Is this likely an advertisement, tracker, or privacy-invasive request?
Consider:
1. Domain reputation
2. URL patterns
3. Request characteristics
4. Privacy implications

Respond with JSON:
{{
    "is_suspicious": true/false,
    "confidence": 0.95,
    "category": "ads|tracking|analytics|legitimate",
    "reason": "brief explanation"
}}"""

            ai_response = await self.ai_client.chat(analysis_prompt, max_tokens=200)
            
            # Parse AI response
            content = ai_response.get("content", "")
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content
            
            analysis = json.loads(json_str)
            
            if analysis.get("is_suspicious", False) and analysis.get("confidence", 0) > 0.7:
                # Create AI rule for future use
                ai_rule = BlockRule(
                    pattern=url,
                    rule_type="ai_detected",
                    category=analysis.get("category", "ads"),
                    confidence=analysis.get("confidence", 0.8),
                    source="ai_analysis"
                )
                self.ai_rules.append(ai_rule)
                
                return {
                    "blocked": True,
                    "reason": f"AI detected: {analysis.get('reason', 'suspicious request')}",
                    "rule_type": "ai_analysis",
                    "category": analysis.get("category", "ads"),
                    "confidence": analysis.get("confidence", 0.8)
                }
        
        except Exception as e:
            logger.warning("AI analysis failed", error=str(e))
        
        return {"blocked": False}
    
    def get_element_blocking_css(self) -> str:
        """Generate CSS to hide ad elements"""
        css_rules = []
        
        # Hide known ad selectors
        for selector in self.element_selectors:
            css_rules.append(f"{selector} {{ display: none !important; visibility: hidden !important; }}")
        
        # Additional privacy-focused hiding
        privacy_selectors = [
            # Social media widgets
            '.fb-like', '.twitter-follow-button', '.g-plusone',
            '.linkedin-share', '.pinterest-save',
            # Cookie banners (some)
            '[class*="cookie-banner"]', '[id*="cookie-notice"]',
            # Newsletter popups
            '[class*="newsletter-popup"]', '[class*="email-signup"]'
        ]
        
        for selector in privacy_selectors:
            css_rules.append(f"{selector} {{ display: none !important; }}")
        
        return "\n".join(css_rules)
    
    async def analyze_page_content(self, html: str, url: str) -> Dict[str, any]:
        """AI-powered analysis of page content for ads/trackers"""
        if not self.ai_client:
            return {"ads_detected": [], "trackers_detected": [], "privacy_score": 0.5}
        
        try:
            # Extract scripts and suspicious elements
            import re
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
            external_scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            
            analysis_prompt = f"""Analyze this webpage for privacy/tracking concerns:

URL: {url}
External Scripts: {len(external_scripts)}
Script Sources: {', '.join(external_scripts[:10])}

Identify:
1. Ad networks present
2. Tracking scripts
3. Privacy-invasive elements
4. Overall privacy score (0-1, higher = more private)

Respond with JSON:
{{
    "ads_detected": ["script1.js", "ad-network.com"],
    "trackers_detected": ["analytics.js", "tracking-pixel"],
    "privacy_score": 0.3,
    "recommendations": ["Block script X", "Hide element Y"]
}}"""

            ai_response = await self.ai_client.chat(analysis_prompt, max_tokens=400)
            
            content = ai_response.get("content", "")
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                analysis = json.loads(content[json_start:json_end].strip())
            else:
                analysis = json.loads(content)
            
            return analysis
            
        except Exception as e:
            logger.error("Page content analysis failed", error=str(e))
            return {"ads_detected": [], "trackers_detected": [], "privacy_score": 0.5}
    
    def get_statistics(self) -> Dict[str, any]:
        """Get ad blocking statistics"""
        return {
            "blocked_requests": self.blocked_requests,
            "blocked_elements": self.blocked_elements,
            "ai_detections": self.ai_detections,
            "total_rules": len(self.domain_blocklist) + len(self.url_patterns) + len(self.element_selectors),
            "ai_rules": len(self.ai_rules)
        }
    
    def add_custom_rule(self, pattern: str, rule_type: str, category: str):
        """Add custom blocking rule"""
        if rule_type == "domain":
            self.domain_blocklist.add(pattern.lower())
        elif rule_type == "url":
            self.url_patterns.append(re.compile(pattern, re.IGNORECASE))
        elif rule_type == "element":
            self.element_selectors.add(pattern)
        
        logger.info("Added custom rule", pattern=pattern, type=rule_type, category=category)

# Integration with browser extension
async def create_ad_blocker(ai_client):
    """Factory function to create ad blocker instance"""
    return AIAdBlocker(ai_client)