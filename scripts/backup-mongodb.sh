#!/bin/bash
# MongoDB Backup Script
set -e
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mongodb}"
MONGODB_URI="${MONGODB_URI:-mongodb://mongodb:27017}"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "${BACKUP_DIR}"
mongodump --uri="${MONGODB_URI}" --out="${BACKUP_DIR}/${DATE}" --gzip
tar -czf "${BACKUP_DIR}/backup_${DATE}.tar.gz" -C "${BACKUP_DIR}" "${DATE}"
rm -rf "${BACKUP_DIR}/${DATE}"
find "${BACKUP_DIR}" -name "backup_*.tar.gz" -mtime +7 -delete
echo "Backup completed: ${BACKUP_DIR}/backup_${DATE}.tar.gz"
