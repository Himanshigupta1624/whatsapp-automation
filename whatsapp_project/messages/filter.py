# from transformers import pipeline
# import re
# import logging

# logger = logging.getLogger(__name__)

# FREELANCE_KEYWORDS = [
#     # Core development terms
#     'web developer', 'website developer', 'frontend developer', 'backend developer',
#     'full stack developer', 'web designer', 'ui developer', 'ux developer',
#     'app developer', 'mobile developer', 'flutter developer', 'react developer',
#     'wordpress developer', 'shopify developer', 'mern stack', 'mean stack',
    
#     # Design & Creative
#     'graphic designer', 'ui designer', 'ux designer', 'poster designer',
#     'logo designer', 'brand designer', 'figma designer', 'video editor',
#     'photographer', 'videographer', 'content creator', 'animator',
    
#     # Digital Marketing
#     'digital marketer', 'social media marketer', 'seo expert', 'content writer',
#     'copywriter', 'lead generator', 'ads manager', 'marketing specialist',
    
#     # Other Tech
#     'data scientist', 'ai developer', 'ml engineer', 'blockchain developer',
#     'c++ developer', 'python developer', 'java developer', 'software tester',
#     'qa engineer', 'devops engineer', 'database developer',
    
#     # Services & Projects
#     'website development', 'web development', 'app development', 'logo design',
#     'website design', 'mobile app', 'e-commerce', 'portfolio site',
#     'business website', 'landing page', 'automation', 'chatbot',
    
#     # Action words
#     'looking for', 'need', 'require', 'hiring', 'seeking', 'wanted',
#     'freelancer', 'freelance', 'developer', 'designer', 'project'
# ]

# # Load zero-shot classifier once (lazy loading)
# _classifier = None

# def get_zero_shot_classifier():
#     """Load the zero-shot classification model"""
#     global _classifier
#     if _classifier is None:
#         try:
#             _classifier = pipeline(
#                 "zero-shot-classification", 
#                 model="facebook/bart-large-mnli",
#                 device=-1  # Use CPU (change to 0 for GPU)
#             )
#             logger.info("Zero-shot classifier loaded successfully")
#         except Exception as e:
#             logger.error(f"Failed to load zero-shot classifier: {e}")
#             _classifier = False
    
#     return _classifier

# def preprocess_message(message: str) -> str:
#     """Clean the message for better classification"""
#     # Remove excessive emojis and special characters
#     message = re.sub(r'[^\w\s@+.-]', ' ', message)
#     # Remove multiple spaces
#     message = re.sub(r'\s+', ' ', message)
#     # Remove forwarded signatures
#     message = re.sub(r'forwarded as received\.?', '', message, flags=re.IGNORECASE)
#     return message.strip()

# def quick_keyword_check(message: str) -> bool:
#     """Quick check for freelance/development keywords"""
#     message_lower = message.lower()
#     return any(keyword in message_lower for keyword in FREELANCE_KEYWORDS)

# def zero_shot_intent_check(message: str) -> dict:
#     """Use zero-shot classification to determine message intent"""
#     try:
#         classifier = get_zero_shot_classifier()
        
#         if not classifier or classifier is False:
#             return {"intent": "unknown", "confidence": 0.0}
        
#         # Clean the message
#         clean_message = preprocess_message(message)
        
#         # Define labels for classification
#         labels = [
#             "Client looking to hire freelancer or developer",
#             "Freelancer offering services to clients", 
#             "General conversation or spam message"
#         ]
        
#         # Classify the message
#         result = classifier(clean_message, candidate_labels=labels)
        
#         top_label = result['labels'][0]
#         confidence = result['scores'][0]
        
#         logger.info(f"Zero-shot result: {top_label} ({confidence:.3f}) for: {message[:40]}...")
        
#         return {
#             "intent": top_label,
#             "confidence": confidence,
#             "all_scores": dict(zip(result['labels'], result['scores']))
#         }
        
#     except Exception as e:
#         logger.error(f"Zero-shot classification failed: {e}")
#         return {"intent": "unknown", "confidence": 0.0}

# def is_job_requirement(message: str) -> bool:
#     """
#     Check if message is a job requirement (someone looking to hire freelancers)
#     Returns True for freelance job postings, False for company jobs and freelancer offers
#     """
    
#     # Step 1: Quick keyword pre-filter
#     if not quick_keyword_check(message):
#         logger.info(f"No relevant keywords found: '{message[:40]}...'")
#         return False
    
#     # Step 1.5: Filter out company job postings (full-time positions)
#     message_lower = message.lower()
    
