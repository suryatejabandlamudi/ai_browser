"""
Gmail & Calendar Integration for AI Browser
Critical feature to compete with Perplexity Comet
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@dataclass
class EmailMessage:
    id: str
    subject: str
    sender: str
    recipient: str
    body: str
    timestamp: datetime
    labels: List[str]
    thread_id: str
    unread: bool = False

@dataclass
class CalendarEvent:
    id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    attendees: List[str]
    location: Optional[str] = None
    meeting_link: Optional[str] = None

class GoogleWorkspaceIntegration:
    """Complete Gmail and Calendar integration like Perplexity Comet"""
    
    def __init__(self, credentials_file: str = "credentials.json"):
        self.credentials_file = credentials_file
        self.credentials = None
        self.gmail_service = None
        self.calendar_service = None
        
        # OAuth scopes for Gmail and Calendar
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.compose',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/calendar.events',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/userinfo.email'
        ]
        
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Google services with OAuth"""
        try:
            # Load existing credentials or start OAuth flow
            if not await self._load_credentials():
                await self._oauth_flow()
            
            # Build Gmail service
            self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
            
            # Build Calendar service  
            self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
            
            self.initialized = True
            logging.info("Google Workspace integration initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize Google integration: {e}")
            return False
    
    async def _load_credentials(self) -> bool:
        """Load existing credentials from token file"""
        try:
            token_file = "token.json"
            if Path(token_file).exists():
                self.credentials = Credentials.from_authorized_user_file(token_file, self.scopes)
                
                # Refresh if expired
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    # Save refreshed credentials
                    with open(token_file, 'w') as token:
                        token.write(self.credentials.to_json())
                
                return self.credentials and self.credentials.valid
        except Exception as e:
            logging.error(f"Error loading credentials: {e}")
        
        return False
    
    async def _oauth_flow(self):
        """Start OAuth flow for user authentication"""
        flow = Flow.from_client_secrets_file(
            self.credentials_file, 
            scopes=self.scopes,
            redirect_uri='http://localhost:8080/oauth/callback'
        )
        
        # Start local server for OAuth callback
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        logging.info(f"Please visit this URL to authorize the application: {auth_url}")
        
        # In a real implementation, you'd handle the callback
        # For now, assume user completes OAuth and we get the code
        # This would be integrated with the browser's OAuth handling
        
        # Placeholder for OAuth completion
        # flow.fetch_token(authorization_response=callback_url)
        # self.credentials = flow.credentials
        
        # Save credentials
        with open('token.json', 'w') as token:
            token.write(self.credentials.to_json())
    
    # GMAIL FUNCTIONALITY
    
    async def get_recent_emails(self, limit: int = 10, query: str = None) -> List[EmailMessage]:
        """Get recent emails with AI context parsing"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Build Gmail query
            gmail_query = query or 'in:inbox'
            
            # Get message list
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=gmail_query,
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            email_list = []
            
            for msg_ref in messages:
                msg = self.gmail_service.users().messages().get(
                    userId='me',
                    id=msg_ref['id'],
                    format='full'
                ).execute()
                
                email_obj = self._parse_email_message(msg)
                email_list.append(email_obj)
            
            return email_list
            
        except HttpError as e:
            logging.error(f"Gmail API error: {e}")
            return []
    
    def _parse_email_message(self, msg: dict) -> EmailMessage:
        """Parse Gmail API message into EmailMessage object"""
        headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
        
        # Extract body
        body = self._extract_email_body(msg['payload'])
        
        # Parse timestamp
        timestamp = datetime.fromtimestamp(int(msg['internalDate']) / 1000)
        
        return EmailMessage(
            id=msg['id'],
            subject=headers.get('Subject', 'No Subject'),
            sender=headers.get('From', 'Unknown'),
            recipient=headers.get('To', 'Unknown'),
            body=body,
            timestamp=timestamp,
            labels=msg.get('labelIds', []),
            thread_id=msg['threadId'],
            unread='UNREAD' in msg.get('labelIds', [])
        )
    
    def _extract_email_body(self, payload: dict) -> str:
        """Extract email body from Gmail payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    async def send_email(self, to: str, subject: str, body: str, cc: str = None) -> bool:
        """Send email through Gmail API"""
        if not self.initialized:
            await self.initialize()
        
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            
            message.attach(MIMEText(body, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send via Gmail API
            send_result = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logging.info(f"Email sent successfully: {send_result['id']}")
            return True
            
        except HttpError as e:
            logging.error(f"Error sending email: {e}")
            return False
    
    async def reply_to_email(self, message_id: str, reply_body: str) -> bool:
        """Reply to an existing email"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get original message
            original = self.gmail_service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = {h['name']: h['value'] for h in original['payload']['headers']}
            
            # Create reply
            reply = MIMEText(reply_body)
            reply['to'] = headers.get('From')
            reply['subject'] = f"Re: {headers.get('Subject', '')}"
            reply['in-reply-to'] = headers.get('Message-ID')
            reply['references'] = headers.get('Message-ID')
            
            # Send reply
            raw_reply = base64.urlsafe_b64encode(reply.as_bytes()).decode()
            
            result = self.gmail_service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_reply,
                    'threadId': original['threadId']
                }
            ).execute()
            
            return True
            
        except HttpError as e:
            logging.error(f"Error replying to email: {e}")
            return False
    
    # CALENDAR FUNCTIONALITY
    
    async def get_upcoming_events(self, limit: int = 10, days_ahead: int = 7) -> List[CalendarEvent]:
        """Get upcoming calendar events"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Calculate time range
            now = datetime.utcnow()
            time_max = now + timedelta(days=days_ahead)
            
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=limit,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            calendar_events = []
            
            for event in events:
                calendar_event = self._parse_calendar_event(event)
                calendar_events.append(calendar_event)
            
            return calendar_events
            
        except HttpError as e:
            logging.error(f"Calendar API error: {e}")
            return []
    
    def _parse_calendar_event(self, event: dict) -> CalendarEvent:
        """Parse Google Calendar event into CalendarEvent object"""
        # Parse start/end times
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
        
        # Extract attendees
        attendees = []
        if 'attendees' in event:
            attendees = [a.get('email', '') for a in event['attendees']]
        
        # Look for meeting links
        meeting_link = None
        if 'conferenceData' in event:
            for entry_point in event['conferenceData'].get('entryPoints', []):
                if entry_point.get('entryPointType') == 'video':
                    meeting_link = entry_point.get('uri')
                    break
        
        return CalendarEvent(
            id=event['id'],
            title=event.get('summary', 'No Title'),
            description=event.get('description', ''),
            start_time=start_dt,
            end_time=end_dt,
            attendees=attendees,
            location=event.get('location'),
            meeting_link=meeting_link
        )
    
    async def create_calendar_event(self,
                                  title: str,
                                  start_time: datetime,
                                  end_time: datetime,
                                  description: str = '',
                                  attendees: List[str] = None,
                                  location: str = None) -> Optional[str]:
        """Create new calendar event"""
        if not self.initialized:
            await self.initialize()
        
        try:
            event_data = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/New_York'  # Should be dynamic
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/New_York'
                }
            }
            
            if location:
                event_data['location'] = location
            
            if attendees:
                event_data['attendees'] = [{'email': email} for email in attendees]
            
            # Create event
            event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event_data,
                sendUpdates='all'
            ).execute()
            
            logging.info(f"Calendar event created: {event['id']}")
            return event['id']
            
        except HttpError as e:
            logging.error(f"Error creating calendar event: {e}")
            return None
    
    async def search_emails(self, query: str, limit: int = 20) -> List[EmailMessage]:
        """AI-powered email search"""
        return await self.get_recent_emails(limit=limit, query=query)
    
    async def get_email_summary(self, days_back: int = 1) -> Dict[str, Any]:
        """Get email summary for AI context"""
        try:
            # Get recent emails
            recent_emails = await self.get_recent_emails(limit=50)
            
            # Filter by time
            cutoff = datetime.now() - timedelta(days=days_back)
            filtered_emails = [e for e in recent_emails if e.timestamp > cutoff]
            
            # Generate summary
            summary = {
                'total_emails': len(filtered_emails),
                'unread_count': len([e for e in filtered_emails if e.unread]),
                'top_senders': self._get_top_senders(filtered_emails),
                'recent_subjects': [e.subject for e in filtered_emails[:10]]
            }
            
            return summary
            
        except Exception as e:
            logging.error(f"Error generating email summary: {e}")
            return {}
    
    def _get_top_senders(self, emails: List[EmailMessage]) -> List[Dict[str, Any]]:
        """Get top email senders"""
        sender_counts = {}
        for email in emails:
            sender = email.sender
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        
        # Sort by count
        sorted_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [{'sender': s[0], 'count': s[1]} for s in sorted_senders[:5]]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of Google integration"""
        try:
            if not self.initialized:
                return {'status': 'not_initialized'}
            
            # Test Gmail access
            gmail_test = self.gmail_service.users().getProfile(userId='me').execute()
            
            # Test Calendar access
            calendar_test = self.calendar_service.calendarList().list().execute()
            
            return {
                'status': 'healthy',
                'gmail_accessible': True,
                'calendar_accessible': True,
                'user_email': gmail_test.get('emailAddress')
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }