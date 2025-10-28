# Hackathon Chatbot 🤖

An AI-powered RAG (Retrieval-Augmented Generation) chatbot built for hackathons. Upload documents and ask questions using natural language!

![Hackathon Logo](frontend/public/hack-ai-thon.png)

## 🌟 Features

- **📄 Document Upload** - Supports PDF and Word documents (.pdf, .docx, .doc)
- **🔍 Semantic Search** - Uses vector embeddings for intelligent content retrieval
- **🤖 AI-Powered Responses** - Leverages Databricks LLM (Llama 4 Maverick) for natural language answers
- **💬 Chat Interface** - Beautiful React-based UI with markdown support
- **📊 Document Management** - View, delete, and manage uploaded documents
- **🔄 Auto-Processing** - Automatically processes documents on startup
- **🌐 Network Flexible** - Works across different networks and host configurations

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **FastAPI** - Modern web framework for building APIs
- **Sentence Transformers** - For document embeddings
- **PyPDF2 & python-docx** - Document parsing
- **Databricks LLM API** - AI response generation
- **File-based Vector Storage** - No external database needed

### Frontend (React/Vite)
- **React 18** - Modern UI framework
- **Vite** - Fast build tool
- **Axios** - HTTP client
- **React Markdown** - Rich text rendering

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Databricks workspace (for LLM access)

### Local Development

#### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r ../requirements.txt

# Run the server
python main.py
```

The backend will be available at `http://localhost:8000`

#### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

#### 3. Upload Documents
1. Open http://localhost:3000
2. Upload PDF or Word documents
3. Ask questions about your documents!

## ☁️ Databricks Deployment

This application is designed to run on Databricks. See detailed deployment instructions:

📖 **[Quick Start Guide](README_DEPLOYMENT.md)** - 5-minute deployment walkthrough  
📖 **[Complete Deployment Guide](DATABRICKS_DEPLOYMENT.md)** - Comprehensive guide with 3 deployment options  
📓 **[Databricks Notebook](databricks_backend_notebook.py)** - Ready-to-use notebook file  
🔧 **[Setup Script](databricks_setup.sh)** - Automated deployment script

### Quick Databricks Deploy
```bash
# Install Databricks CLI
pip install databricks-cli

# Configure authentication
databricks configure --token

# Run automated setup
chmod +x databricks_setup.sh
./databricks_setup.sh

# Follow the prompts to upload files and configure
```

## 📁 Project Structure

```
Hackthon_Chatbot/
├── backend/                    # Backend API
│   ├── main.py                # FastAPI application
│   ├── chat_handler.py        # LLM integration
│   ├── knowledge_base.py      # Vector storage
│   ├── document_processor.py  # Document parsing
│   └── __init__.py
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   └── ChatInterface.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
├── uploads/                    # Document storage
├── simple_db/                  # Vector embeddings storage
├── requirements.txt            # Python dependencies
├── databricks_backend_notebook.py  # Databricks notebook
├── databricks_setup.sh         # Deployment automation
├── DATABRICKS_DEPLOYMENT.md    # Deployment guide
└── README.md                   # This file
```

## 🔧 Configuration

### Backend Configuration
Edit `backend/chat_handler.py` to configure:
- **Databricks endpoint URL**
- **Access token**
- **LLM parameters** (temperature, max_tokens)

### Frontend Configuration
Edit `frontend/src/components/ChatInterface.jsx` to configure:
- **API base URL**
- **Suggested questions**
- **UI customization**

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| POST | `/upload` | Upload document |
| POST | `/chat` | Send chat message |
| GET | `/documents` | List documents |
| DELETE | `/documents/{filename}` | Delete document |
| DELETE | `/clear` | Clear all documents |

API Documentation available at: `http://localhost:8000/docs`

## 🧪 Testing

### Test Backend
```bash
# Health check
curl http://localhost:8000/health

# List documents
curl http://localhost:8000/documents
```

### Test Frontend
1. Open http://localhost:3000
2. Try suggested questions
3. Upload a test document
4. Ask questions about the document

## 🐛 Troubleshooting

### Backend Issues

**Issue: Module not found**
```bash
pip install -r requirements.txt
```

**Issue: Port already in use**
```bash
# Change port in backend/main.py
port = int(os.getenv("PORT", 8001))  # Use 8001 instead
```

### Frontend Issues

**Issue: Cannot connect to backend**
- Verify backend is running on port 8000
- Check `API_BASE_URL` in `ChatInterface.jsx`

**Issue: Build fails**
```bash
cd frontend
rm -rf node_modules
npm install
```

## 🔐 Security Notes

- **API Tokens**: Never commit API tokens to version control
- **CORS**: Configure allowed origins in production
- **Authentication**: Add authentication for production deployments
- **Rate Limiting**: Implement rate limiting for API endpoints

## 📈 Performance

- **Vector Search**: Uses cosine similarity for fast retrieval
- **Chunking**: Documents split into 1000-character chunks with 200-character overlap
- **Caching**: Embeddings cached for fast subsequent queries
- **Async**: Async request handling for better performance

## 🤝 Contributing

This project was built for the Hack-AI-Thon. Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Share improvements

## 📝 License

This project is open source and available for educational and hackathon purposes.

## 🎯 Use Cases

- **Hackathon Assistant** - Answer questions about event details
- **Document Q&A** - Query large document collections
- **Knowledge Base** - Build internal knowledge bases
- **Research Assistant** - Explore research papers and documentation
- **Customer Support** - Answer questions from documentation

## 🛠️ Tech Stack

**Backend:**
- FastAPI
- Sentence Transformers
- PyPDF2
- python-docx
- Databricks LLM API
- scikit-learn

**Frontend:**
- React 18
- Vite
- Axios
- React Markdown
- CSS3

**Infrastructure:**
- Databricks (Recommended)
- DBFS Storage
- Driver Proxy for API access

## 📞 Support

For deployment help:
1. Check [DATABRICKS_DEPLOYMENT.md](DATABRICKS_DEPLOYMENT.md) for detailed instructions
2. Review notebook output for error messages
3. Test API endpoints individually
4. Check Databricks cluster logs

## 🎉 Demo

The application includes sample data for the Hack-AI-Thon event. Try these questions:
- "Share me Hack-AI-Thon Registration link"
- "Show me Hack-AI-Thon schedule"
- "Show me Hack-AI-Thon location"
- "Show me Hack-AI-Thon contact information"

## 🚀 What's Next?

Potential improvements:
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Document comparison
- [ ] Advanced analytics dashboard
- [ ] User authentication
- [ ] Document versioning
- [ ] Export conversations
- [ ] Mobile app

---

**Built with ❤️ for Hack-AI-Thon 2025**

For questions or feedback, please open an issue or contact the development team.

