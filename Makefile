.PHONY: run-neo4j run-backend run-frontend run-all stop wait-neo4j

run-neo4j:
	docker compose up -d neo4j

wait-neo4j:
	@echo "Waiting for Neo4j to become healthy..."
	@until docker compose ps neo4j | grep -q "healthy"; do sleep 2; done
	@echo "Neo4j is ready!"

run-backend:
	cd backend && poetry run uvicorn app.main:app --reload --reload-dir app &

run-frontend:
	cd frontend && npm run dev &

run-all: run-neo4j wait-neo4j run-backend run-frontend
	@echo "Все сервисы запущены!"
	@echo "Neo4j:    http://localhost:7474"
	@echo "Backend:  http://localhost:8000/docs"
	@echo "Frontend: http://localhost:5173"

stop:
	@echo "Останавливаем сервисы..."
	-docker compose stop neo4j
	-pkill -f "uvicorn app.main:app"
	-pkill -f "vite"
	@echo "Готово."