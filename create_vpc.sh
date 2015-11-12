#!/bin/bash

profile=$1
vpcname=$2

echo =================================================================================; echo

# Criar VPC com CIDR 172.31.0.0/16
    echo "Criando VPC $vpcname com CIDR 172.31.0.0/16"
    vpcid=$(aws --profile $profile ec2 create-vpc --cidr-block 172.31.0.0/16 --output text --query 'Vpc.VpcId')
    echo VpcId=$vpcid

    echo "Alterando Tag Name da vpc para '$vpcname'"
    aws --profile $profile ec2 create-tags --resources $vpcid --tags Key=Name,Value=$vpcname

    echo -n "Aguardando pela VPC..."
    while state=$(aws --profile $profile ec2 describe-vpcs --filters Name=tag-key,Values=vpcname --filters Name=tag-value,Values=$vpcname --output text --query 'Vpcs[*].State'); test "$state" = "pending"; do
        echo -n . ; sleep 3;
    done; echo " $state"

echo; echo =================================================================================; echo

# Criar um internet gateway (para permitir acesso a internet)
    echo "Criando um internet gateway"
    internetgatewayid=$(aws --profile $profile ec2 create-internet-gateway --output text --query 'InternetGateway.InternetGatewayId')
    echo InternetGatewayId=$internetgatewayid

    echo "Alterando Tag Name do internet gateway para 'Gateway da Subrede Publica'"
    aws --profile $profile ec2 create-tags --resources $internetgatewayid --tags Key=Name,Value="Gateway da Subrede Publica - $vpcname"

echo; echo =================================================================================; echo

# Atachar o internet gateway na vpc
    echo "Atachando o internet gateway na vpc $vpcname"
    aws --profile $profile ec2 attach-internet-gateway --internet-gateway-id $internetgatewayid --vpc-id $vpcid

echo; echo =================================================================================; echo

# Criar tabelas de roteamento para subredes publicas e privadas
    echo "Criando tabela de roteamento para subredes publicas"
    # Quando a vpc é criada uma tabela de roteamento default eh criada automaticamente, vamos usa-la para as subredes publicas
    public_routetableid=$(aws --profile $profile ec2 describe-route-tables --filters Name=vpc-id,Values=$vpcid --output text --query 'RouteTables[*].RouteTableId')
    echo RouteTableId=$public_routetableid

    echo "Alterando Tag Name da tabela de roteamento para 'Tabela de Roteamento Publica'"
    aws --profile $profile ec2 create-tags --resources $public_routetableid --tags Key=Name,Value="Tabela de Roteamento Publica - $vpcname"

    echo "Criando tabela de roteamento para subredes privadas"
    private_routetableid=$(aws --profile $profile ec2 create-route-table --vpc-id $vpcid --output text --query 'RouteTable.RouteTableId')
    echo RouteTableId=$private_routetableid

    echo "Alterando Tag Name da tabela de roteamento para 'Tabela de Roteamento Privada'"
    aws --profile $profile ec2 create-tags --resources $private_routetableid --tags Key=Name,Value="Tabela de Roteamento Privada - $vpcname"

echo; echo =================================================================================; echo

# Criar rota na tabela de roteamento publica para o internet gateway, ira rotear o trafego para fora desta rede para internet
    echo "Criando rota na tabela de roteamento publica para o internet gateway"
    aws --profile $profile ec2 create-route --route-table-id $public_routetableid --gateway-id $internetgatewayid --destination-cidr-block 0.0.0.0/0

echo; echo =================================================================================; echo

# Criar subnets:

# A AWS tem 5 zonas de disponibilidade em us-east-1: a,b,c,d,e. Somente a,b,c,e podem ser usadas, d fica reservada.

