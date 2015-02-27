#!/bin/bash

vpcname="vpc-02"

# Criar VPC com CIDR 10.50.0.0/16
    echo "Criando VPC $vpcname com CIDR 10.50.0.0/16"
    vpc_id=$(aws ec2 create-vpc --cidr-block 10.50.0.0/16 --output text --query 'Vpc.VpcId')
    echo VpcId=$vpc_id

    echo "Alterando Tag Name"
    aws ec2 create-tags --resources $vpc_id --tags Key=Name,Value=$vpcname

    echo -n "Aguardando pela VPC..."
    while state=$(aws ec2 describe-vpcs --filters Name=tag-key,Values=vpcname --filters Name=tag-value,Values=$vpcname --output text --query 'Vpcs[*].State'); test "$state" = "pending"; do
        echo -n . ; sleep 3;
    done; echo " $state"

# Criar um internet gateway (para permitir acesso a internet)
    echo "Criando um internet gateway"
    igw=$(aws ec2 create-internet-gateway --output text --query 'InternetGateway.InternetGatewayId')
    echo InternetGatewayId=$igw

    echo "Alterando Tag Name"
    aws ec2 create-tags --resources $igw --tags Key=Name,Value="Gateway da Subrede Publica"

# Atachar o internet gateway na vpc
    echo "Atachando o internet gateway na vpc"
    aws ec2 attach-internet-gateway --internet-gateway-id $igw --vpc-id $vpc_id

# Criar tabelas de roteamento para subredes publicas e privadas
    echo "Criando tabela de roteamento para subredes publicas"
    # Quando a vpc é criada uma tabela de roteamento default eh criada automaticamente, vamos usa-la para as subredes publicas
    public_rtb_id=$(aws ec2 describe-route-tables --filters Name=vpc-id,Values=$vpc_id --output text --query 'RouteTables[*].RouteTableId')
    echo RouteTableId=$public_rtb_id

    echo "Alterando Tag Name"
    aws ec2 create-tags --resources $public_rtb_id --tags Key=Name,Value="Tabela de Roteamento Publica"

    echo "Criando tabela de roteamento para subredes privadas"
    private_rtb_id=$(aws ec2 create-route-table --vpc-id $vpc_id --output text --query 'RouteTable.RouteTableId')
    echo RouteTableId=$private_rtb_id

    echo "Alterando Tag Name"
    aws ec2 create-tags --resources $private_rtb_id --tags Key=Name,Value="Tabela de Roteamento Privada"

# Criar rota na tabela de roteamento publica para o internet gateway, ira rotear o trafego para fora desta rede para internet
    echo "Criando rota na tabela de roteamento publica para o internet gateway"
    aws ec2 create-route --route-table-id $public_rtb_id --gateway-id $igw --destination-cidr-block 0.0.0.0/0

# Criar subnets:

# Subrede Publica 01 - 10.50.0.0/24 - zona de disponibilidade us-east-1a
    subnet_id=$(aws ec2 create-subnet --vpc-id $vpc_id --cidr-block 10.50.0.0/24 --availability-zone us-east-1a --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnet_id
    echo "Alterando Tag Name"
    aws ec2 create-tags --resources $subnet_id --tags Key=Name,Value="Subrede Publica 01"
    aws ec2 associate-route-table --subnet-id $subnet_id --route-table-id $public_rtb_id

# Subrede Privada 01 - 10.50.1.0/24 - zona de disponibilidade us-east-1a
    subnet_id=$(aws ec2 create-subnet --vpc-id $vpc_id --cidr-block 10.50.1.0/24 --availability-zone us-east-1a --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnet_id
    echo "Alterando Tag Name"
    aws ec2 create-tags --resources $subnet_id --tags Key=Name,Value="Subrede Privada 01"
    aws ec2 associate-route-table --subnet-id $subnet_id --route-table-id $private_rtb_id

# Subrede Publica 02 - 10.50.2.0/24 - zona de disponibilidade us-east-1b
    subnet_id=$(aws ec2 create-subnet --vpc-id $vpc_id --cidr-block 10.50.2.0/24 --availability-zone us-east-1b --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnet_id
    echo "Alterando Tag Name"
    aws ec2 create-tags --resources $subnet_id --tags Key=Name,Value="Subrede Publica 02"
    aws ec2 associate-route-table --subnet-id $subnet_id --route-table-id $public_rtb_id

# Subrede Privada 02 - 10.50.3.0/24 - zona de disponibilidade us-east-1b
    subnet_id=$(aws ec2 create-subnet --vpc-id $vpc_id --cidr-block 10.50.3.0/24 --availability-zone us-east-1b --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnet_id
    echo "Alterando Tag Name"
    aws ec2 create-tags --resources $subnet_id --tags Key=Name,Value="Subrede Privada 02"
    aws ec2 associate-route-table --subnet-id $subnet_id --route-table-id $private_rtb_id

# Subrede Publica 03 - 10.50.4.0/24 - zona de disponibilidade us-east-1c
    subnet_id=$(aws ec2 create-subnet --vpc-id $vpc_id --cidr-block 10.50.4.0/24 --availability-zone us-east-1c --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnet_id
    echo "Alterando Tag Name"
    aws ec2 create-tags --resources $subnet_id --tags Key=Name,Value="Subrede Publica 03"
    aws ec2 associate-route-table --subnet-id $subnet_id --route-table-id $public_rtb_id

# Subrede Privada 03 - 10.50.5.0/24 - zona de disponibilidade us-east-1c
    subnet_id=$(aws ec2 create-subnet --vpc-id $vpc_id --cidr-block 10.50.5.0/24 --availability-zone us-east-1c --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnet_id
    echo "Alterando Tag Name"
    aws ec2 create-tags --resources $subnet_id --tags Key=Name,Value="Subrede Privada 03"
    aws ec2 associate-route-table --subnet-id $subnet_id --route-table-id $private_rtb_id
