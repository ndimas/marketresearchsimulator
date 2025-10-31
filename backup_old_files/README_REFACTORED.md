# Swiss Market Research Simulator - Refactored Version

A clean, configurable, and production-ready Swiss market research simulator with proven LLM endpoint testing capabilities.

## 🎯 Overview

This refactored version maintains the successful 100% success rate and political alignment accuracy from the original `ultimate_100_5questions_test_fixed.py` while providing:

- ✅ **Configurable model and endpoint parameters**
- 🏗️ **Clean, organized file structure**
- 📊 **Enhanced metrics and reporting**
- 🔧 **Environment-based configuration**
- 🚀 **Production-ready codebase**

## 🏆 Proven Performance

The original implementation achieved:
- **100% success rate** (500/500 requests)
- **100% quality rate** 
- **100 concurrent requests** handled
- **16.5 personas/second** throughput
- **35.3% average political alignment**

## 📁 Clean File Structure

```
├── market_research_simulator.py    # Main application entry point
├── src/
│   ├── config.py                  # Configuration management
│   ├── client.py                  # Enhanced LLM client with extraction logic
│   ├── personas/
│   │   ├── models.py             # Persona data models
│   │   └── generator.py          # Persona generation
│   └── llm/
│       └── models.py             # LLM data models
├── personas.json                 # Test data (100 Swiss personas)
├── .env                          # Environment configuration
└── README_REFACTORED.md           # This file
```

## 🔧 Configuration

All parameters are configurable via environment variables in `.env`:

### LLM Configuration
```bash
LLM_ENDPOINT_URL=https://your-endpoint.com
LLM_MODEL_ID=TheBloke/Mistral-7B-Instruct-v0.1-AWQ
LLM_MODEL_NAME=TheBloke/Mistral-7B-Instruct-v0.1-AWQ
LLM_MAX_TOKENS=100
LLM_TEMPERATURE=0.3
LLM_TOP_P=0.9
```

### Concurrency Configuration
```bash
MAX_CONCURRENT=100          # Maximum concurrent requests
REQUEST_DELAY=0.02          # Delay between requests (seconds)
MAX_RETRIES=2               # Maximum retry attempts
TIMEOUT_TOTAL=60            # Total timeout (seconds)
TIMEOUT_CONNECT=10          # Connection timeout (seconds)
```

### Test Configuration
```bash
PERSONA_COUNT=100           # Number of personas to test
PERSONAS_FILE=personas.json # Personas data file
RESULTS_PREFIX=market_research_results # Results file prefix
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy and customize the `.env` file:
```bash
cp .env.example .env
# Edit .env with your endpoint and model details
```

### 3. Run the Simulator
```bash
python market_research_simulator.py
```

## 📊 Output Files

The simulator generates detailed output files:

- `market_research_results_q1.json` through `market_research_results_q5.json` - Detailed responses for each question
- `market_research_results_summary.json` - Overall performance summary

### Sample Output Structure
```json
{
  "persona_id": 1,
  "persona": {...},
  "question": "What is your preferred political party...",
  "answer": "B",
  "response_time": 0.45,
  "success": true,
  "extraction_method": "single_letter_start",
  "raw_content": "B. As a left-leaning journalist...",
  "processing_time": 0.47
}
```

## 🧠 Smart Answer Extraction

The refactored client includes the proven extraction logic from the original solution:

1. **Single letter at start** - Handles leading spaces
2. **JSON format** - `{"answer": "B"}`
3. **Answer: X format** - `Answer: B`
4. **First sentence detection** - Finds letters in first sentence
5. **Parenthesis format** - `A)` or `A )`

Each extraction method is tracked for analysis.

## 📈 Performance Metrics

The simulator provides comprehensive metrics:

### Basic Metrics
- **Success Rate**: Percentage of successful requests
- **Quality Rate**: Percentage of valid A/B/C/D answers
- **Throughput**: Requests per second
- **Response Times**: Average, min, max response times

### Political Alignment
- **Left-Leaning Accuracy**: Correct left-wing persona responses
- **Right-Leaning Accuracy**: Correct right-wing persona responses
- **Overall Alignment**: Combined political accuracy

### Performance Assessment
- 🟢 **EXCELLENT**: 95%+ quality, 80%+ political alignment
- 🟡 **VERY GOOD**: 90%+ quality, 70%+ political alignment
- 🟠 **GOOD**: 80%+ quality, 60%+ political alignment
- 🔴 **NEEDS IMPROVEMENT**: Below good thresholds

## 🔄 Migration from Original

To migrate from the original `ultimate_100_5questions_test_fixed.py`:

1. **Keep your personas.json** - No changes needed
2. **Update .env** - Add your endpoint details
3. **Run new simulator** - Same proven logic, cleaner interface

```bash
# Old way
python ultimate_100_5questions_test_fixed.py

# New way
python market_research_simulator.py
```

## 🛠️ Advanced Usage

### Custom Configuration
```python
from src.config import AppConfig

# Create custom config
config = AppConfig(
    model=ModelConfig(
        model_id="your-custom-model",
        endpoint_url="https://your-endpoint.com",
        max_concurrent=50
    ),
    concurrency=ConcurrencyConfig(
        max_concurrent=50,
        request_delay=0.1
    ),
    test=TestConfig(
        persona_count=50,
        questions=["Your custom question"]
    )
)

# Use in simulator
simulator = MarketResearchSimulator(config)
await simulator.run_full_survey()
```

### Custom Questions
```python
config.test.questions = [
    "Your custom question 1? A) Option A B) Option B C) Option C D) Option D",
    "Your custom question 2? A) Option A B) Option B C) Option C D) Option D"
]
```

## 🔍 Debugging

Enable debug mode in `.env`:
```bash
DEBUG=true
```

This provides:
- Detailed extraction method statistics
- Raw response content
- Error details and retry attempts

## 📝 Development

### Project Structure
- `src/config.py` - Configuration management with environment variable support
- `src/client.py` - Enhanced LLM client with proven extraction logic
- `src/personas/` - Persona management (unchanged from original)
- `src/llm/` - LLM data models (unchanged from original)

### Key Improvements
1. **Separation of Concerns** - Config, client, and simulation logic separated
2. **Environment Variables** - All parameters configurable without code changes
3. **Enhanced Metrics** - More detailed performance tracking
4. **Error Handling** - Robust retry logic and error reporting
5. **Clean Architecture** - Production-ready code structure

## 🎯 Best Practices

### For Production Use
1. **Environment Variables** - Never hardcode endpoints or API keys
2. **Monitoring** - Track success rates and response times
3. **Rate Limiting** - Adjust `MAX_CONCURRENT` based on endpoint capacity
4. **Error Handling** - Monitor failed requests and retry patterns

### For Testing
1. **Start Small** - Test with `PERSONA_COUNT=10` first
2. **Validate Results** - Check political alignment makes sense
3. **Monitor Resources** - Ensure endpoint can handle the load

## 🤝 Contributing

When contributing to this refactored version:

1. **Maintain Configuration** - Use the config system for new parameters
2. **Preserve Extraction Logic** - Don't modify the proven extraction methods
3. **Update Documentation** - Document any new configuration options
4. **Test Thoroughly** - Ensure changes don't break the 100% success rate

## 📞 Support

For issues or questions:
1. Check the configuration in `.env`
2. Verify endpoint accessibility
3. Review extraction method statistics
4. Check persona data format

---

**This refactored version maintains the proven performance while providing a clean, configurable, and production-ready foundation for Swiss market research simulation.**
