from sentence_transformers import SentenceTransformer
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Web development specific keywords
WEB_DEV_KEYWORDS = [
    # Core web development terms
    'web developer', 'website developer', 'frontend developer', 'backend developer',
    'full stack developer', 'web designer', 'ui developer', 'ux developer',
    
    # Services needed
    'need website', 'website development', 'web development', 'create website',
    'build website', 'design website', 'website redesign', 'responsive design',
    
    # Technologies
    'html', 'css', 'javascript', 'react', 'angular', 'vue', 'node.js',
    'wordpress', 'shopify', 'woocommerce', 'bootstrap', 'tailwind',
    
    # Project types
    'landing page', 'portfolio site', 'business website', 'e-commerce site',
    'online store', 'web application', 'web app', 'website maintenance',
    
    # General indicators
    'freelancer', 'developer', 'programmer', 'coder',
    'need', 'require', 'looking for', 'hire', 'project'
]

# Load AI model once (lazy loading)
_model = None
_web_dev_embeddings = None

def get_ai_model():
    global _model, _web_dev_embeddings
    if _model is None:
        try:
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Web development specific phrases
            web_dev_phrases = [
                "I need a web developer",
                "Looking for website developer", 
                "Need someone to build a website",
                "Require frontend developer",
                "Want to create a business website",
                "Need e-commerce website development",
                "Looking for React developer",
                "Need website redesign",
                "Want responsive website design",
                "Seeking web application developer"
            ]
            
            _web_dev_embeddings = _model.encode(web_dev_phrases)
            logger.info("Web dev AI model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")
            _model = False
    
    return _model, _web_dev_embeddings

def quick_web_dev_check(message: str) -> bool:
    """Quick check for web development keywords"""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in WEB_DEV_KEYWORDS)

def ai_web_dev_check(message: str) -> bool:
    """AI check specifically for web development context"""
    try:
        model, web_dev_embeddings = get_ai_model()
        
        if not model or model is False:
            return False
        
        message_embedding = model.encode([message])
        similarities = np.dot(message_embedding, web_dev_embeddings.T)[0]
        max_similarity = np.max(similarities)
        
        # Threshold for web dev relevance
        threshold = 0.4  # Adjust based on your needs
        
        logger.info(f"Web dev AI score: {max_similarity:.3f} for: {message[:40]}...")
        return max_similarity > threshold
        
    except Exception as e:
        logger.error(f"AI web dev check failed: {e}")
        return False

def is_relevant_message(msg: str) -> bool:
    """Check if message is looking for web development services"""
    
    # Step 1: Quick keyword check
    has_web_keywords = quick_web_dev_check(msg)
    
    # Step 2: AI confirmation if keywords found
    if has_web_keywords:
        ai_confirms = ai_web_dev_check(msg)
        logger.info(f"Keywords: ✓, AI confirms: {ai_confirms} - Result: {ai_confirms}")
        return ai_confirms
    
    # Step 3: AI-only check for edge cases (higher threshold)
    ai_result = ai_web_dev_check(msg)
    if ai_result:
        # Double-check with stricter threshold for AI-only matches
        try:
            model, web_dev_embeddings = get_ai_model()
            if model and model is not False:
                message_embedding = model.encode([msg])
                similarities = np.dot(message_embedding, web_dev_embeddings.T)[0]
                max_similarity = np.max(similarities)
                
                strict_threshold = 0.6  # Higher for AI-only
                result = max_similarity > strict_threshold
                logger.info(f"AI-only check: {max_similarity:.3f} > {strict_threshold} = {result}")
                return result
        except:
            pass
    
    logger.info(f"Message rejected: '{msg[:40]}...'")
    return False
