#!/usr/bin/env bash
# source config
source ./.env

sudo mkdir -p www/html
cd www/html/
sudo chmod -R 777 .

# sudo with root permissions
sudo su

# update softwave
apt-get update

# install apache2 system
#apt-get -y install apache2

# install nginx system
apt-get -y install nginx

# install php
apt-get -y update
add-apt-repository ppa:ondrej/php
# install php with nginx
apt-get install -y php7.1 php7.1-fpm php7.1-cli php7.1-common php7.1-gd php7.1-mysql php7.1-mcrypt php7.1-curl php7.1-intl php7.1-xsl php7.1-mbstring php7.1-zip php7.1-bcmath php7.1-iconv php7.1-soap

# install php with apache2
#apt-get install php7.1 libapache2-mod-php7.1 libapache2-mod-php7.1 php7.1-common php7.1-mbstring php7.1-xmlrpc php7.1-soap php7.1-gd php7.1-xml php7.1-intl php7.1-mysql php7.1-cli php7.1-mcrypt php7.1-ldap php7.1-zip php7.1-curl php7.1-bcmath

# down version php
#sudo a2dismod php7.1
#sudo a2enmod php7.2

# To remove any trace of mariadb installed through apt-get:

##service mysql stop
#apt-get --purge remove "mysql*"
#apt-get purge mariadb-*
#rm -rf /etc/mysql/
##and it is all gone. Including databases and any configuration file.
##to check if anything named mysql is gone do a
#sudo updatedb
##and a
#locate mysql

# Install MariaDB 10.2
apt-get install software-properties-common
apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xF1656F24C74CD1D8
add-apt-repository 'deb [arch=amd64] http://mariadb.biz.net.id/repo/10.2/ubuntu bionic main'

# Update packages and install MariaDB.
apt-get -y dist-upgrade
apt install mariadb-server

# Setup MariaDB using the mysql_secure_installation built-in shell script
mysql_secure_installation

# Set MariaDB to start on system boot and initialize the daemon.
systemctl enable mysql
systemctl start mysql

# Create Magento Database
mysql -u root -p
create database magento;
create user magento identified by 'magento123@#';
grant all privileges on magento.* to magento@localhost identified by 'magento123@#';
flush privileges;
exit;

# Create folder
cd /var/www/html/
chmod -R 777 ./

# download source and un tar package
wget https://github.com/magento/magento2/archive/2.2.6.tar.gz
wget https://github.com/magento/magento2-sample-data/archive/2.2.6.tar.gz
tar -xzvf 2.2.6.tar.gz
tar -xzvf 2.2.6.tar.gz.1
mv -v magento2-2.2.6/* ./
mv -v magento2-2.2.6/.* ./
cp -avr magento2-sample-data-2.2.6/* ./
rm -rf magento2-2.2.6/ magento2-sample-data-2.2.6/ 2.2.6.tar.gz 2.2.6.tar.gz.1

# create symbolic links between the files you just cloned so sample data works properly
php -f dev/tools/build-sample-data.php -- --ce-source="/var/www/html"

# Change or modify the directory permission to fit Apache2 configuration.
find var generated vendor pub/static pub/media app/etc -type f -exec chmod g+w {} +
find var generated vendor pub/static pub/media app/etc -type d -exec chmod g+ws {} +
chown -R ubuntu:www-data .
chmod u+x bin/magento

# Install PHP Composer
apt-get install -y composer

# Install Magento components using the PHP composer
composer install -v

# Install Magento components using the PHP composer. Ignore platform request when not compatible with PHP
#composer install --ignore-platform-reqs

# install Magento from the command line
php bin/magento setup:install \
 --base-url=http://localhost/magentogitsource/\
 --db-host=localhost \
 --db-name=magento \
 --db-user=magento \
 --db-password=magento123@# \
 --backend-frontname=admin \
 --admin-firstname=Magento \
 --admin-lastname=Admin \
 --admin-email=user@example.com \
 --admin-user=admin \
 --admin-password=admin123 \
 --language=en_US \
 --currency=USD \
 --timezone=America/Chicago \
 --use-rewrites=1

# upgrade the sample data packages
php bin/magento setup:upgrade

# Disable nginx
systemctl disable nginx.service
systemctl stop nginx.service

echo " upstream fastcgi_backend {
     server unix:/run/php/php7.1-fpm.sock;
 }

 server {

     listen 80;
     set \$MAGE_ROOT /var/www/html;
     include /var/www/html/nginx.conf.sample;
 }" > /etc/nginx/sites-available/magento

# Creating a symlink to it in the /etc/nginx/sites-enabled directory
ln -s /etc/nginx/sites-available/magento /etc/nginx/sites-enabled

# remove nginx default
rm -f /etc/nginx/sites-enabled/default

# restart nginx
systemctl restart nginx.service

#scp -i posprofessionaldemo.pem /home/vuvanphan/Downloads/package_pro.zip ubuntu@3.80.131.92:/var/www/html
#apt-get install -y unzip
#unzip package.zip
#mv -v pwapos-omc-2.0-1.1.0/* .
#rm -rf pwapos-omc-2.0-1.1.0/ package_stan.zip

#php bin/magento setup:upgrade
#php bin/magento setup:di:compile
#php bin/magento setup:static-content:deploy -f
#php bin/magento indexer:reindex
#php bin/magento webpos:deploy
#php bin/magento cache:flush