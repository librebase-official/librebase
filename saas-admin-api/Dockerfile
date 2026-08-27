FROM python:3.12-alpine
WORKDIR /app
COPY scripts/ ./scripts/
EXPOSE 54341
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:54341/health || exit 1
CMD ["python3", "scripts/admin_dashboard_server.py"]
