FROM mongo:7.0

# إضافة healthcheck
HEALTHCHECK --interval=10s --timeout=5s --start-period=40s --retries=3 \
  CMD mongosh --eval "db.adminCommand('ping')" || exit 1

EXPOSE 27017

CMD ["mongod", "--bind_ip_all"]
