#!/bin/bash -ex
#####################
# https://github.com/ghoulmann/rpi-graphite/blob/master/rpi-graphite.sh
# Installs Graphite
#####################
# Graphite served from :8080
# Default is disabled
# Requires interaction: yes, admin name, password
# check for root
if [[ $EUID -ne 0 ]]; then
    echo "$0 must be run as root." 1>&2
    exit 1
fi

# Install Function - Installs packages from repositories
install ()
{
    apt-get update #always do "sudo apt-get update" before installing from the (always free) software repositories.
    DEBIAN_FRONTEND=noninteractive apt-get -y \
    -o DPkg::Options::=--force-confdef \
    -o DPkg::Options::=--force-confold \
    install $@
}

# pip install function
pips ()
{
    pip install $@
}

install apache2 \
python-pip \
python-cairo \
python-django \
python-django-tagging \
libapache2-mod-wsgi \
libapache2-mod-python \
python-twisted \
python-memcache \
python-pysqlite2 \
python-simplejson \
memcached \
python-cairo-dev \
python-ldap \
erlang-os-mon \
erlang-snmp \
netcat

# rabbitmq-server

# install with pip
pips whisper carbon graphite-web


# apache2 site conf from web
rm -f /etc/apache2/sites-available/graphite
wget https://raw.github.com/tmm1/graphite/master/examples/example-graphite-vhost.conf -O /etc/apache2/sites-available/graphite

# port 8080 instead of 80
sed -i 's|80|8080|' /etc/apache2/sites-available/graphite
echo "Listen 8080" >> /etc/apache2/sites-available/graphite

# mv storage to hard disk
if [ ! -d /mnt/ramdisk/graphite ] ; then 
    mkdir /mnt/ramdisk/graphite
    mv /opt/graphite/storage /mnt/ramdisk/graphite
    ln -s /mnt/ramdisk/graphite/storage /opt/graphite/storage
fi

# copy configuration files
cp graphite/*.{conf,wsgi} /opt/graphite/conf

# because docs say so
mkdir -p /etc/httpd/wsgi/

#Local settings from example
cp graphite/local_settings.py /opt/graphite/webapp/graphite/local_settings.py

# SyncDB - requires interaction
# work around a bug in django
export LC_ALL="en_US.UTF-8"
cd /opt/graphite/webapp/graphite && python manage.py syncdb --noinput
# cd /opt/graphite/webapp/graphite && python manage.py syncdb 

# set permissions
chown www-data:www-data /mnt/ramdisk/graphite
chown -R www-data:www-data /opt/graphite/storage

# enable mod_wsgi
a2enmod wsgi

# enable site
a2ensite graphite

# restart apache2
service apache2 reload

cat <<EOC | crontab
SHELL=/bin/bash
# remove log files from ramdisk
# run 30 minutes after 2 am, every day
30 2 * * *    (sudo find /mnt/ramdisk/graphite/storage/log -name "*.log.*" -exec rm -f {} \; > dev/null)
EOC

echo "setting up graphite init script"
cp carbon-cache.sh /etc/init.d/carbon-cache
chmod 755 /etc/init.d/carbon-cache
chown root:root /etc/init.d/carbon-cache
