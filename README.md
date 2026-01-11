# AI Influencer Discovery API

A FastAPI-based application for discovering and analyzing influencers using AI.

## Features

- 🔍 Search and discover influencers across multiple platforms
- 📊 Detailed influencer analytics and insights
- 🎯 Filter by platform, followers, category, and more
- 🤖 AI-powered analysis and recommendations
- 📈 Trending categories and insights

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip or poetry

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd ai-influener-discovery
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application:

```bash
uvicorn main:app --reload
```

The API will be available at:

- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check

- `GET /health` - Check API health status

### Influencer Discovery

- `GET /api/v1/influencers/` - Search influencers with filters
- `GET /api/v1/influencers/{influencer_id}` - Get influencer details
- `POST /api/v1/influencers/analyze` - Analyze a new influencer
- `GET /api/v1/influencers/trending/categories` - Get trending categories

## Project Structure

```
ai-influener-discovery/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── influencers.py
│   │       └── router.py
│   ├── core/
│   │   └── config.py
│   ├── models/
│   │   └── influencer.py
│   └── services/
│       └── influencer_service.py
├── main.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
ruff check .
```

## Next Steps

- [ ] Integrate with social media platform APIs (Twitter, Instagram, YouTube)
- [ ] Add database for storing influencer data
- [ ] Implement AI/ML models for influencer analysis
- [ ] Add authentication and rate limiting
- [ ] Implement caching for better performance
- [ ] Add comprehensive test coverage

## License

MIT
