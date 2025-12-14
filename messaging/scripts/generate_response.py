"""
AI Response Generator for Turo Messages
Uses Claude to generate contextual responses to guest messages.
"""

import os
from anthropic import Anthropic

# Configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'config')

def load_context_file(filename: str) -> str:
    """Load a context file from the config directory."""
    filepath = os.path.join(CONFIG_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()
    return ""

def generate_response(guest_name: str, message: str, trip_dates: str = None) -> dict:
    """
    Generate an AI response to a guest message.
    
    Returns dict with:
        - response: The generated response text
        - confidence: How confident the AI is (0-1)
        - notes: Any notes about the response
    """
    # Load context documents
    vehicle_info = load_context_file('vehicle_info.md')
    policies = load_context_file('policies.md')
    faq = load_context_file('faq.md')
    tone_guide = load_context_file('tone_guide.md')
    
    # Build the prompt
    system_prompt = f"""You are Daniel, a friendly Turo host for a 2024 Tesla Cybertruck Cyberbeast named "Aether" in Raleigh, NC. You're enthusiastic about the truck and want guests to have an amazing experience.

COMMUNICATION STYLE:
{tone_guide}

VEHICLE INFORMATION:
{vehicle_info}

RENTAL POLICIES:
{policies}

COMMON QUESTIONS & ANSWERS:
{faq}

IMPORTANT GUIDELINES:
- Write in first person as the host (Daniel)
- Be friendly, helpful, and enthusiastic
- Answer questions directly and completely
- Keep responses under 200 words unless more detail is truly needed
- Include relevant video links when they would help
- If you're unsure about something, say so and offer to find out
- Don't make up information not in the context above
"""

    trip_context = f"\nTRIP DATES: {trip_dates}" if trip_dates else ""
    
    user_prompt = f"""A guest named {guest_name} sent this message:{trip_context}

"{message}"

Write a helpful, friendly response. Be concise but thorough."""

    # Call Claude API
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        # Estimate confidence based on response characteristics
        confidence = 0.9  # High confidence for most responses
        notes = "Generated successfully"
        
        # Lower confidence for certain cases
        if "I'm not sure" in response_text or "I don't know" in response_text:
            confidence = 0.6
            notes = "Response expresses uncertainty"
        elif len(response_text) < 50:
            confidence = 0.7
            notes = "Short response - may need review"
        elif "?" in message.lower() and "?" not in response_text:
            confidence = 0.8
            notes = "Question asked but answer may be incomplete"
        
        return {
            "response": response_text,
            "confidence": confidence,
            "notes": notes
        }
        
    except Exception as e:
        return {
            "response": None,
            "confidence": 0,
            "notes": f"Error generating response: {str(e)}"
        }

def main():
    """Test the response generator."""
    test_message = "Hi! I'm excited about renting the Cybertruck. Does it come with FSD enabled? Also, what's the best way to charge it?"
    
    print("Testing response generation...")
    print(f"Guest message: {test_message}\n")
    
    result = generate_response(
        guest_name="John D.",
        message=test_message,
        trip_dates="Dec 20-23, 2025"
    )
    
    print(f"Generated response (confidence: {result['confidence']:.0%}):")
    print(f"{result['response']}")
    print(f"\nNotes: {result['notes']}")

if __name__ == "__main__":
    main()
