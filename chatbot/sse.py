import json
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_GET
from .models import Conversation, Message
from .llm_integration import stream_response

@require_GET
def chat_stream(request):
    def event_generator():
        conversation_id = request.GET.get('conversation_id')
        
        if not conversation_id:
            yield 'data: {"type": "error", "message": "No conversation ID provided"}\n\n'
            return

        try:
            # Get the conversation
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Get the last user message
            last_message = Message.objects.filter(
                conversation=conversation,
                is_user=True,
                is_deleted=False
            ).order_by('-created_at').first()
            
            if not last_message:
                yield 'data: {"type": "error", "message": "No message found in conversation"}\n\n'
                return

            # Stream response
            for event in stream_response(last_message.content, conversation):
                yield f"data: {json.dumps(event)}\n\n"

        except Conversation.DoesNotExist:
            error_data = {
                "type": "error",
                "message": "Conversation not found",
                "conversation_id": conversation_id
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        except Exception as e:
            error_data = {
                "type": "error",
                "message": f"Server error: {str(e)}",
                "conversation_id": conversation_id
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    response = StreamingHttpResponse(
        event_generator(),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response