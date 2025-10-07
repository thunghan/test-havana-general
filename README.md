# Havana University Chat Bot

A web-based chat bot application that allows prospective students to learn more about Havana University. The application includes real-time chat with AI assistance, human escalation capabilities, and an admin dashboard for monitoring and intervention.

## Features

### Student Chat Page
- Real-time chat interface with AI assistant
- AI powered by Google Gemini 2.5 Pro or OpenAI GPT-4o
- Automatic escalation to human operator when needed (via AI tool calling)
- Intelligent call booking through natural language (AI handles slot retrieval and booking)
- Chat history management
- Connection status indicators

### Admin Dashboard
- Monitor all student chats in real-time
- Toggle between AI models (Gemini/GPT-4o)
- Manual intervention toggle for each chat
- Send messages as human operator
- View complete chat history

## Showcase

### Scenario 1: AI Answering Simple Questions

The AI chatbot answers common questions about Havana University based on the knowledge base.

![AI answering simple questions](./docs/scenario-1-simple-questions.mov)

### Scenario 2: AI Escalating to Human

When the AI encounters a question it cannot answer or the student requests human help, it automatically escalates to a human operator.

![AI escalating to human operator](./docs/scenario-2-ai-escalation.mov)

### Scenario 3: Human Admin Manual Takeover

An admin can manually enable human intervention mode to take over any conversation, allowing direct communication with the student.

![Admin manual takeover](./docs/scenario-3-manual-takeover.mov)

### Scenario 4: AI Making a Booking

The AI intelligently handles booking requests by retrieving available slots and confirming appointments through natural language conversation.

![AI making a booking](./docs/scenario-4-booking.mov)

## Tech Stack

### Backend
- **Python 3.x** with Flask 3.0.0
- **Flask-SocketIO 5.3.6** for real-time communication
- **LangChain 0.3.27** with OpenAI and Google Generative AI integrations
- **LangChain Tool Calling** for AI function execution (human escalation, booking management)
- **MySQL 8.0** with connection pooling for data persistence
- **python-dotenv** for environment configuration

### Frontend
- **Next.js 15** with TypeScript
- **React 19** for UI components
- **Socket.IO Client** for real-time updates
- **shadcn/ui** component library with Tailwind CSS
- **Lucide React** for icons

### Architecture & Design Choices

**Monolithic Deployment with Static Frontend Serving**
- The Next.js frontend is built into static assets and served from Flask's `static/` directory
- This simplifies running the app to a single server process for the purpose of this demo
- Trade-off: Less optimal for scaling compared to separate frontend/backend deployments (see Future Improvements)

**Real-Time Communication via WebSockets**
- Flask-SocketIO enables bidirectional communication between students, AI, and admin operators
- Allows instant message delivery, escalation notifications, and admin monitoring without polling
- Critical for the live intervention feature where admins can monitor and seamlessly take over conversations

**AI Tool Calling for Extensibility**
- LangChain's structured tool calling allows the AI to execute functions (escalation, booking) declaratively
- The AI decides when to use tools based on conversation context, not hardcoded triggers
- Easy to extend with new capabilities (e.g., application status checks, course queries) by adding tool definitions

**Database Connection Pooling**
- MySQL connection pooling prevents connection exhaustion under concurrent load
- Auto-reconnection logic handles transient database failures gracefully
- Essential for WebSocket applications where connections are long-lived

**Model Flexibility**
- Support for both OpenAI and Google Gemini allows cost optimization and feature comparison
- Admin can switch models in real-time to adapt to different use cases or API availability

## AI Tool Calling

The chatbot uses LangChain's tool calling feature to intelligently handle complex operations:

### Available Tools

1. **`human_escalation`**
   - Automatically escalates to human operator when AI cannot handle the query
   - Triggered when information is unavailable or user explicitly requests human help
   - Sets `is_human_enabled` flag in database

2. **`get_booking_slots`**
   - Retrieves available time slots from database
   - AI automatically calls this when conversation moves toward scheduling
   - Returns structured data that AI formats naturally for the user

