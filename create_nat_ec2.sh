#!/bin/bash

echo; echo =================================================================================; echo

    echo "Carregando variáveis de ambiente"

    . ./$1

    image_id=ami-9a562df2

    key_name=producao

    instance_type=t2.micro

    private_ip_address_NAT1=${cidr}.0.254
    private_ip_address_NAT3=${cidr}.2.254
    private_ip_address_NAT5=${cidr}.4.254
    private_ip_address_NAT7=${cidr}.6.254

echo; echo =================================================================================; echo

    echo "Criando instância NAT1"
    ec2_InstanceId_NAT1=$(aws ec2 run-instances --image-id ${image_id} --key-name ${key_name} --security-group-ids ${security_group_NAT1} --instance-type ${instance_type} --subnet-id ${subnetid_1} --private-ip-address ${private_ip_address_NAT1} --associate-public-ip-address --user-data file://user-data.sh --output text --query 'Instances[*].InstanceId')

    echo -n "Aguardando instância NAT1 estar no estado 'running'"
    while state=$(aws ec2 describe-instances --instance-ids ${ec2_InstanceId_NAT1} --output text --query 'Reservations[*].Instances[*].State.Name'); test "${state}" = "pending"; do
        sleep 1; echo -n '.'
    done; echo " ${state}"

    echo "Alterando Tag Name do instância NAT1 para 'prod-NAT1'"
    aws ec2 create-tags --resources ${ec2_InstanceId_NAT1} --tags Key=Name,Value="prod-NAT1"

    echo "Alterando parâmetro source-dest-check para no"
    aws ec2 modify-instance-attribute --instance-id ${ec2_InstanceId_NAT1} --no-source-dest-check

    echo "Adicionando a instância NAT1 na tabela de roteamento privada para destinos 0.0.0.0/0"
    aws ec2 create-route --route-table-id ${private_routetable_id} --destination-cidr-block 0.0.0.0/0 --instance-id ${ec2_InstanceId_NAT1}

    echo "Parando a instância"
    aws ec2 stop-instances --instance-ids ${ec2_InstanceId_NAT1}

echo; echo =================================================================================; echo

    echo "Criando instância NAT3"
    ec2_InstanceId_NAT3=$(aws ec2 run-instances --image-id ${image_id} --key-name ${key_name} --security-group-ids ${security_group_NAT3} --instance-type ${instance_type} --subnet-id ${subnetid_3} --private-ip-address ${private_ip_address_NAT3} --associate-public-ip-address --user-data file://user-data.sh --output text --query 'Instances[*].InstanceId')

    echo -n "Aguardando instância NAT3 estar no estado 'running'"
    while state=$(aws ec2 describe-instances --instance-ids ${ec2_InstanceId_NAT3} --output text --query 'Reservations[*].Instances[*].State.Name'); test "${state}" = "pending"; do
        sleep 1; echo -n '.'
    done; echo " ${state}"

    echo "Alterando Tag Name do instância NAT3 para 'prod-NAT3'"
    aws ec2 create-tags --resources ${ec2_InstanceId_NAT3} --tags Key=Name,Value="prod-NAT3"

    echo "Alterando parâmetro source-dest-check para no"
    aws ec2 modify-instance-attribute --instance-id ${ec2_InstanceId_NAT3} --no-source-dest-check

    echo "Adicionando a instância NAT3 na tabela de roteamento privada para destinos 0.0.0.0/0"
    aws ec2 create-route --route-table-id ${private_routetable_id} --destination-cidr-block 0.0.0.0/0 --instance-id ${ec2_InstanceId_NAT3}

    ##echo "Parando a instância"
    ##aws ec2 stop-instances --instance-ids ${ec2_InstanceId_NAT3}

echo; echo =================================================================================; echo

    echo "Criando instância NAT5"
    ec2_InstanceId_NAT5=$(aws ec2 run-instances --image-id ${image_id} --key-name ${key_name} --security-group-ids ${security_group_NAT5} --instance-type ${instance_type} --subnet-id ${subnetid_5} --private-ip-address ${private_ip_address_NAT5} --associate-public-ip-address --user-data file://user-data.sh --output text --query 'Instances[*].InstanceId')

    echo -n "Aguardando instância NAT5 estar no estado 'running'"
    while state=$(aws ec2 describe-instances --instance-ids ${ec2_InstanceId_NAT5} --output text --query 'Reservations[*].Instances[*].State.Name'); test "${state}" = "pending"; do
        sleep 1; echo -n '.'
    done; echo " ${state}"

    echo "Alterando Tag Name do instância NAT5 para 'prod-NAT5'"
    aws ec2 create-tags --resources ${ec2_InstanceId_NAT5} --tags Key=Name,Value="prod-NAT5"

    echo "Alterando parâmetro source-dest-check para no"
    aws ec2 modify-instance-attribute --instance-id ${ec2_InstanceId_NAT5} --no-source-dest-check

    echo "Adicionando a instância NAT5 na tabela de roteamento privada para destinos 0.0.0.0/0"
    aws ec2 create-route --route-table-id ${private_routetable_id} --destination-cidr-block 0.0.0.0/0 --instance-id ${ec2_InstanceId_NAT5}

    ##echo "Parando a instância"
    ##aws ec2 stop-instances --instance-ids ${ec2_InstanceId_NAT5}

echo; echo =================================================================================; echo

    echo "Criando instância NAT7"
    ec2_InstanceId_NAT7=$(aws ec2 run-instances --image-id ${image_id} --key-name ${key_name} --security-group-ids ${security_group_NAT7} --instance-type ${instance_type} --subnet-id ${subnetid_7} --private-ip-address ${private_ip_address_NAT7} --associate-public-ip-address --user-data file://user-data.sh --output text --query 'Instances[*].InstanceId')

    echo -n "Aguardando instância NAT7 estar no estado 'running'"
    while state=$(aws ec2 describe-instances --instance-ids ${ec2_InstanceId_NAT7} --output text --query 'Reservations[*].Instances[*].State.Name'); test "${state}" = "pending"; do
        sleep 1; echo -n '.'
    done; echo " ${state}"

    echo "Alterando Tag Name do instância NAT5 para 'prod-NAT7'"
    aws ec2 create-tags --resources ${ec2_InstanceId_NAT7} --tags Key=Name,Value="prod-NAT7"

    echo "Alterando parâmetro source-dest-check para no"
    aws ec2 modify-instance-attribute --instance-id ${ec2_InstanceId_NAT7} --no-source-dest-check

    echo "Adicionando a instância NAT7 na tabela de roteamento privada para destinos 0.0.0.0/0"
    aws ec2 create-route --route-table-id ${private_routetable_id} --destination-cidr-block 0.0.0.0/0 --instance-id ${ec2_InstanceId_NAT7}

    ##echo "Parando a instância"
    ##aws ec2 stop-instances --instance-ids ${ec2_InstanceId_NAT5}

echo; echo =================================================================================; echo
