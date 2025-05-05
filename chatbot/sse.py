import json
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_GET
from .models import Conversation
from .llm_integration import stream_response

@require_GET
def chat_stream(request):
    def event_generator():
        user_query = request.GET.get('q')
        conversation_id = request.GET.get('conversation_id')
        
        if not user_query:
            yield 'data: {"type": "error", "message": "Empty query"}\n\n'
            return

        try:
            # Use existing conversation or create new one
            if conversation_id:
                conversation = Conversation.objects.get(id=conversation_id)
            else:
                conversation = Conversation.objects.create(
                    title=f"Chat: {user_query[:30]}..."
                )

            # Stream response
            for event in stream_response(user_query, conversation):
                # Include conversation ID in each event
                if event.get('type') == 'status':
                    event['conversation_id'] = conversation.id
                yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            error_data = {
                "type": "error",
                "message": f"Server error: {str(e)}",
                "conversation_id": conversation.id if 'conversation' in locals() else None
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    response = StreamingHttpResponse(
        event_generator(),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET'
    return response