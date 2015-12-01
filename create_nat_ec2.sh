#!/bin/bash

echo; echo =================================================================================; echo

    echo "Carregando variáveis de ambiente"

    # Recebe como argumento o arquivo de variáveis de ambiente
    . ./$1

    image_id=ami-60b6c60a

    key_name=producao-infra

    instance_type=t2.micro

    private_ip_address_NAT1=${cidr}.0.254
    private_ip_address_NAT3=${cidr}.2.254
    private_ip_address_NAT5=${cidr}.4.254
    private_ip_address_NAT7=${cidr}.6.254

echo; echo =================================================================================; echo

    for i in nat1 nat3 nat5 nat7; do
      echo "Gerando arquivo ${i}-user-data.sh"
      sed "s/HOST=@@@@@/HOST=${i}/g" nat-user-data-template.sh > ${i}-user-data.sh
      sed -i "s/DOMAIN=#####/DOMAIN=${vpc_name}/g" ${i}-user-data.sh
    done

echo; echo =================================================================================; echo

    echo "Criando instância NAT1"
    ec2_InstanceId_NAT1=$(aws --profile ${profile} ec2 run-instances \
    --image-id ${image_id} \
    --key-name ${key_name} \
    --security-group-ids ${security_group_NAT1} \
    --monitoring Enabled=true \
    --instance-type ${instance_type} \
    --subnet-id ${subnetid_1} \
    --private-ip-address ${private_ip_address_NAT1} \
    --associate-public-ip-address --user-data file://nat1-user-data.sh \
    --output text \
    --query 'Instances[*].InstanceId')

    echo -n "Aguardando instância NAT1 estar no estado 'running'"
    while state=$(aws --profile ${profile} ec2 describe-instances --instance-ids ${ec2_InstanceId_NAT1} --output text --query 'Reservations[*].Instances[*].State.Name'); test "${state}" = "pending"; do
        sleep 1; echo -n '.'
    done; echo " ${state}"

    echo "Alterando Tag Name da instância NAT1 para 'nat1.${vpc_name}'"
    aws --profile ${profile} ec2 create-tags \
    --resources ${ec2_InstanceId_NAT1} \
    --tags Key=Name,Value="nat1.${vpc_name}"

    echo "Alterando parâmetro source-dest-check para no"
    aws --profile ${profile} ec2 modify-instance-attribute \
    --instance-id ${ec2_InstanceId_NAT1} \
    --no-source-dest-check

    echo "Adicionando a instância NAT1 na tabela de roteamento privada para destinos 0.0.0.0/0"
    aws --profile ${profile} ec2 create-route \
    --route-table-id ${private1_routetable_id} \
    --destination-cidr-block 0.0.0.0/0 \
    --instance-id ${ec2_InstanceId_NAT1}

    ##echo "Parando a instância"
    ##aws --profile ${profile} ec2 stop-instances --instance-ids ${ec2_InstanceId_NAT1}

echo; echo =================================================================================; echo

    echo "Criando instância NAT3"
    ec2_InstanceId_NAT3=$(aws --profile ${profile} ec2 run-instances \
    --image-id ${image_id} \
    --key-name ${key_name} \
    --security-group-ids ${security_group_NAT3} \
    --monitoring Enabled=true \
    --instance-type ${instance_type} \
    --subnet-id ${subnetid_3} \
    --private-ip-address ${private_ip_address_NAT3} \
    --associate-public-ip-address \
    --user-data file://nat3-user-data.sh \
    --output text \
    --query 'Instances[*].InstanceId')

    echo -n "Aguardando instância NAT3 estar no estado 'running'"
    while state=$(aws --profile ${profile} ec2 describe-instances --instance-ids ${ec2_InstanceId_NAT3} --output text --query 'Reservations[*].Instances[*].State.Name'); test "${state}" = "pending"; do
        sleep 1; echo -n '.'
    done; echo " ${state}"

    echo "Alterando Tag Name da instância NAT3 para 'nat3.${vpc_name}'"
    aws --profile ${profile} ec2 create-tags \
    --resources ${ec2_InstanceId_NAT3} \
    --tags Key=Name,Value="nat3.${vpc_name}"

    echo "Alterando parâmetro source-dest-check para no"
    aws --profile ${profile} ec2 modify-instance-attribute \
    --instance-id ${ec2_InstanceId_NAT3} \
    --no-source-dest-check

    echo "Adicionando a instância NAT3 na tabela de roteamento privada para destinos 0.0.0.0/0"
    aws --profile ${profile} ec2 create-route \
    --route-table-id ${private2_routetable_id} \
    --destination-cidr-block 0.0.0.0/0 \
    --instance-id ${ec2_InstanceId_NAT3}

    ##echo "Parando a instância"
    ##aws --profile ${profile} ec2 stop-instances --instance-ids ${ec2_InstanceId_NAT3}

