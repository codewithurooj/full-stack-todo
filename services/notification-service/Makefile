.PHONY: help install setup test test-cov lint format run docker-build docker-run clean

help:
	@echo "Notification Service - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install Python dependencies"
	@echo "  make setup         Run development setup (generate keys, create .env)"
	@echo ""
	@echo "Development:"
	@echo "  make run           Run service locally"
	@echo "  make test          Run tests"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make lint          Lint code"
	@echo "  make format        Format code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-run    Run Docker container"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove temporary files"

install:
	pip install -r requirements.txt

setup:
	python setup_dev.py

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=app --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

lint:
	flake8 app tests --max-line-length=100 --exclude=__pycache__

format:
	black app tests
	isort app tests

run:
	python -m app.main

docker-build:
	docker build -t notification-service:latest .

docker-run:
	docker run \
		--env-file .env \
		--network host \
		notification-service:latest

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf htmlcov .coverage
