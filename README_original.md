# Swiss Market Research Agency: Persona-Based LLM Querying

A comprehensive system for simulating Swiss voting-age citizen responses for market research using LLM-powered personas deployed on RunPod with RTX 5090 GPUs.

## Project Overview

This project simulates Swiss voting-age citizen responses for market research by:
1. **Generating 100 realistic personas** representing Swiss citizens with proper demographic distribution
2. **Deploying Llama 3.1 8B** on RunPod RTX 4090 with optimized vLLM configuration
3. **Querying all personas simultaneously** with market research questions
4. **Analyzing responses** across demographic dimensions

## Features

- 🇨🇭 **Realistic Swiss Demographics**: Proper representation of languages, cantons, age groups, and political leanings
- 🚀 **High Performance**: Optimized for 100+ concurrent requests using async processing
- 📊 **Comprehensive Analysis**: Detailed demographic breakdown of responses
- 🔧 **Easy Deployment**: Automated RunPod deployment with optimized Docker configuration
- 🧪 **Full Test Suite**: Comprehensive unit and integration tests

## Project Structure

```
swiss-market-research-llm/
├── persona_generator.py      # Swiss persona generation with realistic demographics
├── runpod-deployment.py       # RunPod deployment configuration and scripts
├── main.py                    # Main querying and analysis system
├── test_suite.py              # Comprehensive test suite
├── pyproject.toml             # Project dependencies
├── project.md                 # Detailed project specifications
└── README.md                  # This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- RunPod account with API key
- Access to Llama 3.1 8B model (Hugging Face)

### Installation

1. **Clone and install dependencies:**
```bash
git clone <repository-url>
cd swiss-market-research-llm
pip install -e .
```

2. **Set up environment:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual API key
nano .env
# Add your RunPod API key: RUNPOD_API_KEY=your_actual_api_key_here
```

### Usage

#### Step 1: Generate Personas
```bash
python persona_generator.py
```
This creates `personas.json` with 100 diverse Swiss personas.

#### Step 2: Deploy LLM on RunPod
```bash
python runpod-deployment.py
```
This creates deployment files in the `deployment/` directory.

Deploy to RunPod:
```bash
cd deployment
./deploy.sh
```

Test the deployment:
```bash
./test.sh
```

#### Step 3: Run Market Research Queries
```bash
python main.py
```
This will:
- Load personas from `personas.json`
- Query each persona with 5 predefined research questions
- Save responses to `responses_q*.json`
- Generate analysis in `analysis_q*.json`

## Configuration

### Customizing Personas

Edit `persona_generator.py` to modify:
- Canton distribution and weights
- Occupation and education options
- Political party weightings
- Demographic targets

### Customizing Questions

Modify the `questions` list in `main.py`:
```python
questions = [
    "What is your preferred political party in the next Swiss election?",
    "What is your opinion on Switzerland's environmental policies?",
    # Add your custom questions here
]
```

### Performance Tuning

Adjust concurrent request limits in `main.py`:
```python
results = await query_handler.query_all_personas(personas, question, max_concurrent=50)
```

## API Reference

### PersonaGenerator

```python
from persona_generator import SwissPersonaGenerator

generator = SwissPersonaGenerator()
personas = generator.generate_personas(count=100)
generator.save_personas(personas, "my_personas.json")
```

### RunPodDeployer

```python
from runpod_deployment import RunPodDeployer

deployer = RunPodDeployer(api_key="your-api-key")
deployer.create_deployment_files("meta-llama/Meta-Llama-3.1-8B-Instruct")
```

### SwissMarketResearchQuery

```python
from main import SwissMarketResearchQuery

query_handler = SwissMarketResearchQuery(endpoint_url, model_id)
results = await query_handler.query_all_personas(personas, question)
query_handler.save_results(results, "results.json")
query_handler.analyze_responses(results, "analysis.json")
```

## Output Files

### Personas (`personas.json`)
```json
[
    {
        "id": 1,
        "age": 35,
        "gender": "Male",
        "canton": "Zurich",
        "language": "German",
        "occupation": "Engineer",
        "education": "Master",
        "political_leaning": "Center",
        "description": "A 35-year-old male from Zurich who works as an engineer..."
    }
]
```

### Responses (`responses_q1.json`)
```json
[
    {
        "persona_id": 1,
        "persona": {...},
        "question": "What is your preferred political party?",
        "answer": "SVP",
        "response_time": 1.23,
        "success": true,
        "error_message": null
    }
]
```

### Analysis (`analysis_q1.json`)
```json
{
    "total_respondents": 100,
    "question": "What is your preferred political party?",
    "by_language": {
        "German": {"count": 65, "answers": [...]},
        "French": {"count": 23, "answers": [...]}
    },
    "by_canton": {...},
    "by_age_group": {...},
    "by_political_leaning": {...},
    "response_statistics": {
        "avg_response_length": 12.5,
        "unique_answers": 8
    }
}
```

## Testing

Run the complete test suite:
```bash
python -m unittest test_suite.py -v
```

Or run specific test categories:
```bash
python -m unittest test_suite.TestPersonaGenerator -v
python -m unittest test_suite.TestRunPodDeployment -v
python -m unittest test_suite.TestSwissMarketResearchQuery -v
```

## Performance Metrics

- **Persona Generation**: < 1 second for 100 personas
- **Deployment Setup**: 5-10 minutes on RunPod
- **Query Processing**: ~30-60 seconds for 100 concurrent queries
- **Memory Usage**: Optimized for RTX 4090 (24GB VRAM)
- **Concurrency**: Supports 50+ simultaneous requests

## Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Check RunPod API key is valid
   - Verify model access permissions
   - Ensure sufficient GPU quota

2. **Query Timeouts**
   - Reduce `max_concurrent` parameter
   - Check endpoint health with test script
   - Increase timeout values in `main.py`

3. **Persona Generation Issues**
   - Verify Swiss demographic data
   - Check linguistic diversity requirements
   - Validate age distribution

### Debug Mode

Enable verbose logging:
```bash
export DEBUG=true
python main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:
- Check the test suite for usage examples
- Review `project.md` for detailed specifications
- Run `python main.py --help` for command-line options

## Acknowledgments

- **RunPod** for providing GPU infrastructure
- **Meta AI** for the Llama 3.1 model
- **vLLM** team for high-performance inference
- Swiss Federal Statistical Office for demographic data patterns
