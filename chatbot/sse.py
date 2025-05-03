# New file in chatbot app
import json
from django.http import StreamingHttpResponse
from .llm_integration import stream_response

def chat_stream(request):
    def event_generator():
        user_query = request.GET.get('q')
        if not user_query:
            yield 'data: {"type": "error", "message": "Empty query"}\n\n'
            return
            
        try:
            for event in stream_response(user_query):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f'data: {{"type": "error", "message": "{str(e)}"}}\n\n'
    
    
        response = StreamingHttpResponse(
        event_generator(),
        content_type='text/event-stream',
    )
        response['Cache-Control'] = 'no-cache'
        response['Access-Control-Allow-Origin'] = 'http://localhost:3000'  # Explicitly allow frontend
        response['Connection'] = 'keep-alive'
        return response