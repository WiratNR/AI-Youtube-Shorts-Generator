from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Make sure it is defined in the .env file.")

genai.configure(api_key=api_key)

class JSONResponse(BaseModel):
    """
    The response should strictly follow the following structure: -
     [
        {
        start: "Start time of the clip",
        content: "Highlight Text",
        end: "End Time for the highlighted clip"
        }
     ]
    """
    start: float = Field(description="Start time of the clip")
    content: str= Field(description="Highlight Text")
    end: float = Field(description="End time for the highlighted clip")

system = """
The input contains a timestamped transcription of a video.
Select a 2-minute segment from the transcription that contains something interesting, useful, surprising, controversial, or thought-provoking.
The selected text should contain only complete sentences.
Do not cut the sentences in the middle.
The selected text should form a complete thought.
Return a JSON object with the following structure:
## Output 
[{{
    start: "Start time of the segment in seconds (number)",
    content: "The transcribed text from the selected segment (clean text only, NO timestamps)",
    end: "End time of the segment in seconds (number)"
}}]

## Input
{Transcription}
"""

# User = """
# Example
# """




def GetHighlight(Transcription):
    import json
    
    try:
        # Configure Gemini model with JSON schema
        generation_config = {
            "temperature": 1.0,
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "object",
                "properties": {
                    "start": {
                        "type": "number",
                        "description": "Start time of the segment in seconds"
                    },
                    "content": {
                        "type": "string",
                        "description": "The transcribed text from the selected segment (clean text only, NO timestamps)"
                    },
                    "end": {
                        "type": "number",
                        "description": "End time of the segment in seconds"
                    }
                },
                "required": ["start", "content", "end"]
            }
        }
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=generation_config
        )
        
        # Format the prompt
        prompt = system.format(Transcription=Transcription)
        
        print("Calling Gemini for highlight selection...")
        response = model.generate_content(prompt)
        
        # Parse JSON response
        if not response or not response.text:
            print("ERROR: Gemini returned empty response")
            return None, None
        
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError as e:
            print(f"ERROR: Could not parse JSON response: {e}")
            print(f"Response text: {response.text}")
            return None, None
        
        # Validate response structure
        if not all(key in result for key in ['start', 'content', 'end']):
            print(f"ERROR: Invalid response structure: {result}")
            return None, None
        
        try:
            Start = int(result['start'])
            End = int(result['end'])
        except (ValueError, TypeError) as e:
            print(f"ERROR: Could not parse start/end times from response")
            print(f"  start: {result.get('start')}")
            print(f"  end: {result.get('end')}")
            print(f"  Error: {e}")
            return None, None
        
        # Validate times
        if Start < 0 or End < 0:
            print(f"ERROR: Negative time values - Start: {Start}s, End: {End}s")
            return None, None
        
        if End <= Start:
            print(f"ERROR: Invalid time range - Start: {Start}s, End: {End}s (end must be > start)")
            return None, None
        
        # Log the selected segment
        print(f"\n{'='*60}")
        print(f"SELECTED SEGMENT DETAILS:")
        print(f"Time: {Start}s - {End}s ({End-Start}s duration)")
        print(f"Content: {result['content']}")
        print(f"{'='*60}\n")
        
        if Start == End:
            Ask = input("Error - Get Highlights again (y/n) -> ").lower()
            if Ask == "y":
                Start, End = GetHighlight(Transcription)
            return Start, End
        return Start, End
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR IN GetHighlight FUNCTION:")
        print(f"{'='*60}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"\nTranscription length: {len(Transcription)} characters")
        print(f"First 200 chars: {Transcription[:200]}...")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    print(GetHighlight(User))
