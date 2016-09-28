#!/bin/bash

### Criar partição de SWAP ###

echo "n
e
1


n
l


t
5
82
w
" | fdisk /dev/xvdb

### Formatar e habilitar partição de SWAP ###

mkswap /dev/xvdb5
swapon /dev/xvdb5

echo "/dev/xvdb5  swap        swap    defaults        0   0" >> /etc/fstab

### Alterar hostname ###

hostnamectl set-hostname ubuntu.vpc-zoom-01
