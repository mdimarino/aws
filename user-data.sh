#!/bin/bash

    echo 1 > /proc/sys/net/ipv4/ip_forward
    echo 0 > /proc/sys/net/ipv4/conf/eth0/send_redirects
    /sbin/iptables -t nat -A POSTROUTING -o eth0 -s 0.0.0.0/0 -j MASQUERADE

    /bin/sed -i "s/exit 0/echo 1 > \/proc\/sys\/net\/ipv4\/ip_forward\necho 0 > \/proc\/sys\/net\/ipv4\/conf\/eth0\/send_redirects\n\/sbin\/iptables -t nat -A POSTROUTING -o eth0 -s 0.0.0.0\/0 -j MASQUERADE\n\nexit 0/g" /etc/rc.local