#     # Company job indicators (should be filtered out)
#     company_job_indicators = [
#         'we\'re hiring', 'we are hiring', 'hiring:', 'join our team', 'full time',
#         'salary:', 'experience:', 'location:', 'cv to', 'resume to', 'apply to',
#         'company', 'intern', 'internship', 'office', 'onsite', 'employee',
#         'benefits', 'package', 'permanent', 'years must', 'background and',
#         'only for freshers', 'freshers!', 'candidates with'
#     ]
    
#     # Check if it's a company job posting
#     company_score = sum(1 for indicator in company_job_indicators if indicator in message_lower)
#     if company_score >= 2:
#         logger.info(f"❌ COMPANY JOB POSTING detected: '{message[:40]}...'")
#         return False
    
#     # Freelance job indicators (what we want)
#     freelance_job_indicators = [
#         'looking for', 'need', 'require', 'seeking', 'wanted',
#         'any ', 'available', 'dm me', 'contact me', 'reach out',
#         'freelance', 'freelancer', 'project', 'gig'
#     ]
    
#     # Freelancer offer indicators (should be filtered out)
#     freelancer_indicators = [
#         'i am', 'i\'m', 'offering', 'available for', 'portfolio', 
#         'my services', 'hire me', 'contact us', 'we are', 'we provide',
#         'get your', 'just ₹', 'starting from'
#     ]
    
#     freelance_job_score = sum(1 for indicator in freelance_job_indicators if indicator in message_lower)
#     freelancer_score = sum(1 for indicator in freelancer_indicators if indicator in message_lower)
    
#     # If clear freelancer offer pattern, filter out
#     if freelancer_score >= 2:
#         logger.info(f"❌ FREELANCER OFFER detected: '{message[:40]}...'")
#         return False
    
#     # If clear freelance job requirement pattern, accept
#     if freelance_job_score >= 2 and freelancer_score == 0:
#         logger.info(f"✅ FREELANCE JOB REQUIREMENT detected: '{message[:40]}...'")
#         return True
    
#     # Step 2: Zero-shot classification for borderline cases
#     classification_result = zero_shot_intent_check(message)
    
#     intent = classification_result.get("intent", "")
#     confidence = classification_result.get("confidence", 0.0)
    
#     # Check if it's a client looking to hire with sufficient confidence
#     is_job_req = (
#         "Client looking to hire" in intent and 
#         confidence > 0.6  # Higher confidence threshold to reduce false positives
#     )
    
#     if is_job_req:
#         logger.info(f"✅ JOB REQUIREMENT detected: {confidence:.3f} - '{message[:40]}...'")
#     else:
#         if "Freelancer offering" in intent:
#             logger.info(f"❌ FREELANCER OFFER detected: {confidence:.3f} - '{message[:40]}...'")
#         else:
#             logger.info(f"❌ GENERAL MESSAGE: {confidence:.3f} - '{message[:40]}...'")
    
#     return is_job_req

# # Keep the old function name for backward compatibility
# def is_relevant_message(msg: str) -> bool:
#     """Check if message is a job requirement (backward compatibility)"""
#     return is_job_requirement(msg)

# # Test function to validate the classifier
# def test_classifier():
#     """Test the classifier with sample messages"""
#     test_messages = [
#         # Should be TRUE (Job Requirements)
#         "Hey everyone, I am looking for a n8n developer",
#         "Looking for Poster Designers! Need creative designers",
#         "Hello, I'm looking for freelance videographers",
#         "Need digital marketer who has experience in lead generation",
#         "Any Figma designers freelancers kindly DM me",
#         "Hi\n\nAny freelance Shopify Website developer available?\n\nDM me, I will share the contact person",
        
#         # Should be FALSE (Freelancer Offers)
#         "I'm a passionate freelance developer actively looking for projects",
#         "Hello Everyone! I'm offering freelance services in Digital Marketing",
#         "Are you looking for performance-driven digital marketers?",
#         "I'm Barath Chander E, a freelance developer looking for opportunities",
#         "Get Your Own Business Portfolio Website for Just ₹1999!",
        
#         # Should be FALSE (Company Jobs)
#         "We're Hiring: Machine Learning Intern\n\nWe're looking for a passionate Machine Learning intern to join our team!",
#         "🚀 We're Hiring – Digital Marketing Manager at Fitoverse 🌐\nLooking for a smart, hands-on marketer who can run Google Ads, Meta Ads, SEO, and Email Marketing campaigns. Salary: ₹25,000 – ₹30,000/month Experience: 1-2 years Must!",
#         "Dears,\nWe are hiring freshers!\nLooking for candidates with a CSC, ECE, or EEE background and good communication skills to handle client coordination and Avaya support.\nOnly for freshers.\nIf you're interested, please DM."
#     ]
    
#     print("🧪 Testing Zero-Shot Classifier:")
#     print("=" * 50)
    
#     for message in test_messages:
#         result = is_job_requirement(message)
#         status = "✅ PASS" if result else "❌ FILTER"
#         print(f"{status}: {message[:60]}...")
    
