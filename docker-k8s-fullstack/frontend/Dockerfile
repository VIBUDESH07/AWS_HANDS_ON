FROM nginx:1.27-alpine

# Default BACKEND_URL — Compose/K8s-la env moolama override pannuvom
ENV BACKEND_URL=http://backend:8000

COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY public/ /usr/share/nginx/html/

EXPOSE 80
