import re
import logging
import os
# Try to import Google Generative AI, but handle gracefully if not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

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

# Configure Gemini API with graceful fallback
def configure_gemini():
    """Configure Gemini API with API key - graceful fallback"""
    try:
        import google.generativeai as genai_import
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY not found - pattern-only mode")
            return False

        genai_import.configure(api_key=api_key)
        return True
    except ImportError:
        logger.warning("Google Generative AI not available - pattern-only mode")
        return False
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}")
        return False

# Initialize Gemini model with memory conservation
_gemini_model = None

def get_gemini_model():
    """Get Gemini model instance - memory conservative"""
    global _gemini_model
    if _gemini_model is None:
        try:
            if configure_gemini():
                import google.generativeai as genai_import
                _gemini_model = genai_import.GenerativeModel('gemini-1.5-flash')
                logger.info("Gemini model available for complex cases")

            else:
                _gemini_model = False
                logger.info("Using pattern-only classification (memory efficient)")
        except Exception as e:
            logger.error(f"Gemini initialization failed: {e}")
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
    """Quick check for freelance/development keywords - memory efficient"""
    message_lower = message.lower()

    # Comprehensive disqualifiers that are never freelance jobs
    hard_disqualifiers = [
        'salary', 'in hand', 'hours duty', 'bus canteen', 'mnc company',
        'urgent requirement', 'send resume', 'sir', 'education :', 'male & female',
        'qualification :', 'immediate hiring', 'steel deal', 'get access',
        # Service offering patterns (VedaTechX style)
        'what we offer', 'we offer', 'our services', 'we provide', 'we deliver',
        'fiverr', 'gig', 'dm me to get started', 'contact us for', 'visit our',
        'check out our', 'hire us', 'we specialize', 'we are expert',
        'explore the gig', 'madeonfiverr', 'our expertise', 'we help you',
        'you\'re in the right place', 'we merge', 'transform your', 
        'tailored to your', 'smart erp solutions', 'ancient wisdom',
        'exceptional solutions', 'empowering your business'
    ]

    if any(disq in message_lower for disq in hard_disqualifiers):
        return False

    # Expanded hiring intent keywords (more inclusive)
    hiring_keywords = [
        'looking for', 'need', 'require', 'seeking', 'wanted', 'hire', 'hiring',
        'any ', 'available', 'dm me', 'contact me', 'reach out', 'freelance', 
        'freelancer', 'project', 'build', 'create', 'develop', 'need to',
        'need to build', 'need to create', 'need to develop'
    ]

    # Expanded skill keywords (include all the original comprehensive list)
    skill_keywords = [
        'developer', 'designer', 'freelancer', 'video editor', 'marketer',
        'appointment setter', 'content writer', 'programmer', 'coder',
        # Add back the comprehensive list
        'web developer', 'website developer', 'frontend developer', 'backend developer',
        'full stack developer', 'web designer', 'ui developer', 'ux developer',
        'app developer', 'mobile developer', 'flutter developer', 'react developer',
        'wordpress developer', 'shopify developer', 'mern stack', 'mean stack',
        'graphic designer', 'ui designer', 'ux designer', 'poster designer',
        'logo designer', 'brand designer', 'figma designer', 'video editor',
        'photographer', 'videographer', 'content creator', 'animator',
        'digital marketer', 'social media marketer', 'seo expert', 'content writer',
        'copywriter', 'lead generator', 'ads manager', 'marketing specialist',
        'data scientist', 'ai developer', 'ml engineer', 'blockchain developer',
        'c++ developer', 'python developer', 'java developer', 'software tester',
        'qa engineer', 'devops engineer', 'database developer',
        'website development', 'web development', 'app development', 'logo design',
        'website design', 'mobile app', 'e-commerce', 'portfolio site',
        'business website', 'landing page', 'automation', 'chatbot', 'site', 'website',
        # Special patterns for Shopify
        'shopify', 'shopify website', 'shopify site', 'shopify store'
    ]

    has_hiring_intent = any(keyword in message_lower for keyword in hiring_keywords)
    has_skill_requirement = any(keyword in message_lower for keyword in skill_keywords)

    return has_hiring_intent and has_skill_requirement

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
Analyze this message very carefully and classify it into one of these categories:

