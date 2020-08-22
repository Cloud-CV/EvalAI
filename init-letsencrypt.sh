#!/bin/bash

read -p "Skip reading variable (not for first time usage)? (y/N) " skip_input
  if [ "$skip_input" != "Y" ] && [ "$skip_input" != "y" ]; then
    touch .env

    read -p "Enter AWS Access key ID : " AWS_ACCESS_KEY_ID
    echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" > .env

    read -p "Enter AWS Account ID : " AWS_ACCOUNT_ID
    echo "AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID" >> .env

    read -p "Enter AWS Default Region (eg: us-east-1) : " AWS_DEFAULT_REGION
    echo "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION" >> .env

    read -p "Enter AWS secret access key : " AWS_SECRET_ACCESS_KEY
    echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >> .env

    read -p "Enter Hostname : " HOSTNAME
    echo "HOSTNAME=$HOSTNAME" >> .env

    read -p "Enter RDS Hostname : " RDS_HOSTNAME
    echo "RDS_HOSTNAME=$RDS_HOSTNAME" >> .env

    read -p "Enter RDS DB Name : " RDS_DB_NAME
    echo "RDS_DB_NAME=$RDS_DB_NAME" >> .env

    read -p "Enter RDS Username : " RDS_USERNAME
    echo "RDS_USERNAME=$RDS_USERNAME" >> .env

    read -p "Enter RDS Password : " RDS_PASSWORD
    echo "RDS_PASSWORD=$RDS_PASSWORD" >> .env

    read -p "Enter Sentry DSN URL : " SENTRY_URL
    echo "SENTRY_URL=$SENTRY_URL" >> .env

    read -p "Enter AWS S3 Bucket Name: " AWS_STORAGE_BUCKET_NAME
    echo "AWS_STORAGE_BUCKET_NAME=$AWS_STORAGE_BUCKET_NAME" >> .env

    read -p "Enter your domain name (example.com) : " DOMAIN_NAME
    echo "DOMAIN_NAME=$DOMAIN_NAME" >> .env

  fi

read -p "Enter your domain name (example.com) : " DOMAIN_NAME

domains=($DOMAIN_NAME evalai.$DOMAIN_NAME evalapi.$DOMAIN_NAME)

rsa_key_size=4096
data_path="./certbot"

# Adding a valid address is strongly recommended
read -p "Enter your Email ID : " email

staging=1 # Set to 1 if you're testing your setup to avoid hitting request limits

if [ -d "$data_path" ]; then
  read -p "Existing data found for $domains. Continue and replace existing certificate? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi


if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  mkdir -p "$data_path/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
fi

echo "### Creating dummy certificate for $domains ..."
path="/etc/letsencrypt/live/$domains"
mkdir -p "$data_path/conf/live/$domains"
sudo docker-compose -f docker-compose-vm.yml run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:1024 -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot


echo "### Starting nginx ..."
sudo docker-compose -f docker-compose-vm.yml up --force-recreate -d nodejs

echo "### Deleting dummy certificate for $domains ..."
sudo docker-compose -f docker-compose-vm.yml run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$domains && \
  rm -Rf /etc/letsencrypt/archive/$domains && \
  rm -Rf /etc/letsencrypt/renewal/$domains.conf" certbot


echo "### Requesting Lets Encrypt certificate for $domains ..."
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Select appropriate email arg
case "$email" in
  "") email_arg="--register-unsafely-without-email" ;;
  *) email_arg="--email $email" ;;
esac

# Enable staging mode if needed
if [ $staging != "0" ]; then staging_arg="--staging"; fi

sudo docker-compose -f docker-compose-vm.yml run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $email_arg \
    $domain_args \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot

echo "### Reloading nginx ..."
sudo docker-compose -f docker-compose-vm.yml exec nodejs nginx -s reload