"""                                                                                                                                   
Module: security.py                                                                                                                   
Responsibility: Enterprise security layer enforcing:                                                                                  
1. Adversarial Prompt Injection and Jailbreak detection.                                                                              
2. PII (Personally Identifiable Information) masking for GDPR & DPDP compliance.                                                      
"""                                                                                                                                   
                                                                                                                                        
import re                                                                                                                             
from typing import NamedTuple                                                                                                         
                                                                                                                                        
                                                                                                                                        
class SecurityCheckResult(NamedTuple):                                                                                                
    is_safe: bool                                                                                                                     
    threat_type: str | None                                                                                                           
    reason: str | None                                                                                                                
                                                                                                                                        
                                                                                                                                        
# Canonical patterns for adversarial prompt injection                                                                                 
PROMPT_INJECTION_PATTERNS = [                                                                                                         
    r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|prompts)\b",                                               
    r"(?i)\bdisregard\s+(all\s+)?(previous|prior|system)\s+(instructions|directives)\b",                                              
    r"(?i)\byou\s+are\s+now\s+(in\s+developer\s+mode|unrestricted|dan|jailbroken)\b",                                                 
    r"(?i)\b(system\s+prompt|initial\s+instructions)\s*(leak|reveal|show|print|output)\b",                                            
    r"(?i)\b(reveal|leak|show|print|display|tell\s+me)\s+(your\s+)?(system\s+prompt|hidden\s+instructions)\b",                                                             
    r"(?i)\boverride\s+(system|policy|security)\s+(rules|guidelines)\b",                                                              
]                                                                                                                                     
                                                                                                                                        
# Regex patterns for Personally Identifiable Information (PII)                                                                        
PII_PATTERNS = [                                                                                                                      
    # Employee ID: EMP-101, EMP-999                                                                                                   
    (re.compile(r"\bEMP-\d{3,6}\b", re.IGNORECASE), "[EMPLOYEE_ID_REDACTED]"),                                                        
    # Standard Email addresses                                                                                                        
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL_REDACTED]"),                                         
    # Phone numbers (international, India, UK)                                                                                        
    (re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3,5}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b"), "[PHONE_REDACTED]"),                          
    # Salary / Compensation (INR, GBP, USD)                                                                                           
    (re.compile(r"(?i)(?:₹|£|\$|INR|GBP|USD)\s*\d{1,3}(?:,\d{2,3})*(?:\.\d{2})?"), "[COMPENSATION_REDACTED]"),                        
]                                                                                                                                     
                                                                                                                                        
                                                                                                                                        
def detect_prompt_injection(message: str) -> SecurityCheckResult:                                                                     
    """                                                                                                                               
    Scans incoming user input for jailbreaks and prompt injection attacks.                                                            
    """                                                                                                                               
    if not message or not message.strip():                                                                                            
        return SecurityCheckResult(is_safe=True, threat_type=None, reason=None)                                                       
                                                                                                                                        
    for pattern in PROMPT_INJECTION_PATTERNS:                                                                                         
        match = re.search(pattern, message)                                                                                           
        if match:                                                                                                                     
            return SecurityCheckResult(                                                                                               
                is_safe=False,                                                                                                        
                threat_type="PROMPT_INJECTION",                                                                                       
                reason=f"Suspicious directive detected: '{match.group(0)}'",                                                          
            )                                                                                                                         
                                                                                                                                        
    return SecurityCheckResult(is_safe=True, threat_type=None, reason=None)                                                           
                                                                                                                                        
                                                                                                                                        
def redact_pii_for_logging(text: str) -> str:                                                                                         
    """                                                                                                                               
    Sanitizes text by masking employee IDs, emails, phone numbers, and compensation.                                                  
    Used before writing conversation traces to operational audit logs.                                                                
    """                                                                                                                               
    if not text:                                                                                                                      
        return ""                                                                                                                     
                                                                                                                                        
    sanitized = text                                                                                                                  
    for pattern, placeholder in PII_PATTERNS:                                                                                         
        sanitized = pattern.sub(placeholder, sanitized)                                                                               
                                                                                                                                        
    return sanitized