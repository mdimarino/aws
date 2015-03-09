#!/bin/bash

    vpcname=vpc-01
    vpcid=vpc-2997d84c
    internetgatewayid=igw-ffc0499a
    public_routetableid=rtb-3ad1885f
    private_routetableid=rtb-0ed1886b
    subnetid_0=subnet-136bcb38
    subnetid_1=subnet-116bcb3a
    subnetid_2=subnet-2b93095c
    subnetid_3=subnet-2993095e
    subnetid_4=subnet-8b8833d2
    subnetid_5=subnet-8f8833d6
    subnetid_6=subnet-987c33a2
    subnetid_7=subnet-997c33a3
    security_group_NAT1=sg-6de16809
    security_group_NAT3=sg-69e1680d
    security_group_NAT5=sg-71e16815
    security_group_NAT7=sg-7de16819

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
    aws ec2 create-tags --resources $ec2_InstanceId_NAT1 --tags Key=Name,Value="prod_NAT1"

    echo "Alterando parâmetro source-dest-check para no"
    aws ec2 modify-instance-attribute --instance-id $ec2_InstanceId_NAT1 --no-source-dest-check

    echo "Adicionando a instância NAT1 na tabela de roteamento privada para destinos 0.0.0.0/0"
    aws ec2 create-route --route-table-id $private_routetableid --destination-cidr-block 0.0.0.0/0 --instance-id $ec2_InstanceId_NAT1

    echo "Parando a instância"
    aws ec2 stop-instances --instance-ids $ec2_InstanceId_NAT1

echo; echo =================================================================================; echo