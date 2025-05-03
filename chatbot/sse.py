import json
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_GET
from .models import Conversation
from .llm_integration import stream_response

@require_GET
def chat_stream(request):
    def event_generator():
        user_query = request.GET.get('q')
        if not user_query:
            yield 'data: {"type": "error", "message": "Empty query"}\n\n'
            return

        try:
            # Create conversation
            conversation = Conversation.objects.create(
                title=f"Chat: {user_query[:30]}...",
                user=request.user if request.user.is_authenticated else None
            )

            # Stream response
            for event in stream_response(user_query, conversation):
                # Ensure proper SSE format
                yield f"data: {json.dumps(event)}\n\n"
                
        except Exception as e:
            yield f'data: {{"type": "error", "message": "Server error: {str(e)}"}}\n\n'

    response = StreamingHttpResponse(
        event_generator(),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    response['Access-Control-Allow-Credentials'] = 'true'
    response['Access-Control-Allow-Methods'] = 'GET'
    return response