3. **`book_time_slot`**
   - Books a time slot based on user selection
   - Supports both explicit slot IDs and natural language (e.g., "9am on October 10th")
   - AI parses user intent and extracts date/time information
   - Performs database booking and confirms to user

### How It Works

1. Student sends a message
2. AI analyzes the message and decides if tools are needed
3. If yes, AI calls appropriate tool(s) with extracted parameters
4. Tool executes and returns results
5. AI generates a natural, friendly response based on tool results
6. Response is sent to student with any necessary flags (escalation, booking confirmation)

## Project Structure

```
test-havana-general/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── chatbot.py             # LangChain chatbot logic
│   ├── requirements.txt       # Python dependencies
│   ├── run_migrations.py      # Database migration script
│   ├── school_data.txt        # School information knowledge base
│   ├── db/
│   │   ├── database.py        # Database utility class
│   │   └── migrations/        # SQL migration files
│   └── static/                # Built frontend files (generated)
├── frontend/
│   ├── app/                   # Next.js app directory
│   │   ├── student-chat/      # Student chat page
│   │   ├── admin/             # Admin dashboard page
│   │   └── layout.tsx         # Root layout with sidebar
│   ├── components/            # React components
│   ├── lib/                   # Utilities (socket, api, types)
│   └── package.json           # Node dependencies
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- MySQL 8.0
- OpenAI API key (optional, for GPT-4o)
- Google AI API key (for Gemini)

### 1. Database Setup

Setup and start MySQL:

If using devbox:

```bash
devbox shell
devbox services up mysql
```

If using brew:

```bash
brew install mysql
brew services start mysql
```

Create the database and admin user for the app:

```bash
mysql -u root -p
```

```sql
CREATE DATABASE havana_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'admin'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON havana_dev.* TO 'admin'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2. Backend Setup

Initialize and start a new virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Navigate to the backend directory:

