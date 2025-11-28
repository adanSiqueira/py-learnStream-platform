# ================================
# Alembic Commands via Docker
# ================================

APP=app

# Create new migration
migrate:
	docker compose exec $(APP) alembic revision --autogenerate -m "$(m)"

# Upgrade to latest migration
upgrade:
	docker compose exec $(APP) alembic upgrade head

# Downgrade one step
downgrade:
	docker compose exec $(APP) alembic downgrade -1

# Show current migration
current:
	docker compose exec $(APP) alembic current

# List all migrations
history:
	docker compose exec $(APP) alembic history

# Apply migrations fresh after deleting database
reset-db:
	docker compose down -v
	docker compose up -d
	docker compose exec $(APP) alembic upgrade head