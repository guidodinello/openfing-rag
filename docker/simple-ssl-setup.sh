#!/bin/bash
# simple-ssl-setup.sh - Minimal SSL certificate generation

set -e

DOMAIN="openfingchat.duckdns.org"
EMAIL="guido.dinello+openfing-chat@gmail.com"

echo "🚀 Simple SSL setup for $DOMAIN"

# Step 1: Create minimal nginx config if it doesn't exist
echo "📝 Creating minimal nginx config..."
mkdir -p docker/nginx/conf.d
cat > docker/nginx/conf.d/ssl-only.conf << 'EOF'
server {
    listen 80;
    server_name openfingchat.duckdns.org;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location = /health {
        return 200 '{"status": "nginx ready for SSL"}';
        add_header Content-Type application/json;
    }

    location / {
        return 200 'SSL certificate generation in progress...';
        add_header Content-Type text/plain;
    }
}
EOF

# Step 2: Create minimal docker-compose
echo "📝 Creating minimal docker-compose..."
cat > docker/docker-compose.ssl-only.yml << 'EOF'
services:
    nginx-ssl:
        image: nginx:alpine
        ports:
            - "80:80"
        volumes:
            - ./nginx/conf.d/ssl-only.conf:/etc/nginx/conf.d/default.conf:ro
            - certbot_conf:/etc/letsencrypt:ro
            - certbot_www:/var/www/certbot
        restart: unless-stopped

    certbot:
        image: certbot/certbot:latest
        volumes:
            - certbot_conf:/etc/letsencrypt
            - certbot_www:/var/www/certbot
        command: certonly --webroot --webroot-path=/var/www/certbot --email guido.dinello+openfing-chat@gmail.com --agree-tos --no-eff-email -d openfingchat.duckdns.org

volumes:
    certbot_conf:
        driver: local
    certbot_www:
        driver: local
EOF

# Step 3: Start minimal nginx
echo "🐳 Starting minimal nginx..."
docker compose -f docker/docker-compose.ssl-only.yml up -d nginx-ssl

# Step 4: Test basic connectivity
echo "🧪 Testing basic nginx..."
sleep 5
if curl -f http://$DOMAIN/health > /dev/null 2>&1; then
    echo "✅ Basic nginx working!"
else
    echo "❌ Basic nginx failed. Check firewall settings."
    echo "Make sure you've configured Mi Nube firewall for port 80!"
    exit 1
fi

# Step 5: Generate certificate
echo "🔐 Generating SSL certificate..."
docker compose -f docker/docker-compose.ssl-only.yml run --rm certbot

# Step 6: Verify certificate was created
echo "🔍 Checking if certificates exist..."
if docker compose -f docker/docker-compose.ssl-only.yml exec nginx-ssl test -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem"; then
    echo "✅ SSL certificates generated successfully!"

    # Copy certificates to main docker-compose volumes (if they exist)
    echo "📋 Certificate files created:"
    docker compose -f docker/docker-compose.ssl-only.yml exec nginx-ssl ls -la /etc/letsencrypt/live/$DOMAIN/

else
    echo "❌ Certificate generation failed."
    echo "Check the logs above for details."
    exit 1
fi

# Step 7: Cleanup
echo "🧹 Cleaning up minimal setup..."
docker compose -f docker/docker-compose.ssl-only.yml down

echo ""
echo "🎉 SSL certificates generated!"
echo "📁 Certificates are stored in Docker volume 'certbot_conf'"
echo ""
echo "Now you can:"
echo "1. Update your main nginx config to use HTTPS"
echo "2. Start your full application with docker-compose.yml"
echo "3. The certificates will be available in the shared volume"
echo ""
echo "Certificate files location in volume:"
echo "  - /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
echo "  - /etc/letsencrypt/live/$DOMAIN/privkey.pem"