#     print("=" * 50)

# if __name__ == "__main__":
#     test_classifier()

import google.generativeai as genai
import re
import logging
import os

logger = logging.getLogger(__name__)

FREELANCE_KEYWORDS = [
    # Core development terms
    'web developer', 'website developer', 'frontend developer', 'backend developer',
    'full stack developer', 'web designer', 'ui developer', 'ux developer',
    'app developer', 'mobile developer', 'flutter developer', 'react developer',
    'wordpress developer', 'shopify developer', 'mern stack', 'mean stack',
    
    # Design & Creative
    'graphic designer', 'ui designer', 'ux designer', 'poster designer',
    'logo designer', 'brand designer', 'figma designer', 'video editor',
    'photographer', 'videographer', 'content creator', 'animator',
    
    # Digital Marketing
    'digital marketer', 'social media marketer', 'seo expert', 'content writer',
    'copywriter', 'lead generator', 'ads manager', 'marketing specialist',
    
    # Other Tech
    'data scientist', 'ai developer', 'ml engineer', 'blockchain developer',
    'c++ developer', 'python developer', 'java developer', 'software tester',
    'qa engineer', 'devops engineer', 'database developer',
    
    # Services & Projects
    'website development', 'web development', 'app development', 'logo design',
    'website design', 'mobile app', 'e-commerce', 'portfolio site',
    'business website', 'landing page', 'automation', 'chatbot',
    
    # Action words
    'looking for', 'need', 'require', 'hiring', 'seeking', 'wanted',
    'freelancer', 'freelance', 'developer', 'designer', 'project'
]

# Configure Gemini API
def configure_gemini():
    """Configure Gemini API with API key"""
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            return False
        
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}")
        return False

# Initialize Gemini model
_gemini_model = None

def get_gemini_model():
    """Get Gemini model instance"""
    global _gemini_model
    if _gemini_model is None:
        try:
            if configure_gemini():
                _gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Gemini model initialized successfully")
            else:
                _gemini_model = False
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            _gemini_model = False
    
    return _gemini_model

def preprocess_message(message: str) -> str:
    """Clean the message for better classification"""
    # Remove excessive emojis and special characters
    message = re.sub(r'[^\w\s@+.-]', ' ', message)
    # Remove multiple spaces
    message = re.sub(r'\s+', ' ', message)
    # Remove forwarded signatures
    message = re.sub(r'forwarded as received\.?', '', message, flags=re.IGNORECASE)
    return message.strip()

def quick_keyword_check(message: str) -> bool:
    """Quick check for freelance/development keywords"""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in FREELANCE_KEYWORDS)

def gemini_intent_check(message: str) -> dict:
    """Use Gemini API to determine message intent"""
    try:
        model = get_gemini_model()
        
        if not model or model is False:
            return {"intent": "unknown", "confidence": 0.0}
        
        # Clean the message
        clean_message = preprocess_message(message)
        
        # Create prompt for Gemini
        prompt = f"""
Analyze this message and classify it into one of these categories:

1. "Client looking to hire freelancer" - Someone needs/wants to hire a freelancer or developer
2. "Freelancer offering services" - Someone is offering their freelance services
3. "Company job posting" - Company hiring for full-time positions
4. "General message" - Other types of messages

Message: "{clean_message}"

Respond with only:
- Category: [exact category name]
- Confidence: [0.0 to 1.0]
- Explanation: [brief reason]

Format:
Category: [category]
Confidence: [number]
Explanation: [reason]
"""
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse response
        category = "unknown"
        confidence = 0.0
        
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('Category:'):
                category = line.replace('Category:', '').strip()
            elif line.startswith('Confidence:'):
                try:
                    confidence = float(line.replace('Confidence:', '').strip())
                except:
                    confidence = 0.0
        
        logger.info(f"Gemini result: {category} ({confidence:.3f}) for: {message[:40]}...")
        
        return {
            "intent": category,
            "confidence": confidence,
            "full_response": response_text
        }
        
    except Exception as e:
        logger.error(f"Gemini classification failed: {e}")
        return {"intent": "unknown", "confidence": 0.0}

