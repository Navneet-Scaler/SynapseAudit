# Deployment Notes

## Staging & Production Deployment Setup

### 1. Database Migrations
Deploy the PostgreSQL schema script `schema/database_setup.sql` to your RDS or PostgreSQL instance.
```bash
psql -h <host> -U <user> -d synapse_audit -f schema/database_setup.sql
```

### 2. Streamlit Dashboard Hosting
Host the Streamlit dashboard on a containerized service (e.g., AWS ECS, GCP Cloud Run) or a VM (e.g., EC2) behind an Nginx reverse proxy.
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "dashboards/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
