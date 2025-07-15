from transformers import pipeline
import re
import logging

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

# Load zero-shot classifier once (lazy loading)
_classifier = None

def get_zero_shot_classifier():
    """Load the zero-shot classification model"""
    global _classifier
    if _classifier is None:
        try:
            _classifier = pipeline(
                "zero-shot-classification", 
                model="facebook/bart-large-mnli",
                device=-1  # Use CPU (change to 0 for GPU)
            )
            logger.info("Zero-shot classifier loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load zero-shot classifier: {e}")
            _classifier = False
    
    return _classifier

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

def zero_shot_intent_check(message: str) -> dict:
    """Use zero-shot classification to determine message intent"""
    try:
        classifier = get_zero_shot_classifier()
        
        if not classifier or classifier is False:
            return {"intent": "unknown", "confidence": 0.0}
        
        # Clean the message
        clean_message = preprocess_message(message)
        
        # Define labels for classification
        labels = [
            "Client looking to hire freelancer or developer",
            "Freelancer offering services to clients", 
            "General conversation or spam message"
        ]
        
        # Classify the message
        result = classifier(clean_message, candidate_labels=labels)
        
        top_label = result['labels'][0]
        confidence = result['scores'][0]
        
        logger.info(f"Zero-shot result: {top_label} ({confidence:.3f}) for: {message[:40]}...")
        
        return {
            "intent": top_label,
            "confidence": confidence,
            "all_scores": dict(zip(result['labels'], result['scores']))
        }
        
    except Exception as e:
        logger.error(f"Zero-shot classification failed: {e}")
        return {"intent": "unknown", "confidence": 0.0}

def is_job_requirement(message: str) -> bool:
    """
    Check if message is a job requirement (someone looking to hire)
    Returns True for job postings, False for freelancer offers
    """
    
    # Step 1: Quick keyword pre-filter
    if not quick_keyword_check(message):
        logger.info(f"No relevant keywords found: '{message[:40]}...'")
        return False
    
    # Step 1.5: Strong keyword indicators for job requirements
    message_lower = message.lower()
    job_indicators = [
        'looking for', 'need', 'require', 'hiring', 'seeking', 'wanted',
        'any ', 'available', 'dm me', 'contact me', 'reach out'
    ]
    freelancer_indicators = [
        'i am', 'i\'m', 'offering', 'available for', 'portfolio', 
        'my services', 'hire me', 'contact us', 'we are', 'we provide'
    ]
    
    job_score = sum(1 for indicator in job_indicators if indicator in message_lower)
    freelancer_score = sum(1 for indicator in freelancer_indicators if indicator in message_lower)
    
    # If clear keyword pattern, return immediately
    if job_score >= 2 and freelancer_score == 0:
        logger.info(f"✅ STRONG JOB REQUIREMENT keywords detected: '{message[:40]}...'")
        return True
    elif freelancer_score >= 2 and job_score == 0:
        logger.info(f"❌ STRONG FREELANCER OFFER keywords detected: '{message[:40]}...'")
        return False
    
    # Step 2: Zero-shot classification
    classification_result = zero_shot_intent_check(message)
    
    intent = classification_result.get("intent", "")
    confidence = classification_result.get("confidence", 0.0)
    
    # Check if it's a job requirement with sufficient confidence
    is_job_req = (
        "Client looking to hire" in intent and 
        confidence > 0.4  # Lower confidence threshold for better detection
    )
    
    if is_job_req:
        logger.info(f"✅ JOB REQUIREMENT detected: {confidence:.3f} - '{message[:40]}...'")
    else:
        if "Freelancer offering" in intent:
            logger.info(f"❌ FREELANCER OFFER detected: {confidence:.3f} - '{message[:40]}...'")
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
        
        # Should be FALSE (Freelancer Offers)
        "I'm a passionate freelance developer actively looking for projects",
        "Hello Everyone! I'm offering freelance services in Digital Marketing",
        "Are you looking for performance-driven digital marketers?",
        "I'm Barath Chander E, a freelance developer looking for opportunities",
        "Get Your Own Business Portfolio Website for Just ₹1999!"
    ]
    
    print("🧪 Testing Zero-Shot Classifier:")
    print("=" * 50)
    
    for message in test_messages:
        result = is_job_requirement(message)
        status = "✅ PASS" if result else "❌ FILTER"
        print(f"{status}: {message[:60]}...")
    
    print("=" * 50)

if __name__ == "__main__":
    test_classifier()