# Subrede Publica 01 - 172.31.0.0/24 - zona de disponibilidade us-east-1a
    echo "Criando subrede publica 01 - 172.31.0.0/24 - us-east-1a"
    subnetid_0=$(aws --profile $profile ec2 create-subnet --vpc-id $vpcid --cidr-block 172.31.0.0/24 --availability-zone us-east-1a --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnetid_0
    echo "Alterando Tag Name da subrede para 'Subrede Publica 01'"
    aws --profile $profile ec2 create-tags --resources $subnetid_0 --tags Key=Name,Value="Subrede Publica 01 - $vpcname"
    echo "Associando tabela de roteamento publica $public_routetableid a subrede $subnetid_0"
    aws --profile $profile ec2 associate-route-table --subnet-id $subnetid_0 --route-table-id $public_routetableid

echo; echo =================================================================================; echo

# Subrede Privada 01 - 172.31.1.0/24 - zona de disponibilidade us-east-1a
    echo "Criando subrede privada 01 - 172.31.1.0/24 - us-east-1a"
    subnetid_1=$(aws --profile $profile ec2 create-subnet --vpc-id $vpcid --cidr-block 172.31.1.0/24 --availability-zone us-east-1a --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnetid_1
    echo "Alterando Tag Name da subrede para 'Subrede Privada 01'"
    aws --profile $profile ec2 create-tags --resources $subnetid_1 --tags Key=Name,Value="Subrede Privada 01 - $vpcname"
    echo "Associando tabela de roteamento privada $private_routetableid a subrede $subnetid_1"
    aws --profile $profile ec2 associate-route-table --subnet-id $subnetid_1 --route-table-id $private_routetableid

echo; echo =================================================================================; echo

# Subrede Publica 02 - 172.31.2.0/24 - zona de disponibilidade us-east-1b
    echo "Criando subrede publica 02 - 172.31.2.0/24 - us-east-1b"
    subnetid_2=$(aws --profile $profile ec2 create-subnet --vpc-id $vpcid --cidr-block 172.31.2.0/24 --availability-zone us-east-1b --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnetid_2
    echo "Alterando Tag Name da subrede para 'Subrede Publica 02'"
    aws --profile $profile ec2 create-tags --resources $subnetid_2 --tags Key=Name,Value="Subrede Publica 02 - $vpcname"
    echo "Associando tabela de roteamento publica $public_routetableid a subrede $subnetid_2"
    aws --profile $profile ec2 associate-route-table --subnet-id $subnetid_2 --route-table-id $public_routetableid

echo; echo =================================================================================; echo

# Subrede Privada 02 - 172.31.3.0/24 - zona de disponibilidade us-east-1b
    echo "Criando subrede privada 02 - 172.31.3.0/24 - us-east-1b"
    subnetid_3=$(aws --profile $profile ec2 create-subnet --vpc-id $vpcid --cidr-block 172.31.3.0/24 --availability-zone us-east-1b --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnetid_3
    echo "Alterando Tag Name da subrede para 'Subrede Privada 02'"
    aws --profile $profile ec2 create-tags --resources $subnetid_3 --tags Key=Name,Value="Subrede Privada 02"
    echo "Associando tabela de roteamento privada $private_routetableid a subrede $subnetid_3"
    aws --profile $profile ec2 associate-route-table --subnet-id $subnetid_3 --route-table-id $private_routetableid

echo; echo =================================================================================; echo

# Subrede Publica 03 - 172.31.4.0/24 - zona de disponibilidade us-east-1c
    echo "Criando subrede publica 03 - 172.31.4.0/24 - us-east-1c"
    subnetid_4=$(aws --profile $profile ec2 create-subnet --vpc-id $vpcid --cidr-block 172.31.4.0/24 --availability-zone us-east-1c --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnetid_4
    echo "Alterando Tag Name da subrede para 'Subrede Publica 03'"
    aws --profile $profile ec2 create-tags --resources $subnetid_4 --tags Key=Name,Value="Subrede Publica 03 - $vpcname"
    echo "Associando tabela de roteamento publica $public_routetableid a subrede $subnetid_4"
    aws --profile $profile ec2 associate-route-table --subnet-id $subnetid_4 --route-table-id $public_routetableid

echo; echo =================================================================================; echo

# Subrede Privada 03 - 172.31.5.0/24 - zona de disponibilidade us-east-1c
    echo "Criando subrede privada 03 - 172.31.5.0/24 - us-east-1c"
    subnetid_5=$(aws --profile $profile ec2 create-subnet --vpc-id $vpcid --cidr-block 172.31.5.0/24 --availability-zone us-east-1c --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnetid_5
    echo "Alterando Tag Name da subrede para 'Subrede Privada 03'"
    aws --profile $profile ec2 create-tags --resources $subnetid_5 --tags Key=Name,Value="Subrede Privada 03 - $vpcname"
    echo "Associando tabela de roteamento privada $private_routetableid a subrede $subnetid_5"
    aws --profile $profile ec2 associate-route-table --subnet-id $subnetid_5 --route-table-id $private_routetableid

echo; echo =================================================================================; echo

# Subrede Publica 04 - 172.31.6.0/24 - zona de disponibilidade us-east-1e
    echo "Criando subrede publica 04 - 172.31.6.0/24 - us-east-1e"
    subnetid_6=$(aws --profile $profile ec2 create-subnet --vpc-id $vpcid --cidr-block 172.31.6.0/24 --availability-zone us-east-1e --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnetid_6
    echo "Alterando Tag Name da subrede para 'Subrede Publica 04'"
    aws --profile $profile ec2 create-tags --resources $subnetid_6 --tags Key=Name,Value="Subrede Publica 04 - $vpcname"
    echo "Associando tabela de roteamento publica $public_routetableid a subrede $subnetid_6"
    aws --profile $profile ec2 associate-route-table --subnet-id $subnetid_6 --route-table-id $public_routetableid

echo; echo =================================================================================; echo

# Subrede Privada 04 - 172.31.7.0/24 - zona de disponibilidade us-east-1e
    echo "Criando subrede privada 04 - 172.31.7.0/24 - us-east-1e"
    subnetid_7=$(aws --profile $profile ec2 create-subnet --vpc-id $vpcid --cidr-block 172.31.7.0/24 --availability-zone us-east-1e --output text --query 'Subnet.SubnetId')
    echo SubnetId=$subnetid_7
    echo "Alterando Tag Name da subrede para 'Subrede Privada 04'"
    aws --profile $profile ec2 create-tags --resources $subnetid_7 --tags Key=Name,Value="Subrede Privada 04 - $vpcname"
    echo "Associando tabela de roteamento privada $private_routetableid a subrede $subnetid_7"
    aws --profile $profile ec2 associate-route-table --subnet-id $subnetid_7 --route-table-id $private_routetableid

echo; echo =================================================================================; echo

# Criando grupos de seguranca para as instancias NAT, localizadas nas subredes publicas, liberando acesso para as subredes privadas acessarem a internet
    echo "Criando grupo de seguranca para instancia NAT, na subrede publica 01/us-east-1a, liberando acesso para a subrede privada 01"
    security_group_NAT1=$(aws --profile $profile ec2 create-security-group --group-name "NAT-us-east-1a" --description "Regras de Seguranca para a instancia NAT" --vpc-id $vpcid --query 'GroupId')
    aws --profile $profile ec2 authorize-security-group-ingress --group-id $security_group_NAT1 --protocol -1 --port -1 --cidr 172.31.1.0/24
    aws --profile $profile ec2 authorize-security-group-ingress --group-id $security_group_NAT1 --protocol tcp --port 22 --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# Criando grupos de seguranca para as instancias NAT, localizadas nas subredes publicas, liberando acesso para as subredes privadas acessarem a internet
    echo "Criando grupo de seguranca para instancia NAT, na subrede publica 02/us-east-1b, liberando acesso para a subrede privada 02"
    security_group_NAT3=$(aws --profile $profile ec2 create-security-group --group-name "NAT-us-east-1b" --description "Regras de Seguranca para a instancia NAT" --vpc-id $vpcid --query 'GroupId')
    aws --profile $profile ec2 authorize-security-group-ingress --group-id $security_group_NAT3 --protocol -1 --port -1 --cidr 172.31.3.0/24
    aws --profile $profile ec2 authorize-security-group-ingress --group-id $security_group_NAT3 --protocol tcp --port 22 --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# Criando grupos de seguranca para as instancias NAT, localizadas nas subredes publicas, liberando acesso para as subredes privadas acessarem a internet
    echo "Criando grupo de seguranca para instancia NAT, na subrede publica 03/us-east-1c, liberando acesso para a subrede privada 03"
    security_group_NAT5=$(aws --profile $profile ec2 create-security-group --group-name "NAT-us-east-1c" --description "Regras de Seguranca para a instancia NAT" --vpc-id $vpcid --query 'GroupId')
    aws --profile $profile ec2 authorize-security-group-ingress --group-id $security_group_NAT5 --protocol -1 --port -1 --cidr 172.31.5.0/24
    aws --profile $profile ec2 authorize-security-group-ingress --group-id $security_group_NAT5 --protocol tcp --port 22 --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# Criando grupos de seguranca para as instancias NAT, localizadas nas subredes publicas, liberando acesso para as subredes privadas acessarem a internet
    echo "Criando grupo de seguranca para instancia NAT, na subrede publica 04/us-east-1e, liberando acesso para a subrede privada 04"
    security_group_NAT7=$(aws --profile $profile ec2 create-security-group --group-name "NAT-us-east-1e" --description "Regras de Seguranca para a instancia NAT" --vpc-id $vpcid --query 'GroupId')
    aws --profile $profile ec2 authorize-security-group-ingress --group-id $security_group_NAT7 --protocol -1 --port -1 --cidr 172.31.7.0/24
    aws --profile $profile ec2 authorize-security-group-ingress --group-id $security_group_NAT7 --protocol tcp --port 22 --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# Dump das variaveis de ambiente, util para outros scripts
echo export vpcname=$vpcname
echo export vpcid=$vpcid
echo export internetgatewayid=$internetgatewayid
echo export public_routetableid=$public_routetableid
echo export private_routetableid=$private_routetableid
echo export subnetid_0=$subnetid_0
echo export subnetid_1=$subnetid_1
echo export subnetid_2=$subnetid_2
echo export subnetid_3=$subnetid_3
echo export subnetid_4=$subnetid_4
echo export subnetid_5=$subnetid_5
echo export subnetid_6=$subnetid_6
echo export subnetid_7=$subnetid_7
echo export security_group_NAT1=$security_group_NAT1
echo export security_group_NAT3=$security_group_NAT3
echo export security_group_NAT5=$security_group_NAT5
echo export security_group_NAT7=$security_group_NAT7

echo; echo =================================================================================