1. "Client looking to hire freelancer" - Someone genuinely needs to hire a freelancer/developer for their project
2. "Freelancer offering services" - Someone is advertising their services, even if they use phrases like "Looking for clients"
3. "Company job posting" - Company hiring for full-time positions
4. "General message" - Other types of messages

IMPORTANT: Pay special attention to these red flags that indicate SERVICE OFFERINGS (not job requirements):
- Mentions of "What we offer", "we provide", "our services"
- Links to Fiverr, gigs, or portfolios
- "DM me to get started", "contact us", "hire us"
- Company names promoting their services
- Lists of services they provide
- Marketing language like "transform your business", "tailored solutions"

Message: "{clean_message}"

Respond with only:
- Category: [exact category name]
- Confidence: [0.0 to 1.0]
- Explanation: [brief reason focusing on why it's a service offer vs genuine job posting]

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
    Memory-efficient job requirement checker
    Uses pattern matching first, Gemini only as fallback for edge cases
    """

    # Pre-filter: Aggressive pattern detection (no AI needed)
    message_lower = message.lower()

    # Step 1: Immediate rejection patterns (regex-based, memory efficient)
    immediate_reject_patterns = [
        # Salary patterns
        r'\d+\s*to\s*\d+.*(?:in hand|salary)',
        r'salary.*₹.*\d+',
        r'\d+.*in hand',
        # Company job patterns
        r'education.*:.*\d+th',
        r'male.*&.*female',
        r'bus.*canteen',
        r'urgent.*requirement.*male',
        r'mnc.*company',
        r'send.*resume.*urgently',
        # Service offering patterns
        r'what.*we.*offer',
        r'fiverr\.com',
        r'explore.*the.*gig',
        r'dm.*me.*to.*get.*started',
        r'you\'re.*in.*the.*right.*place',
        r'we.*merge.*ancient.*wisdom',
        r'transform.*your.*operations',
        r'empowering.*your.*business'
    ]

    for pattern in immediate_reject_patterns:
        if re.search(pattern, message_lower):
            logger.info(f"❌ REGEX PATTERN REJECT: '{message[:40]}...'")
            return False

    # Step 2: Deceptive service offerings check
    deceptive_patterns = [
        'what we offer', 'we offer', 'fiverr', 'gig', 'dm me to get started', 
        'our services', 'we deliver', 'we provide', 'we specialize', 'we merge',
        'transform your', 'you\'re in the right place', 'tailored to your',
        'exceptional solutions', 'empowering your business'
    ]

    if 'looking for' in message_lower and any(pattern in message_lower for pattern in deceptive_patterns):
        logger.info(f"❌ DECEPTIVE SERVICE OFFERING: '{message[:40]}...'")
        return False

    # Step 3: Basic keyword filtering (memory efficient)
    if not quick_keyword_check(message):
        logger.info(f"❌ KEYWORD CHECK FAILED: '{message[:40]}...'")
        return False

    # Step 4: Advanced pattern matching (before using AI)
    # Company job indicators
    company_indicators = [
        'we\'re hiring', 'we are hiring', 'hiring:', 'join our team', 'full time',
        'company', 'intern', 'internship', 'office', 'onsite', 'employee',
        'only for freshers', 'freshers!', 'candidates with', 'pf esic',
        'interview depend', 'department', 'on roll job', 'production supervisor'
    ]

    company_score = sum(1 for indicator in company_indicators if indicator in message_lower)
    if company_score >= 1:
        logger.info(f"❌ COMPANY JOB DETECTED: '{message[:40]}...'")
        return False

    # Freelancer offer indicators
    freelancer_indicators = [
        'i am', 'i\'m', 'offering', 'available for', 'portfolio', 
        'my services', 'hire me', 'contact us', 'we are', 'we provide',
        'get your', 'just ₹', 'starting from', 'just edited', 'loved working',
        'kindly share portfolio', 'drop a', 'if you\'re', 'views are awesome'
    ]

    freelancer_score = sum(1 for indicator in freelancer_indicators if indicator in message_lower)
    if freelancer_score >= 1:
        logger.info(f"❌ FREELANCER OFFER DETECTED: '{message[:40]}...'")
        return False

    # Step 5: Positive indicators for genuine job requirements
    job_requirement_indicators = [
        'looking for', 'need', 'require', 'seeking', 'wanted',
        'any ', 'available', 'dm me', 'contact me', 'reach out',
        'freelance', 'freelancer', 'project'
    ]

    job_req_score = sum(1 for indicator in job_requirement_indicators if indicator in message_lower)

    # If strong positive indicators and no negative ones, accept without AI
    if job_req_score >= 1 and freelancer_score == 0 and company_score == 0:
        logger.info(f"✅ PATTERN MATCH: JOB REQUIREMENT: '{message[:40]}...'")
        return True

    # Step 6: Only use Gemini for borderline cases (memory conservation)
    try:
        classification_result = gemini_intent_check(message)
        intent = classification_result.get("intent", "")
        confidence = classification_result.get("confidence", 0.0)

        is_job_req = (
            "Client looking to hire" in intent and 
            confidence > 0.7
        )

        if is_job_req:
            logger.info(f"✅ GEMINI FALLBACK: JOB REQUIREMENT: {confidence:.3f} - '{message[:40]}...'")
            return True
        else:
            logger.info(f"❌ GEMINI FALLBACK: NOT JOB REQ: {intent} ({confidence:.3f}) - '{message[:40]}...'")
            return False

    except Exception as e:
        # If Gemini fails (memory issues), fall back to pattern matching
        logger.warning(f"Gemini failed, using pattern fallback: {e}")
        return job_req_score >= 1  # More lenient fallback

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
        "Hi looking for a video editor to edit AI videos",
        "Hey guys, I am looking for experienced appointment setters for my agency",
        "Any freelance Shopify Website developer available? DM me",
        "Hi\n\nAny freelance Shopify Website developer available?\n\nDM me, I will share the contact person\n#Hiring\n\nNeed to build a Shopify site similar to this.",

        # Should be FALSE (Recent Company Job Postings)
        "Urgent requirement • MNC COMPANY • Male & female Education 10th 12th ITI salary 15000 TO 17,000",
        "•Urgently Requirement• •Tomorrow• company Name:-( MNC ) •Only/FEMALE• •Age limit•:- 18-30 years",
        "Please Help To Forward In Job Groups Urgently Required Post : 7 PSR Project : - Biotique Company",
        "FlutterFlow Now Available in Steel Deal! Get access to FlutterFlow – the powerful no-code app builder",
        "Urgent requirement Male & female Education : 10th 12th ITI Salary : 17000 in hand 8 hours duty",
        "MNC COMPANY Male & female Education : BA B COM BSC Salary : 15500 in hand",
        "Urgent requirement ON ROLL JOB Production supervisor 04 Store supervisor 05",
        "Immediate Hiring - Female Candidate With Mechanical Diploma Requirements",

        # Should be FALSE (Freelancer Offers)
        "Just Edited this New Videos for my Client. DM me for Video Projects",
        "I'm a passionate freelance developer actively looking for projects",
        "Get Your Own Business Portfolio Website for Just ₹1999!",
        "Kindly share portfolio with relevant projects",
        "Drop a 'Interested' if you're the right fit or DM me directly",
        "VedaTechX Looking for an expert Odoo developer? What We Offer: Custom Odoo Modules DM me to get started!",

        # Should be FALSE (Model/Other Requirements)
        "Hair Show Model Requirement – Schwarzkopf Professional Academy Location: Saket",
        "We need 5 Female Models for a 2-Day Hair Show Send profiles ASAP!"
    ]

    print("🧪 Testing Classifier with Shopify Messages:")
    print("=" * 60)

    for i, message in enumerate(test_messages, 1):
        result = is_job_requirement(message)
        status = "✅ PASS" if result else "❌ FILTER"
        print(f"{i:2d}. {status}: {message[:50]}...")

    print("=" * 60)

if __name__ == "__main__":
    test_classifier()