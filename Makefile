.PHONY: help build up down restart logs test clean status

help:
	@echo "NewsCatcher - Available Commands:"
	@echo ""
	@echo "  make build      - Build all Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View logs from all services"
	@echo "  make test       - Run backend tests"
	@echo "  make clean      - Stop services and remove volumes (WARNING: deletes data)"
	@echo "  make status     - Show status of all services"
	@echo ""

build:
	@echo "Building Docker images..."
	docker compose build

up:
	@echo "Starting NewsCatcher services..."
	docker compose up -d
	@echo ""
	@echo "✅ NewsCatcher is starting!"
	@echo ""
	@echo "Frontend (UI):      http://localhost:8501"
	@echo "Backend (API):      http://localhost:8000"
	@echo "API Docs:           http://localhost:8000/docs"
	@echo ""
	@echo "Run 'make logs' to view logs"
	@echo "Run 'make status' to check service status"

down:
	@echo "Stopping services..."
	docker compose down

restart:
	@echo "Restarting services..."
	docker compose restart

logs:
	docker compose logs -f

test:
	@echo "Running tests..."
	docker compose exec backend pytest tests/ -v --cov=app

clean:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v; \
		echo "Cleaned up successfully"; \
	fi

status:
	@echo "Service Status:"
	@docker compose ps

