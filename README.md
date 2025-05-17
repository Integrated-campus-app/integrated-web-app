# Integrated Campus Web App - Chatbot

A powerful chatbot application integrated with DeepSeek's API and a local knowledge base for enhanced responses.

## Features

- Real-time chat interface with message status tracking
- File attachment support for messages
- Local knowledge base with document processing
- Integration with DeepSeek's API for intelligent responses
- Conversation management (create, archive, delete)
- Message retry functionality for failed messages
- Server-Sent Events (SSE) for real-time updates
- Comprehensive error handling and logging

## Prerequisites

- Python 3.8+
- Node.js 14+
- DeepSeek API key
- Redis (for real-time updates)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd integrated-web-app
```

2. Set up the Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

4. Install frontend dependencies:

```bash
cd Integrated-campus-web-app
npm install
```

5. Create a `.env` file in the `integrated-web-app` directory:

```
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEBUG=True
SECRET_KEY=your_secret_key_here
```

6. Run migrations:

```bash
python manage.py migrate
```

7. Initialize the knowledge base:

```bash
python manage.py init_knowledge_base --documents-dir=documents
```

## Running the Application

1. Start the Django development server:

```bash
python manage.py runserver
```

2. Start the frontend development server:

```bash
cd Integrated-campus-web-app
npm start
```

The application will be available at:

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000

## Project Structure

```
integrated-web-app/
├── chatbot/
│   ├── knowledge_base/
│   │   ├── config.py
│   │   └── processor.py
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── llm_integration.py
├── Integrated-campus-web-app/
│   ├── src/
│   │   ├── Components/
│   │   │   ├── MessageBubble.jsx
│   │   │   └── ConversationSidebar.jsx
│   │   └── Pages/
│   │       └── Chatbot.jsx
│   └── package.json
└── requirements.txt
```

## API Endpoints

- `GET /api/chatbot/conversations/` - List conversations
- `POST /api/chatbot/conversations/` - Create conversation
- `GET /api/chatbot/conversations/{id}/` - Get conversation details
- `PATCH /api/chatbot/conversations/{id}/` - Update conversation
- `DELETE /api/chatbot/conversations/{id}/` - Delete conversation
- `GET /api/chatbot/messages/` - List messages
- `POST /api/chatbot/messages/` - Create message
- `GET /api/chatbot/messages/{id}/` - Get message details
- `PATCH /api/chatbot/messages/{id}/` - Update message
- `POST /api/chatbot/messages/{id}/retry/` - Retry failed message
- `GET /api/chatbot/stream/` - SSE endpoint for real-time updates

## Testing

Run the test suite:

```bash
python manage.py test chatbot
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