echo; echo =================================================================================; echo

    echo "Criando instância NAT5"
    ec2_InstanceId_NAT5=$(aws --profile ${profile} ec2 run-instances \
    --image-id ${image_id} \
    --key-name ${key_name} \
    --security-group-ids ${security_group_NAT5} \
    --monitoring Enabled=true \
    --instance-type ${instance_type} \
    --subnet-id ${subnetid_5} \
    --private-ip-address ${private_ip_address_NAT5} \
    --associate-public-ip-address \
    --user-data file://nat5-user-data.sh \
    --output text \
    --query 'Instances[*].InstanceId')

    echo -n "Aguardando instância NAT5 estar no estado 'running'"
    while state=$(aws --profile ${profile} ec2 describe-instances --instance-ids ${ec2_InstanceId_NAT5} --output text --query 'Reservations[*].Instances[*].State.Name'); test "${state}" = "pending"; do
        sleep 1; echo -n '.'
    done; echo " ${state}"

    echo "Alterando Tag Name da instância NAT5 para 'nat5.${vpc_name}'"
    aws --profile ${profile} ec2 create-tags \
    --resources ${ec2_InstanceId_NAT5} \
    --tags Key=Name,Value="nat5.${vpc_name}"

    echo "Alterando parâmetro source-dest-check para no"
    aws --profile ${profile} ec2 modify-instance-attribute \
    --instance-id ${ec2_InstanceId_NAT5} \
    --no-source-dest-check

    echo "Adicionando a instância NAT5 na tabela de roteamento privada para destinos 0.0.0.0/0"
    aws --profile ${profile} ec2 create-route \
    --route-table-id ${private3_routetable_id} \
    --destination-cidr-block 0.0.0.0/0 \
    --instance-id ${ec2_InstanceId_NAT5}

    ##echo "Parando a instância"
    ##aws --profile ${profile} ec2 stop-instances --instance-ids ${ec2_InstanceId_NAT5}

echo; echo =================================================================================; echo

    echo "Criando instância NAT7"
    ec2_InstanceId_NAT7=$(aws --profile ${profile} ec2 run-instances \
    --image-id ${image_id} \
    --key-name ${key_name} \
    --security-group-ids ${security_group_NAT7} \
    --monitoring Enabled=true \
    --instance-type ${instance_type} \
    --subnet-id ${subnetid_7} \
    --private-ip-address ${private_ip_address_NAT7} \
    --associate-public-ip-address \
    --user-data file://nat7-user-data.sh \
    --output text \
    --query 'Instances[*].InstanceId')

    echo -n "Aguardando instância NAT7 estar no estado 'running'"
    while state=$(aws --profile ${profile} ec2 describe-instances --instance-ids ${ec2_InstanceId_NAT7} --output text --query 'Reservations[*].Instances[*].State.Name'); test "${state}" = "pending"; do
        sleep 1; echo -n '.'
    done; echo " ${state}"

    echo "Alterando Tag Name da instância NAT7 para 'nat7.${vpc_name}'"
    aws --profile ${profile} ec2 create-tags \
    --resources ${ec2_InstanceId_NAT7} \
    --tags Key=Name,Value="nat7.${vpc_name}"

    echo "Alterando parâmetro source-dest-check para no"
    aws --profile ${profile} ec2 modify-instance-attribute \
    --instance-id ${ec2_InstanceId_NAT7} \
    --no-source-dest-check

    echo "Adicionando a instância NAT7 na tabela de roteamento privada para destinos 0.0.0.0/0"
    aws --profile ${profile} ec2 create-route \
    --route-table-id ${private4_routetable_id} \
    --destination-cidr-block 0.0.0.0/0 \
    --instance-id ${ec2_InstanceId_NAT7}

    ##echo "Parando a instância"
    ##aws --profile ${profile} ec2 stop-instances --instance-ids ${ec2_InstanceId_NAT5}

echo; echo =================================================================================; echo
