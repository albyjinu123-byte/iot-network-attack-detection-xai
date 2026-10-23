# Contributing to SentinelAI

Thank you for your interest in contributing to SentinelAI! We welcome community contributions, bug fixes, performance improvements, and new feature modules.

## How to Contribute

1. **Fork the Repository**: Create your own feature branch from `main`.
2. **Set Up Development Environment**:
   - Backend: Install requirements in a virtual environment (`python -m venv venv`, `pip install -r requirements.txt`).
   - Frontend: Install packages with `npm install` inside `sentinel-ai/frontend`.
3. **Follow Code Quality Standards**:
   - Maintain PEP 8 guidelines for Python code.
   - Maintain TypeScript strict typing for React components.
   - Ensure the consensus feature names remain aligned between `pipeline.py` and `App.tsx`.
4. **Test Before Submitting**:
   - Run `npm run build` in `sentinel-ai/frontend` to verify bundling.
   - Verify that the FastAPI backend starts and routes test payloads cleanly (`python main.py`).
5. **Open a Pull Request**: Provide a descriptive title and explanation of changes.
