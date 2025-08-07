"""
Intelligent Form Detection and Processing System
Analyzes forms, understands field types, and provides smart auto-fill capabilities.
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)

class FieldType(Enum):
    """Types of form fields"""
    TEXT = "text"
    EMAIL = "email"
    PASSWORD = "password"
    PHONE = "phone"
    NAME = "name"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    ZIP_CODE = "zip_code"
    COUNTRY = "country"
    DATE = "date"
    NUMBER = "number"
    URL = "url"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FILE = "file"
    SEARCH = "search"
    UNKNOWN = "unknown"

class FormType(Enum):
    """Types of forms"""
    LOGIN = "login"
    REGISTRATION = "registration"
    CONTACT = "contact"
    CHECKOUT = "checkout"
    SEARCH = "search"
    NEWSLETTER = "newsletter"
    PROFILE = "profile"
    PAYMENT = "payment"
    SHIPPING = "shipping"
    SURVEY = "survey"
    UNKNOWN = "unknown"

@dataclass
class FormField:
    """Represents a form field with intelligent analysis"""
    id: str
    name: Optional[str]
    field_type: FieldType
    label: Optional[str]
    placeholder: Optional[str]
    required: bool
    current_value: Optional[str]
    selectors: List[str]
    validation_rules: List[str]
    auto_fill_suggestion: Optional[str]
    confidence: float  # Confidence in field type detection

@dataclass
class FormAnalysis:
    """Complete analysis of a form"""
    form_id: str
    form_type: FormType
    action_url: Optional[str]
    method: str
    fields: List[FormField]
    submit_buttons: List[Dict[str, Any]]
    completion_percentage: float
    validation_errors: List[str]
    auto_fill_available: bool
    estimated_completion_time: int  # seconds

class IntelligentFormProcessor:
    """Analyzes forms and provides intelligent auto-fill capabilities"""
    
    def __init__(self):
        # Field type detection patterns
        self.field_patterns = {
            FieldType.EMAIL: {
                'input_types': ['email'],
                'name_patterns': [r'email', r'e-mail', r'mail', r'user.*mail', r'login.*email'],
                'id_patterns': [r'email', r'e-mail', r'mail', r'user-email', r'login-email'],
                'placeholder_patterns': [r'email', r'e-mail', r'@', r'your.*email'],
                'label_patterns': [r'email', r'e-mail', r'email address']
            },
            FieldType.PASSWORD: {
                'input_types': ['password'],
                'name_patterns': [r'password', r'passwd', r'pwd', r'pass'],
                'id_patterns': [r'password', r'passwd', r'pwd', r'pass'],
                'placeholder_patterns': [r'password', r'enter.*password'],
                'label_patterns': [r'password', r'pwd']
            },
            FieldType.NAME: {
                'input_types': ['text'],
                'name_patterns': [r'name', r'fullname', r'full.*name', r'firstname', r'lastname', r'first.*name', r'last.*name'],
                'id_patterns': [r'name', r'fullname', r'full-name', r'firstname', r'lastname'],
                'placeholder_patterns': [r'name', r'full.*name', r'first.*name', r'last.*name'],
                'label_patterns': [r'name', r'full.*name', r'first.*name', r'last.*name']
            },
            FieldType.PHONE: {
                'input_types': ['tel', 'text'],
                'name_patterns': [r'phone', r'telephone', r'mobile', r'cell', r'contact.*number'],
                'id_patterns': [r'phone', r'telephone', r'mobile', r'cell'],
                'placeholder_patterns': [r'phone', r'telephone', r'mobile', r'\(\d{3}\)', r'\d{3}-\d{3}-\d{4}'],
                'label_patterns': [r'phone', r'telephone', r'mobile', r'contact.*number']
            },
            FieldType.ADDRESS: {
                'input_types': ['text'],
                'name_patterns': [r'address', r'street', r'addr', r'location'],
                'id_patterns': [r'address', r'street', r'addr'],
                'placeholder_patterns': [r'address', r'street', r'location'],
                'label_patterns': [r'address', r'street', r'location']
            },
            FieldType.ZIP_CODE: {
                'input_types': ['text'],
                'name_patterns': [r'zip', r'postal', r'postcode', r'zip.*code', r'postal.*code'],
                'id_patterns': [r'zip', r'postal', r'postcode', r'zip-code'],
                'placeholder_patterns': [r'zip', r'postal', r'postcode', r'\d{5}'],
                'label_patterns': [r'zip', r'postal', r'zip.*code', r'postal.*code']
            }
        }
        
        # Form type detection patterns
        self.form_type_patterns = {
            FormType.LOGIN: {
                'url_patterns': [r'login', r'signin', r'sign-in', r'auth'],
                'field_combinations': [['email', 'password'], ['username', 'password']],
                'button_text': [r'login', r'sign.*in', r'log.*in', r'enter'],
                'keywords': ['login', 'signin', 'authenticate', 'sign in']
            },
            FormType.REGISTRATION: {
                'url_patterns': [r'register', r'signup', r'sign-up', r'join'],
                'field_combinations': [['email', 'password', 'name'], ['username', 'password', 'email']],
                'button_text': [r'register', r'sign.*up', r'create.*account', r'join'],
                'keywords': ['register', 'signup', 'create account', 'join']
            },
            FormType.CONTACT: {
                'url_patterns': [r'contact', r'support', r'feedback'],
                'field_combinations': [['name', 'email', 'message'], ['email', 'subject', 'message']],
                'button_text': [r'send', r'submit', r'contact', r'send.*message'],
                'keywords': ['contact', 'support', 'feedback', 'message']
            },
            FormType.CHECKOUT: {
                'url_patterns': [r'checkout', r'payment', r'order', r'cart'],
                'field_combinations': [['name', 'email', 'address'], ['card', 'cvv', 'expiry']],
                'button_text': [r'order', r'checkout', r'complete.*order', r'pay', r'purchase'],
                'keywords': ['checkout', 'payment', 'order', 'billing', 'shipping']
            }
        }
        
        # Auto-fill data (in real implementation, this would come from user preferences)
        self.user_data = {
            FieldType.NAME: "John Doe",
            FieldType.EMAIL: "john.doe@example.com",
            FieldType.PHONE: "(555) 123-4567",
            FieldType.ADDRESS: "123 Main St",
            FieldType.CITY: "Anytown",
            FieldType.STATE: "CA",
            FieldType.ZIP_CODE: "12345",
            FieldType.COUNTRY: "United States"
        }
    
    async def analyze_form(self, form_html: str, page_url: str = "") -> FormAnalysis:
        """Analyze a form and provide intelligent insights"""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(form_html, 'html.parser')
            form_element = soup.find('form') or soup  # If not wrapped in form tag
            
            logger.info("Analyzing form", url=page_url)
            
            # Extract form attributes
            form_id = form_element.get('id', f"form_{hash(form_html) % 1000}")
            action_url = form_element.get('action', '')
            method = form_element.get('method', 'GET').upper()
            
            # Analyze form fields
            fields = await self._analyze_form_fields(form_element)
            
            # Find submit buttons
            submit_buttons = self._find_submit_buttons(form_element)
            
            # Determine form type
            form_type = self._classify_form_type(form_element, fields, page_url)
            
            # Calculate completion percentage
            completion_percentage = self._calculate_completion_percentage(fields)
            
            # Check for validation errors
            validation_errors = self._detect_validation_errors(form_element)
            
            # Check auto-fill availability
            auto_fill_available = any(field.auto_fill_suggestion for field in fields)
            
            # Estimate completion time
            estimated_time = self._estimate_completion_time(fields, form_type)
            
            analysis = FormAnalysis(
                form_id=form_id,
                form_type=form_type,
                action_url=action_url,
                method=method,
                fields=fields,
                submit_buttons=submit_buttons,
                completion_percentage=completion_percentage,
                validation_errors=validation_errors,
                auto_fill_available=auto_fill_available,
                estimated_completion_time=estimated_time
            )
            
            logger.info("Form analysis completed", 
                       form_id=form_id,
                       form_type=form_type.value,
                       fields_count=len(fields),
                       completion=f"{completion_percentage:.1f}%")
            
            return analysis
            
        except Exception as e:
            logger.error("Form analysis failed", error=str(e))
            return FormAnalysis(
                form_id="error",
                form_type=FormType.UNKNOWN,
                action_url="",
                method="GET",
                fields=[],
                submit_buttons=[],
                completion_percentage=0,
                validation_errors=[str(e)],
                auto_fill_available=False,
                estimated_completion_time=0
            )
    
    async def _analyze_form_fields(self, form_element) -> List[FormField]:
        """Analyze individual form fields"""
        fields = []
        
        # Find all input elements
        input_elements = form_element.find_all(['input', 'textarea', 'select'])
        
        for i, element in enumerate(input_elements):
            try:
                # Skip hidden fields and buttons
                input_type = element.get('type', 'text').lower()
                if input_type in ['hidden', 'submit', 'button', 'reset']:
                    continue
                
                # Extract field attributes
                field_id = element.get('id', f"field_{i}")
                name = element.get('name', '')
                label = self._find_field_label(element)
                placeholder = element.get('placeholder', '')
                required = element.get('required') is not None
                current_value = element.get('value', '')
                
                # Generate selectors
                selectors = self._generate_field_selectors(element, field_id, name)
                
                # Detect field type
                field_type, confidence = self._detect_field_type(element, label, placeholder, name)
                
                # Generate validation rules
                validation_rules = self._extract_validation_rules(element)
                
                # Generate auto-fill suggestion
                auto_fill_suggestion = self._get_auto_fill_suggestion(field_type)
                
                field = FormField(
                    id=field_id,
                    name=name,
                    field_type=field_type,
                    label=label,
                    placeholder=placeholder,
                    required=required,
                    current_value=current_value,
                    selectors=selectors,
                    validation_rules=validation_rules,
                    auto_fill_suggestion=auto_fill_suggestion,
                    confidence=confidence
                )
                
                fields.append(field)
                
            except Exception as e:
                logger.warning("Failed to analyze field", error=str(e), element=str(element)[:100])
                continue
        
        return fields
    
    def _detect_field_type(self, element, label: str, placeholder: str, name: str) -> Tuple[FieldType, float]:
        """Detect the type of a form field using multiple indicators"""
        scores = {field_type: 0 for field_type in FieldType}
        
        # Check input type
        input_type = element.get('type', 'text').lower()
        
        # Direct input type mapping
        type_mapping = {
            'email': FieldType.EMAIL,
            'password': FieldType.PASSWORD,
            'tel': FieldType.PHONE,
            'url': FieldType.URL,
            'date': FieldType.DATE,
            'number': FieldType.NUMBER,
            'search': FieldType.SEARCH,
            'checkbox': FieldType.CHECKBOX,
            'radio': FieldType.RADIO,
            'file': FieldType.FILE
        }
        
        if input_type in type_mapping:
            scores[type_mapping[input_type]] += 10
        
        # Check element tag
        if element.name == 'textarea':
            scores[FieldType.TEXTAREA] += 10
        elif element.name == 'select':
            scores[FieldType.SELECT] += 10
        
        # Pattern matching on various attributes
        text_to_analyze = ' '.join([
            label or '',
            placeholder or '',
            name or '',
            element.get('id', ''),
            ' '.join(element.get('class', []))
        ]).lower()
        
        for field_type, patterns in self.field_patterns.items():
            # Check name patterns
            for pattern in patterns.get('name_patterns', []):
                if re.search(pattern, name.lower()):
                    scores[field_type] += 8
            
            # Check id patterns
            element_id = element.get('id', '')
            for pattern in patterns.get('id_patterns', []):
                if re.search(pattern, element_id.lower()):
                    scores[field_type] += 7
            
            # Check placeholder patterns
            for pattern in patterns.get('placeholder_patterns', []):
                if re.search(pattern, placeholder.lower()):
                    scores[field_type] += 6
            
            # Check label patterns
            for pattern in patterns.get('label_patterns', []):
                if re.search(pattern, label.lower()):
                    scores[field_type] += 9
        
        # Find the field type with highest score
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # Calculate confidence (normalize score)
        confidence = min(best_score / 15.0, 1.0)
        
        # If confidence is too low, default to TEXT or appropriate fallback
        if confidence < 0.3:
            if element.name == 'textarea':
                return FieldType.TEXTAREA, 1.0
            elif element.name == 'select':
                return FieldType.SELECT, 1.0
            elif input_type in ['checkbox', 'radio', 'file']:
                return type_mapping.get(input_type, FieldType.UNKNOWN), 1.0
            else:
                return FieldType.TEXT, 0.5
        
        return best_type, confidence
    
    def _find_field_label(self, element) -> Optional[str]:
        """Find the label associated with a form field"""
        # Check for explicit label
        field_id = element.get('id')
        if field_id:
            # Find label with for attribute
            form_parent = element.find_parent('form') or element.find_parent('html')
            if form_parent:
                label = form_parent.find('label', {'for': field_id})
                if label:
                    return label.get_text(strip=True)
        
        # Check for wrapping label
        label_parent = element.find_parent('label')
        if label_parent:
            label_text = label_parent.get_text(strip=True)
            # Remove the input element text to get just the label
            input_text = element.get_text(strip=True) if element.get_text() else ''
            if input_text:
                label_text = label_text.replace(input_text, '').strip()
            return label_text
        
        # Check for preceding text or elements
        previous = element.find_previous_sibling()
        if previous:
            if previous.name in ['span', 'div', 'p'] and len(previous.get_text(strip=True)) < 50:
                return previous.get_text(strip=True)
        
        return None
    
    def _generate_field_selectors(self, element, field_id: str, name: str) -> List[str]:
        """Generate multiple selector options for a field"""
        selectors = []
        
        # ID selector (most reliable)
        if element.get('id'):
            selectors.append(f"#{element['id']}")
        
        # Name selector
        if element.get('name'):
            selectors.append(f"[name='{element['name']}']")
        
        # Type selector with other attributes
        input_type = element.get('type')
        if input_type:
            selectors.append(f"input[type='{input_type}']")
        
        # Class selectors
        classes = element.get('class', [])
        if classes:
            for cls in classes[:2]:  # Limit to first 2 classes
                selectors.append(f".{cls}")
        
        # Placeholder selector
        placeholder = element.get('placeholder')
        if placeholder:
            selectors.append(f"[placeholder='{placeholder}']")
        
        # Tag selector (least specific)
        selectors.append(element.name)
        
        return selectors
    
    def _extract_validation_rules(self, element) -> List[str]:
        """Extract validation rules from element attributes"""
        rules = []
        
        if element.get('required'):
            rules.append("required")
        
        if element.get('minlength'):
            rules.append(f"minlength:{element['minlength']}")
        
        if element.get('maxlength'):
            rules.append(f"maxlength:{element['maxlength']}")
        
        if element.get('pattern'):
            rules.append(f"pattern:{element['pattern']}")
        
        if element.get('min'):
            rules.append(f"min:{element['min']}")
        
        if element.get('max'):
            rules.append(f"max:{element['max']}")
        
        input_type = element.get('type', '').lower()
        if input_type == 'email':
            rules.append("email_format")
        elif input_type == 'url':
            rules.append("url_format")
        elif input_type == 'tel':
            rules.append("phone_format")
        
        return rules
    
    def _get_auto_fill_suggestion(self, field_type: FieldType) -> Optional[str]:
        """Get auto-fill suggestion for a field type"""
        return self.user_data.get(field_type)
    
    def _find_submit_buttons(self, form_element) -> List[Dict[str, Any]]:
        """Find submit buttons in the form"""
        buttons = []
        
        # Find input submit buttons
        submit_inputs = form_element.find_all('input', {'type': ['submit', 'button']})
        for btn in submit_inputs:
            buttons.append({
                'type': 'input',
                'value': btn.get('value', 'Submit'),
                'id': btn.get('id', ''),
                'name': btn.get('name', ''),
                'selector': f"input[type='{btn.get('type')}']" + (f"[name='{btn.get('name')}']" if btn.get('name') else '')
            })
        
        # Find button elements
        button_elements = form_element.find_all('button')
        for btn in button_elements:
            btn_type = btn.get('type', 'submit')
            if btn_type in ['submit', 'button']:
                buttons.append({
                    'type': 'button',
                    'value': btn.get_text(strip=True),
                    'id': btn.get('id', ''),
                    'name': btn.get('name', ''),
                    'selector': 'button' + (f"[type='{btn_type}']" if btn_type != 'submit' else '')
                })
        
        return buttons
    
    def _classify_form_type(self, form_element, fields: List[FormField], page_url: str) -> FormType:
        """Classify the type of form based on various indicators"""
        scores = {form_type: 0 for form_type in FormType}
        
        # Check URL patterns
        url_lower = page_url.lower()
        for form_type, patterns in self.form_type_patterns.items():
            for pattern in patterns.get('url_patterns', []):
                if re.search(pattern, url_lower):
                    scores[form_type] += 5
        
        # Check field combinations
        field_types = [field.field_type for field in fields]
        for form_type, patterns in self.form_type_patterns.items():
            for combination in patterns.get('field_combinations', []):
                matching_fields = 0
                for required_field in combination:
                    if any(required_field in field.field_type.value for field in fields):
                        matching_fields += 1
                
                if matching_fields >= len(combination) * 0.7:  # 70% match threshold
                    scores[form_type] += 8
        
        # Check button text
        submit_buttons = self._find_submit_buttons(form_element)
        button_text = ' '.join([btn['value'].lower() for btn in submit_buttons])
        
        for form_type, patterns in self.form_type_patterns.items():
            for pattern in patterns.get('button_text', []):
                if re.search(pattern, button_text):
                    scores[form_type] += 6
        
        # Check form content for keywords
        form_text = form_element.get_text().lower()
        for form_type, patterns in self.form_type_patterns.items():
            for keyword in patterns.get('keywords', []):
                if keyword in form_text:
                    scores[form_type] += 3
        
        # Return the form type with highest score
        best_type = max(scores, key=scores.get)
        return best_type if scores[best_type] > 0 else FormType.UNKNOWN
    
    def _calculate_completion_percentage(self, fields: List[FormField]) -> float:
        """Calculate how much of the form is already completed"""
        if not fields:
            return 0.0
        
        completed_fields = 0
        for field in fields:
            if field.current_value and field.current_value.strip():
                completed_fields += 1
        
        return (completed_fields / len(fields)) * 100
    
    def _detect_validation_errors(self, form_element) -> List[str]:
        """Detect existing validation errors on the form"""
        errors = []
        
        # Look for common error indicators
        error_selectors = [
            '.error', '.invalid', '.field-error', '.validation-error',
            '[class*="error"]', '[class*="invalid"]'
        ]
        
        for selector in error_selectors:
            error_elements = form_element.select(selector)
            for element in error_elements:
                error_text = element.get_text(strip=True)
                if error_text and len(error_text) < 200:  # Reasonable error message length
                    errors.append(error_text)
        
        return errors
    
    def _estimate_completion_time(self, fields: List[FormField], form_type: FormType) -> int:
        """Estimate time needed to complete the form (in seconds)"""
        base_time_per_field = {
            FieldType.TEXT: 5,
            FieldType.EMAIL: 8,
            FieldType.PASSWORD: 10,
            FieldType.PHONE: 8,
            FieldType.NAME: 5,
            FieldType.ADDRESS: 15,
            FieldType.TEXTAREA: 30,
            FieldType.SELECT: 3,
            FieldType.CHECKBOX: 2,
            FieldType.RADIO: 3
        }
        
        total_time = 0
        for field in fields:
            if not field.current_value:  # Only count empty fields
                field_time = base_time_per_field.get(field.field_type, 10)
                
                # Adjust for auto-fill
                if field.auto_fill_suggestion:
                    field_time *= 0.3  # Much faster with auto-fill
                
                total_time += field_time
        
        # Form type adjustments
        if form_type == FormType.CHECKOUT:
            total_time += 30  # Extra time for payment details
        elif form_type == FormType.REGISTRATION:
            total_time += 15  # Extra time for reading terms
        
        return max(total_time, 10)  # Minimum 10 seconds
    
    async def generate_auto_fill_plan(self, form_analysis: FormAnalysis) -> Dict[str, Any]:
        """Generate a plan for auto-filling the form"""
        try:
            auto_fill_actions = []
            
            for field in form_analysis.fields:
                if field.auto_fill_suggestion and not field.current_value:
                    action = {
                        'field_id': field.id,
                        'field_type': field.field_type.value,
                        'selector': field.selectors[0] if field.selectors else f"#{field.id}",
                        'value': field.auto_fill_suggestion,
                        'label': field.label or field.placeholder or field.name,
                        'confidence': field.confidence
                    }
                    auto_fill_actions.append(action)
            
            plan = {
                'form_id': form_analysis.form_id,
                'form_type': form_analysis.form_type.value,
                'actions': auto_fill_actions,
                'estimated_time': len(auto_fill_actions) * 2,  # 2 seconds per field
                'success_criteria': [
                    'All fillable fields completed',
                    'No validation errors',
                    'Form ready for submission'
                ]
            }
            
            logger.info("Auto-fill plan generated", 
                       form_id=form_analysis.form_id,
                       actions_count=len(auto_fill_actions))
            
            return plan
            
        except Exception as e:
            logger.error("Failed to generate auto-fill plan", error=str(e))
            return {'actions': [], 'estimated_time': 0}

# Global instance
form_processor = IntelligentFormProcessor()