# GeoLLM

GeoLLM is a dynamic learning tool designed to bridge the gap between manual geospatial analysis and AI-driven approaches. It serves as a platform for structured experimentation and iterative learning, enabling researchers and practitioners to combine human expertise with AI capabilities effectively.

## Demo
https://geollm.astrowaffle.com/

## Project Philosophy

GeoLLM positions itself between traditional manual workflows and high-level AI agents, serving as a "Swiss Army knife" for:
- Prototyping and experimenting with geospatial data analysis
- Learning through structured iteration and experimentation
- Combining human expertise with AI pattern recognition
- Validating and contextualizing AI-driven insights

## Prerequisites

- Python 3.8+
- Node.js 18+
- PostgreSQL 14+ with PostGIS extension
- NASA Earthdata account
- Anthropic API key for Claude integration
- Google Earth Engine account (for satellite imagery)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nathanael-applied-alchemy/earthbanc_geollm.git
cd geollm
```

2. Install Python dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
npm install
```

## Database Setup

1. Install PostgreSQL and PostGIS:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib postgis

# macOS with Homebrew
brew install postgresql postgis
```

2. Start PostgreSQL service:
```bash
# Ubuntu/Debian
sudo service postgresql start

# macOS
brew services start postgresql
```

3. Create database and user:
```bash
sudo -u postgres psql

CREATE USER geollm_user WITH PASSWORD 'change_me_in_production';
CREATE DATABASE geollm_db;
GRANT ALL PRIVILEGES ON DATABASE geollm_db TO geollm_user;
\c geollm_db
CREATE EXTENSION postgis;
```

## Configuration

1. Set up environment variables:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your configuration:
```
APP_NAME=geollm
API_PORT=8009
FRONTEND_PORT=3009
DATABASE=postgres
DB_NAME=geollm_db
DB_USER=geollm_user
DB_PASSWORD=change_me_in_production
DB_HOST=localhost
DB_PORT=5432
DATABASE_URL=postgresql://geollm_user:change_me_in_production@localhost:5432/geollm_db

NASA_EARTHDATA_USERNAME=your_username
NASA_EARTHDATA_PASSWORD=your_password
ANTHROPIC_API_KEY=your_api_key
```

## Database Migration

Run Alembic migrations to set up the database schema:
```bash
# Initialize Alembic (if not already initialized)
alembic init alembic

# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head
```

## Starting the Application

Use the provided start script to launch both the FastAPI backend and Next.js frontend:

```bash
# Start both servers in daemon mode
python start.py start both --daemon

# Or start without daemon mode in two terminals
python start.py start front
python start.py start back
```

The application will be available at:
- Frontend: `http://localhost:3009`
- Backend API: `http://localhost:8009`

## Project Structure

```
earthbanc_geollm/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── core/
│   │   ├── crud/
│   │   ├── data/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   └── services/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── lib/
│   │   └── styles/
│   └── package.json
└── start.py
```

## Framework for Critical AI Collaboration

GeoLLM promotes a structured approach to AI collaboration:

1. Ask Structured Questions:
   - Identify appropriate data sources
   - Define validation criteria
   - Surface underlying assumptions

2. Iterative Exploration:
   - Begin with broad queries
   - Refine based on feedback
   - Use AI outputs to guide manual investigation

3. Confidence Assessment:
   - Include uncertainty ranges
   - Highlight data gaps
   - Validate against domain expertise

## Example Use Case: Cropland Analysis

The project includes a comprehensive cropland analysis example that demonstrates:

1. Data Integration:
   - Sentinel-2 imagery processing
   - Soil map integration
   - Local agricultural survey data

2. Critical Analysis:
   - Classification threshold evaluation
   - Seasonal variation consideration
   - Boundary condition assessment

3. Iterative Refinement:
   - Algorithm comparison
   - Edge case handling
   - Result validation

## Additional Resources

1. GeoLLM URL: geollm.astrowaffle.com
2. https://docs.google.com/document/d/1jmxOM9mEgLTsytqRr9KzAtG4WhoQ1VepoU-gG8tW3u4/edit?usp=sharing

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions and support, please open an issue in the GitHub repository.
