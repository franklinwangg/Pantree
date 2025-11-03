# === Pantree Streamlit App ===
APP=app.py
VENV?=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

# === Default Commands ===

.PHONY: all run test clean install

all: run

# Create a virtual environment and install dependencies
install:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt || echo "⚠️  requirements.txt missing — please create one"

# Run the Streamlit app
run:
	@echo "🚀 Starting Pantree Streamlit app..."
	@$(VENV)/bin/streamlit run $(APP)

# Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	@rm -rf __pycache__ *.pyc .pytest_cache logs/
	@echo "✅ Clean complete."

# Reset only user-specific OAuth tokens, keep env + credentials
reset:
	@echo "🔁 Resetting Gmail authentication tokens..."
	@rm -f token.json token.pickle
	@echo "✅ Tokens cleared. You’ll be asked to reauthorize Gmail next time."