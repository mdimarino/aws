#!/bin/bash

echo; echo =================================================================================; echo

    echo "Carregando variáveis de ambiente"
    . ./vars.sh

    ubuntu_image=ami-9a562df2

    key_name=producao

    private_ip_address_NAT1=10.50.0.254

echo; echo =================================================================================; echo

    echo "Criando instância NAT1"
    ec2_InstanceId_NAT1=$(aws ec2 run-instances --image-id $ubuntu_image --key-name $key_name --security-group-ids $security_group_NAT1 --instance-type t2.micro --subnet-id $subnetid_0 --private-ip-address $private_ip_address_NAT1 --associate-public-ip-address --user-data file://user-data.sh --output text --query 'Instances[*].InstanceId')

    echo -n "Aguardando instância NAT1 estar no estado 'running'"
    while state=$(aws ec2 describe-instances --instance-ids $ec2_InstanceId_NAT1 --output text --query 'Reservations[*].Instances[*].State.Name'); test "$state" = "pending"; do
        sleep 1; echo -n '.'
    done; echo " $state"

    echo "Alterando Tag Name do instância NAT1 para 'prod_NAT1'"
    aws ec2 create-tags --resources $ec2_InstanceId_NAT1 --tags Key=Name,Value="prod-NAT1"

    echo "Alterando parâmetro source-dest-check para no"
    aws ec2 modify-instance-attribute --instance-id $ec2_InstanceId_NAT1 --no-source-dest-check

    echo "Adicionando a instância NAT1 na tabela de roteamento privada para destinos 0.0.0.0/0"
    aws ec2 create-route --route-table-id $private_routetableid --destination-cidr-block 0.0.0.0/0 --instance-id $ec2_InstanceId_NAT1

    echo "Parando a instância"
    aws ec2 stop-instances --instance-ids $ec2_InstanceId_NAT1

echo; echo =================================================================================; echo
