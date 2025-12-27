#!/bin/bash
# MongoDB Startup Script for Compute Engine

# Install MongoDB
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
   sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

sudo apt-get update
sudo apt-get install -y mongodb-org

# Configure MongoDB for network access
sudo sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/' /etc/mongod.conf

# Enable and start MongoDB
sudo systemctl enable mongod
sudo systemctl start mongod

# Create admin user
sleep 10
mongosh --eval '
db = db.getSiblingDB("admin");
db.createUser({
  user: "admin",
  pwd: "ManusAI2024!",
  roles: [{role: "root", db: "admin"}]
});
'

# Enable authentication
echo "security:" | sudo tee -a /etc/mongod.conf
echo "  authorization: enabled" | sudo tee -a /etc/mongod.conf

sudo systemctl restart mongod

echo "MongoDB installation completed!"
