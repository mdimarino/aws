#!/bin/bash

    HOST=@@@@@
    DOMAIN=#####

    yum-config-manager --enable epel
    yum update -y
    yum install htop iotop mail -y

    hostname $HOST
    sed -i "s/HOSTNAME=localhost.localdomain/HOSTNAME=${HOST}.${DOMAIN}/g" /etc/sysconfig/network

    rm -f /etc/localtime
    cp /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime

    #rpm -Uvh https://yum.newrelic.com/pub/newrelic/el5/x86_64/newrelic-repo-5-3.noarch.rpm
    #yum install newrelic-sysmond -y
    #nrsysmond-config --set license_key=

    echo 1 > /proc/sys/net/ipv4/ip_forward
    echo 0 > /proc/sys/net/ipv4/conf/eth0/send_redirects
    /sbin/iptables -t nat -A POSTROUTING -o eth0 -s 0.0.0.0/0 -j MASQUERADE

    echo '' >> /etc/rc.local
    echo 'echo 1 > /proc/sys/net/ipv4/ip_forward' >> /etc/rc.local
    echo 'echo 0 > /proc/sys/net/ipv4/conf/eth0/send_redirects' >> /etc/rc.local
    echo '/sbin/iptables -t nat -A POSTROUTING -o eth0 -s 0.0.0.0/0 -j MASQUERADE' >> /etc/rc.local