def is_job_requirement(message: str) -> bool:
    """
    Check if message is a job requirement (someone looking to hire freelancers)
    Returns True for freelance job postings, False for company jobs and freelancer offers
    """
    
    # Step 1: Quick keyword pre-filter
    if not quick_keyword_check(message):
        logger.info(f"No relevant keywords found: '{message[:40]}...'")
        return False
    
    # Step 1.5: Filter out company job postings (full-time positions)
    message_lower = message.lower()
    
    # Company job indicators (should be filtered out)
    company_job_indicators = [
        'we\'re hiring', 'we are hiring', 'hiring:', 'join our team', 'full time',
        'salary:', 'experience:', 'location:', 'cv to', 'resume to', 'apply to',
        'company', 'intern', 'internship', 'office', 'onsite', 'employee',
        'benefits', 'package', 'permanent', 'years must', 'background and',
        'only for freshers', 'freshers!', 'candidates with'
    ]
    
    # Check if it's a company job posting
    company_score = sum(1 for indicator in company_job_indicators if indicator in message_lower)
    if company_score >= 2:
        logger.info(f"❌ COMPANY JOB POSTING detected: '{message[:40]}...'")
        return False
    
    # Freelance job indicators (what we want)
    freelance_job_indicators = [
        'looking for', 'need', 'require', 'seeking', 'wanted',
        'any ', 'available', 'dm me', 'contact me', 'reach out',
        'freelance', 'freelancer', 'project', 'gig'
    ]
    
    # Freelancer offer indicators (should be filtered out)
    freelancer_indicators = [
        'i am', 'i\'m', 'offering', 'available for', 'portfolio', 
        'my services', 'hire me', 'contact us', 'we are', 'we provide',
        'get your', 'just ₹', 'starting from'
    ]
    
    freelance_job_score = sum(1 for indicator in freelance_job_indicators if indicator in message_lower)
    freelancer_score = sum(1 for indicator in freelancer_indicators if indicator in message_lower)
    
    # If clear freelancer offer pattern, filter out
    if freelancer_score >= 2:
        logger.info(f"❌ FREELANCER OFFER detected: '{message[:40]}...'")
        return False
    
    # If clear freelance job requirement pattern, accept
    if freelance_job_score >= 2 and freelancer_score == 0:
        logger.info(f"✅ FREELANCE JOB REQUIREMENT detected: '{message[:40]}...'")
        return True
    
    # Step 2: Use Gemini API for borderline cases
    classification_result = gemini_intent_check(message)
    
    intent = classification_result.get("intent", "")
    confidence = classification_result.get("confidence", 0.0)
    
    # Check if it's a client looking to hire with sufficient confidence
    is_job_req = (
        "Client looking to hire" in intent and 
        confidence > 0.7  # Higher confidence threshold
    )
    
    if is_job_req:
        logger.info(f"✅ JOB REQUIREMENT detected: {confidence:.3f} - '{message[:40]}...'")
    else:
        if "Freelancer offering" in intent:
            logger.info(f"❌ FREELANCER OFFER detected: {confidence:.3f} - '{message[:40]}...'")
        elif "Company job posting" in intent:
            logger.info(f"❌ COMPANY JOB detected: {confidence:.3f} - '{message[:40]}...'")
        else:
            logger.info(f"❌ GENERAL MESSAGE: {confidence:.3f} - '{message[:40]}...'")
    
    return is_job_req

# Keep the old function name for backward compatibility
def is_relevant_message(msg: str) -> bool:
    """Check if message is a job requirement (backward compatibility)"""
    return is_job_requirement(msg)

# Test function to validate the classifier
def test_classifier():
    """Test the classifier with sample messages"""
    test_messages = [
        # Should be TRUE (Job Requirements)
        "Hey everyone, I am looking for a n8n developer",
        "Looking for Poster Designers! Need creative designers",
        "Hello, I'm looking for freelance videographers",
        "Need digital marketer who has experience in lead generation",
        "Any Figma designers freelancers kindly DM me",
        "Hi\n\nAny freelance Shopify Website developer available?\n\nDM me, I will share the contact person",
        
        # Should be FALSE (Freelancer Offers)
        "I'm a passionate freelance developer actively looking for projects",
        "Hello Everyone! I'm offering freelance services in Digital Marketing",
        "Are you looking for performance-driven digital marketers?",
        "I'm Barath Chander E, a freelance developer looking for opportunities",
        "Get Your Own Business Portfolio Website for Just ₹1999!",
        
        # Should be FALSE (Company Jobs)
        "We're Hiring: Machine Learning Intern\n\nWe're looking for a passionate Machine Learning intern to join our team!",
        "🚀 We're Hiring – Digital Marketing Manager at Fitoverse 🌐\nLooking for a smart, hands-on marketer who can run Google Ads, Meta Ads, SEO, and Email Marketing campaigns. Salary: ₹25,000 – ₹30,000/month Experience: 1-2 years Must!",
        "Dears,\nWe are hiring freshers!\nLooking for candidates with a CSC, ECE, or EEE background and good communication skills to handle client coordination and Avaya support.\nOnly for freshers.\nIf you're interested, please DM."
    ]
    
    print("🧪 Testing Gemini API Classifier:")
    print("=" * 50)
    
    for message in test_messages:
        result = is_job_requirement(message)
        status = "✅ PASS" if result else "❌ FILTER"
        print(f"{status}: {message[:60]}...")
    
    print("=" * 50)

if __name__ == "__main__":
    test_classifier()
