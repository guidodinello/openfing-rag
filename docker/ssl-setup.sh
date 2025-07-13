#!/bin/bash

# 🔐 SSL Setup Script para OpenFing RAG
# Este script configura HTTPS con Let's Encrypt en tu VPS

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Configurando SSL para OpenFing RAG${NC}"

DOMAIN="openfingchat.duckdns.org" # Cambiar por tu dominio real
EMAIL="guido.dinello+openfing-chat@gmail.com"

echo -e "${YELLOW}📋 Verificando configuración...${NC}"
echo "Dominio: $DOMAIN"
echo "Email: $EMAIL"

read -p "¿Es correcta esta información? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Por favor edita el script con tu dominio y email correctos${NC}"
    exit 1
fi

# 1. Verificar que el dominio apunte a esta VPS
echo -e "${YELLOW}🌐 Verificando DNS...${NC}"
CURRENT_IP=$(curl -s http://checkip.amazonaws.com)
DOMAIN_IP=$(dig +short $DOMAIN)

if [ "$CURRENT_IP" != "$DOMAIN_IP" ]; then
    echo -e "${RED}⚠️  ADVERTENCIA: El dominio $DOMAIN no apunta a esta VPS ($CURRENT_IP)${NC}"
    echo "IP del dominio: $DOMAIN_IP"
    echo "IP de esta VPS: $CURRENT_IP"
    echo "Asegúrate de que tu DNS esté configurado correctamente antes de continuar."
    read -p "¿Continuar de todas formas? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 2. Crear directorios necesarios
echo -e "${YELLOW}📁 Creando estructura de directorios...${NC}"
mkdir -p nginx/conf.d
mkdir -p ssl

# 3. Actualizar configuración de nginx con el dominio correcto
echo -e "${YELLOW}📝 Actualizando configuración de nginx...${NC}"
sed -i "s/DOMINIO_PLACEHOLDER/$DOMAIN/g" nginx/conf.d/default.conf

# 4. Actualizar docker-compose con el dominio y email correctos
echo -e "${YELLOW}🐳 Actualizando docker-compose...${NC}"
sed -i "s/EMAIL_PLACEHOLDER/$EMAIL/g" docker-compose.yml
sed -i "s/DOMINIO_PLACEHOLDER/$DOMAIN/g" docker-compose.yml

# 5. Iniciar nginx solo para obtener certificados
echo -e "${YELLOW}🚀 Iniciando nginx para obtener certificados...${NC}"
docker compose up -d nginx
echo -e "${YELLOW}⏳ Esperando a que nginx esté listo...${NC}"
sleep 10

# 7. Obtener certificados SSL iniciales
echo -e "${YELLOW}🔐 Obteniendo certificados SSL de Let's Encrypt...${NC}"
docker compose -f docker-compose.production.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --staging \
    -d $DOMAIN

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Certificados de staging obtenidos exitosamente${NC}"

    # Ahora obtener certificados reales
    echo -e "${YELLOW}🔐 Obteniendo certificados reales...${NC}"
    docker compose --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d $DOMAIN

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Certificados SSL reales obtenidos exitosamente${NC}"
    else
        echo -e "${RED}❌ Error obteniendo certificados reales${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Error obteniendo certificados de staging${NC}"
    exit 1
fi

# 8. Recargar nginx con configuración SSL
echo -e "${YELLOW}🔄 Recargando nginx con configuración SSL...${NC}"
docker compose exec nginx nginx -s reload

# 9. Iniciar todos los servicios
echo -e "${YELLOW}🚀 Iniciando todos los servicios...${NC}"
docker compose up -d

# 10. Verificar que todo está funcionando
echo -e "${YELLOW}🔍 Verificando configuración...${NC}"
sleep 15

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/health)
if [ "$HTTP_STATUS" = "301" ]; then
    echo -e "${GREEN}✅ Redirección HTTP → HTTPS funcionando${NC}"
else
    echo -e "${YELLOW}⚠️  Redirección HTTP devolvió código: $HTTP_STATUS${NC}"
fi

HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health)
if [ "$HTTPS_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ HTTPS funcionando correctamente${NC}"
else
    echo -e "${RED}❌ HTTPS devolvió código: $HTTPS_STATUS${NC}"
fi

# 11. Mostrar información final
echo -e "\n${GREEN}🎉 ¡Configuración SSL completada!${NC}\n"
echo -e "🌐 Tu API está disponible en: ${GREEN}https://$DOMAIN/api/v1/${NC}"
echo -e "📚 Documentación en: ${GREEN}https://$DOMAIN/docs${NC}"
echo -e "🏥 Health check: ${GREEN}https://$DOMAIN/health${NC}"
echo -e "\n${YELLOW}📝 Próximos pasos:${NC}"
echo "1. Verificar que tu aplicación funciona correctamente"
echo "2. Configurar firewall si es necesario"
echo "3. Los certificados se renovarán automáticamente cada 12 horas"

echo -e "\n${YELLOW}🔧 Comandos útiles:${NC}"
echo "Ver logs: docker compose logs -f"
echo "Renovar certificados manualmente: docker compose run --rm certbot renew"
echo "Verificar certificados: openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"

echo -e "\n${GREEN}✨ ¡Listo! Tu sistema RAG ahora está funcionando con HTTPS${NC}"