```bash
cd backend
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file with your configuration:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=havana_dev
DB_USER=admin
DB_PASSWORD=password

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

Run database migrations:

```bash
python run_migrations.py
```

### 3. Frontend Setup

Navigate to the frontend directory:

```bash
cd ../frontend
```

Install Node dependencies:

```bash
npm install
```

Build the frontend (outputs to `backend/static`, optional since the latest compiled frontend code is checked in):

```bash
npm run build
```

### 4. Run the Application

From the backend directory, start the Flask server:

```bash
cd ../backend
python app.py
```

The application will be available at: **http://localhost:3000**

## Usage

### For Students

1. Navigate to the **Student Chat** page (default landing page)
2. Click "New Chat" to start a conversation
3. Ask questions about Havana University
4. The AI will respond based on the school information
5. If needed, the chat can escalate to a human operator
6. Book follow-up calls when time slots are offered

### For Administrators

1. Navigate to the **Admin** page from the sidebar
2. View all active chats in the right panel
3. Toggle between AI models (Gemini/GPT-4o) using the switch
4. Select a chat to monitor
5. Enable "Human Intervention" to take over the conversation
6. Send messages directly to students when intervention is active

## Database Schema

### chats
- `id` - Primary key
- `is_human_enabled` - Boolean flag for human intervention
- `created_at` - Timestamp
- `deleted_at` - Soft delete timestamp

### chat_history
- `id` - Primary key
- `chat_id` - Foreign key to chats
- `role` - Enum: 'ai', 'human', 'human_operator'
- `message` - Text content
- `created_at` - Timestamp
- `deleted_at` - Soft delete timestamp

### bookings
- `id` - Primary key
- `date` - Date of appointment
- `time` - Time slot (e.g., '0900', '1400')
- `chat_id` - Foreign key to chats (NULL if available)
- `created_at` - Timestamp
- `deleted_at` - Soft delete timestamp

## Development

### AI-Assisted Development

This project was developed with the assistance of AI-powered development tools:

- **Cursor AI IDE**: Used for code generation, refactoring and debugging assistance throughout the development process. Cursor's AI capabilities helped accelerate feature implementation, particularly for complex integrations like LangChain tool calling and WebSocket event handling.

- **Gemini CLI**: Leveraged for rapid prototyping and documentation generation. The CLI interface allowed for quick iterations on architecture decisions and implementation strategies.

### Backend Development

Run the Flask app in debug mode:

```bash
cd backend
python app.py
```

The server will reload automatically on code changes.

### Frontend Development

For frontend development with hot reload:

```bash
cd frontend
npm run dev
```

Then access the Next.js dev server at http://localhost:3000

When ready to deploy, build and copy to backend:

```bash
npm run build
```

**Note:** The Next.js dev server runs on port 3000 by default, but when deployed via the Flask backend, the application uses the Flask server port (also 3000 by default).

### Modifying School Information

Edit `backend/school_data.txt` to update the knowledge base. The AI will only answer questions based on this file.

## API Endpoints

### REST API

- `GET /api/chats` - Get all chats
- `GET /api/chats/:id` - Get specific chat with history
- `GET /api/model` - Get current AI model
- `POST /api/model` - Set AI model (body: `{"model": "openai" | "gemini"}`)

### SocketIO Events

#### Student Events
- `student_connect` - Connect to a chat
- `student_message` - Send a message (AI uses tool calling to handle bookings)

#### Admin Events
- `admin_connect` - Connect to monitor a chat
- `admin_disconnect_from_chat` - Disconnect from a chat
- `admin_message` - Send message as operator
- `toggle_human_enabled` - Toggle human intervention

#### Server-Emitted Events
- `new_message` - New message in chat
- `escalation_triggered` - Human intervention activated
- `booking_confirmed` - Booking successfully completed
- `admin_status_changed` - Admin connection status changed
- `human_enabled_changed` - Human intervention status changed

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DB_HOST | MySQL host | localhost |
| DB_PORT | MySQL port | 3306 |
| DB_NAME | Database name | havana_dev |
| DB_USER | Database user | admin |
| DB_PASSWORD | Database password | password |
| OPENAI_API_KEY | OpenAI API key | - |
| GOOGLE_API_KEY | Google AI API key | - |
| PORT | Flask server port | 3000 |

## Notes

- Authentication and authorization are out of scope for this implementation
- Performance optimization and security hardening are not included
- The application uses soft deletes (deleted_at column) but doesn't expose deletion functionality
- Booking slots are pre-populated for the next 7 days with 6 time slots per day

## Troubleshooting

### Database Connection Issues

Make sure MySQL is running and credentials are correct:

```bash
mysql -u admin -p havana_dev
```

### Frontend Build Issues

Clear Next.js cache and rebuild:

```bash
cd frontend
npm run clean
npm run build
```

### SocketIO Connection Issues

Check that:
1. Flask server is running on port 3000
2. CORS is properly configured
3. Browser console for any connection errors

## Future Improvements

This section outlines potential enhancements that could improve the application's scalability, maintainability, and functionality:

### Infrastructure & Deployment

1. **Frontend Deployment to Cloud Storage**
   - Deploy the frontend to Google Cloud Storage (GCS) or AWS S3 instead of serving from the Flask `static/` folder
   - Benefits: Better CDN integration, reduced backend load, independent frontend scaling
   - Serve via CloudFront (AWS) or Cloud CDN (GCP) for global performance

2. **Separate WebSocket Service**
   - Extract WebSocket handling into a dedicated Node.js service instead of embedding in Python
   - Benefits: Better WebSocket performance, language-appropriate tooling, independent scaling
   - Could use Socket.IO server with Redis adapter for multi-instance support

3. **Container Orchestration**
   - Containerize services with Docker and orchestrate with Kubernetes
   - Implement auto-scaling based on load
   - Add health checks and graceful shutdown handling

### Database & Data Management

4. **Advanced RAG (Retrieval-Augmented Generation) Design**
   
   **Vector Database Integration:**
   - Use vector databases (Pinecone, Weaviate, or ChromaDB) to store embeddings of school data
   - Implement semantic search to find relevant information based on similarity matching
   - Benefits: More accurate answers, handles larger knowledge bases, better context retrieval
   
   **Graph RAG:**
   - Store structured school data in a graph database (Neo4j, Memgraph)
   - Use Cypher queries to traverse relationships and retrieve contextually relevant data
   - Benefits: Better handling of complex relationships (courses → departments → faculty)
   - Enables queries like "Which professors teach AI courses in the CS department?"
   
   **Hybrid Approach:**
   - Combine vector search for semantic understanding with graph traversal for structured queries
   - Use knowledge graphs for entities and relationships, vectors for unstructured content

5. **Database Optimization**
   - Implement database read replicas for scaling read operations
   - Add caching layer (Redis) for frequently accessed data (chat lists, booking slots)
   - Implement database connection pooling with automatic reconnection (already partially implemented)
   - Add database indexes on frequently queried columns

### AI & Chat Features

6. **Enhanced AI Capabilities**
   - Add support for streaming responses for better UX
   - Implement conversation summarization for long chat histories
   - Add multilingual support with language detection
   - Fine-tune models on university-specific terminology and common questions

7. **Advanced Tool Calling**
   - Add more tools: check application status, course availability, financial aid calculator
   - Implement tool chaining for complex multi-step operations
   - Add fallback strategies when tools fail

8. **Conversation Analytics**
   - Track common questions and satisfaction metrics
   - Identify knowledge gaps in the school data
   - A/B testing for different prompt strategies

### Security & Authentication

9. **Authentication & Authorization**
   - Implement JWT-based authentication for students and admins
   - Add role-based access control (RBAC)
   - Integrate with university SSO systems (SAML, OAuth)
   - Rate limiting to prevent abuse

10. **Security Hardening**
    - Input sanitization and validation
    - SQL injection prevention (use parameterized queries consistently)
    - XSS protection in frontend
    - HTTPS enforcement
    - API key rotation and secrets management (AWS Secrets Manager, HashiCorp Vault)

### Monitoring & Observability

11. **Logging & Monitoring**
    - Structured logging with log aggregation (ELK stack, Datadog)
    - Application performance monitoring (APM)
    - Real-time alerting for errors and performance degradation
    - Track AI model performance and costs

12. **Error Handling & Resilience**
    - Implement circuit breakers for external API calls
    - Add retry logic with exponential backoff
    - Graceful degradation when services are unavailable
    - Better error messages for users

### User Experience

13. **Rich Media Support**
    - Support for image uploads (campus photos, documents)
    - Video chat integration for human operators
    - Screen sharing capabilities
    - File attachments for application documents

14. **Enhanced UI/UX**
    - Typing indicators for both AI and human operators
    - Read receipts
    - Message reactions and feedback buttons
    - Dark mode support
    - Mobile-responsive design improvements
    - Accessibility (WCAG 2.1 compliance)

### Testing & Quality

15. **Comprehensive Testing**
    - Unit tests for backend logic
    - Integration tests for API endpoints
    - E2E tests for critical user flows
    - Load testing for scalability validation
    - AI response quality testing

16. **Code Cleanup and Maintenance**
    - Reorganize code to make it more modular
    - Clean unused functions
    - Optimize logic and bug fixes

### Business Features

17. **Booking System Enhancements**
    - Calendar integration (Google Calendar, Outlook)
    - Email/SMS notifications for bookings
    - Timezone support for international students
    - Rescheduling and cancellation flows
    - Virtual meeting link generation (Zoom, Meet)

18. **Multi-Channel Support**
    - WhatsApp or Telegram integration
    - Facebook Messenger bot
    - SMS chatbot
    - Unified inbox for all channels

19. **CRM Integration**
    - Sync conversations with Salesforce, HubSpot
    - Lead scoring based on engagement
    - Automated follow-up sequences

20. **Building POC for Demos**
    - Add utils to scrape websites of potential clients
    - White labeling

## License

This project is for the Havana take-home test.
