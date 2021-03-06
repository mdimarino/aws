#!/bin/bash

# Automatização da criação de VPCs na Amazon Web Services US-EAST.

profile=$1
vpc_name=$2
cidr=$3 # exemplo: 172.16

# Cada região da AWS US-EAST tem cinco zonas de disponibilidade: a,b,c,d,e.
# Somente quatro podem ser usadas, uma fica reservada.
# Liste aqui suas zonas de disponibilidade.

availability_zone_1=us-east-1a
availability_zone_2=us-east-1b
availability_zone_3=us-east-1c
availability_zone_4=us-east-1e

# Exemplos de subredes usando CIDR 172.16.

# Cada subrede terá 4091 endereços para hosts.
# A AWS reserva os IPs .1(VPC router), .2(Amazon-provided DNS) e .3(uso futuro).
# Netmask: 255.255.240.0 = 20

# zona a publica 01 172.16.0.0/20 - 172.16.0.4 a 172.16.15.254
# zona a privada 01 172.16.16.0/20 - 172.16.16.4 a 172.16.31.254

# zona b publica 02 172.16.32.0/20 - 172.16.32.4 a 172.16.47.254
# zona b privada 02 172.16.48.0/20 - 172.16.48.4 a 172.16.63.254

# zona c publica 03 172.16.64.0/20 - 172.16.64.4 a 172.16.79.254
# zona c privada 03 172.16.80.0/20 - 172.16.80.4 a 172.16.95.254

# zona e publica 04 172.16.96.0/20 - 172.16.96.4 a 172.16.111.254
# zona e privada 04 172.16.112.0/20 - 172.16.112.4 a 172.16.127.254

echo =================================================================================; echo

# Criar VPC com CIDR ${cidr}.0.0/16.

    echo -n "* Criando VPC ${vpc_name} com CIDR ${cidr}.0.0/16: "
    vpc_id=$(aws --profile ${profile} ec2 create-vpc \
        --cidr-block ${cidr}.0.0/16 \
        --output text \
        --query 'Vpc.VpcId')
    echo "vpc_id=${vpc_id}"

    echo "* Alterando Tag Name da vpc para '${vpc_name}'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${vpc_id} \
        --tags Key=Name,Value=${vpc_name}

    echo -n "* Aguardando pela VPC..."
    while state=$(aws --profile ${profile} ec2 describe-vpcs \
        --filters Name=tag-key,Values=vpc_name \
        --filters Name=tag-value,Values=${vpc_name} \
        --output text --query 'Vpcs[*].State'); test "${state}" = "pending"; do
        echo -n . ; sleep 3;
    done; echo " ${state}"

    echo "* Habilitando atributos dns-support e dns-hostnames na vpc ${vpc_name}"
    aws --profile ${profile} ec2 modify-vpc-attribute \
        --vpc-id ${vpc_id} \
        --enable-dns-support "{\"Value\":true}"
    aws --profile ${profile} ec2 modify-vpc-attribute \
        --vpc-id ${vpc_id} \
        --enable-dns-hostnames "{\"Value\":true}"

echo; echo =================================================================================; echo

# Criar internet gateway (para permitir subredes públicas terem acesso à internet) e ligar à vpc.

    echo -n "* Criando internet gateway: "
    internet_gateway_id=$(aws --profile ${profile} ec2 create-internet-gateway \
        --output text \
        --query 'InternetGateway.InternetGatewayId')
    echo "internet_gateway_id=${internet_gateway_id}"

    echo "* Alterando Tag Name do internet gateway para '${vpc_name} - Gateway das Subredes Públicas'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${internet_gateway_id} \
        --tags Key=Name,Value="${vpc_name} - Gateway das Subredes Publicas"

    echo "* Ligando o internet gateway à vpc ${vpc_name}"
    aws --profile ${profile} ec2 attach-internet-gateway \
        --internet-gateway-id ${internet_gateway_id} \
        --vpc-id ${vpc_id}

echo; echo =================================================================================; echo

# Criar tabelas de roteamento para subredes públicas e privadas.

    # Quando a vpc é criada uma tabela de roteamento default é criada automaticamente, vamos usá-la para as subredes públicas

    echo -n "* Criando tabela de roteamento para Subredes Públicas: "

    public_routetable_id=$(aws --profile ${profile} ec2 describe-route-tables \
        --filters Name=vpc-id,Values=${vpc_id} \
        --output text \
        --query 'RouteTables[*].RouteTableId')
    echo "RouteTableId=${public_routetable_id}"

    echo "* Alterando Tag Name da tabela de roteamento para '${vpc_name} - Tabela de Roteamento das Subredes Públicas'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${public_routetable_id} \
        --tags Key=Name,Value="${vpc_name} - Tabela de Roteamento das Subredes Publicas"

    echo ''

    echo -n "* Criando tabela de roteamento para Subrede Privada 01: "
    private1_routetable_id=$(aws --profile ${profile} ec2 create-route-table \
        --vpc-id ${vpc_id} \
        --output text \
        --query 'RouteTable.RouteTableId')
    echo "RouteTableId=${private1_routetable_id}"

    echo "* Alterando Tag Name da tabela de roteamento para '${vpc_name} - Tabela de Roteamento da Subrede Privada 01'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${private1_routetable_id} \
        --tags Key=Name,Value="${vpc_name} - Tabela de Roteamento da Subrede Privada 01"

    echo ''

    echo -n "* Criando tabela de roteamento para Subrede Privada 02: "
    private2_routetable_id=$(aws --profile ${profile} ec2 create-route-table \
        --vpc-id ${vpc_id} \
        --output text \
        --query 'RouteTable.RouteTableId')
    echo "RouteTableId=${private2_routetable_id}"

    echo "* Alterando Tag Name da tabela de roteamento para '${vpc_name} - Tabela de Roteamento da Subrede Privada 02'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${private2_routetable_id} \
        --tags Key=Name,Value="${vpc_name} - Tabela de Roteamento da Subrede Privada 02"

    echo ''

    echo -n "* Criando tabela de roteamento para Subrede Privada 03: "
    private3_routetable_id=$(aws --profile ${profile} ec2 create-route-table \
        --vpc-id ${vpc_id} \
        --output text \
        --query 'RouteTable.RouteTableId')
    echo "RouteTableId=${private3_routetable_id}"

    echo "* Alterando Tag Name da tabela de roteamento para '${vpc_name} - Tabela de Roteamento da Subrede Privada 03'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${private3_routetable_id} \
        --tags Key=Name,Value="${vpc_name} - Tabela de Roteamento da Subrede Privada 03"

    echo ''

    echo -n "* Criando tabela de roteamento para Subrede Privada 04: "
    private4_routetable_id=$(aws --profile ${profile} ec2 create-route-table \
        --vpc-id ${vpc_id} \
        --output text \
        --query 'RouteTable.RouteTableId')
    echo "RouteTableId=${private4_routetable_id}"

    echo "* Alterando Tag Name da tabela de roteamento para '${vpc_name} - Tabela de Roteamento da Subrede Privada 04'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${private4_routetable_id} \
        --tags Key=Name,Value="${vpc_name} - Tabela de Roteamento da Subrede Privada 04"

echo; echo =================================================================================; echo

# Criar rota na tabela de roteamento pública para o internet gateway, ira rotear o tráfego para fora desta rede para internet.

    echo "* Criando rota na tabela de roteamento pública para o internet gateway"
    aws --profile ${profile} ec2 create-route \
        --route-table-id ${public_routetable_id} \
        --gateway-id ${internet_gateway_id} \
        --destination-cidr-block 0.0.0.0/0

echo; echo =================================================================================; echo

# Criar subredes:

# Subrede Pública 01 - ${cidr}.0.0/20 - zona de disponibilidade ${availability_zone_1}.

    echo -n "* Criando subrede pública 01 - ${cidr}.0.0/20 - ${availability_zone_1}: "
    subnetid_1=$(aws --profile ${profile} ec2 create-subnet \
        --vpc-id ${vpc_id} \
        --cidr-block ${cidr}.0.0/20 \
        --availability-zone ${availability_zone_1} \
        --output text \
        --query 'Subnet.SubnetId')
    echo "SubnetId=${subnetid_1}"

    echo "* Instâncias criadas na subrede ${subnetid_1} devem ser criadas com um IP público"
    aws --profile ${profile} ec2 modify-subnet-attribute \
        --subnet-id ${subnetid_1} \
        --map-public-ip-on-launch

    echo "* Alterando Tag Name da subrede para '${vpc_name} - Subrede Pública 01'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${subnetid_1} \
        --tags Key=Name,Value="${vpc_name} - Subrede Publica 01"

    echo -n "* Associando tabela de roteamento das subredes públicas ${public_routetable_id} a subrede ${subnetid_1}: "
    aws --profile ${profile} ec2 associate-route-table \
        --subnet-id ${subnetid_1} \
        --route-table-id ${public_routetable_id}

echo; echo =================================================================================; echo

# Subrede Privada 01 - ${cidr}.16.0/20 - zona de disponibilidade ${availability_zone_1}.

    echo -n "* Criando subrede privada 01 - ${cidr}.16.0/22 - ${availability_zone_1}: "
    subnetid_2=$(aws --profile ${profile} ec2 create-subnet \
        --vpc-id ${vpc_id} \
        --cidr-block ${cidr}.16.0/20 \
        --availability-zone ${availability_zone_1} \
        --output text \
        --query 'Subnet.SubnetId')
    echo "SubnetId=${subnetid_2}"

    echo "* Instâncias criadas na subrede ${subnetid_2} devem ser criadas sem IP público"
    aws --profile ${profile} ec2 modify-subnet-attribute \
        --subnet-id ${subnetid_2} \
        --no-map-public-ip-on-launch

    echo "* Alterando Tag Name da subrede para '${vpc_name} - Subrede Privada 01'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${subnetid_2} \
        --tags Key=Name,Value="${vpc_name} - Subrede Privada 01"

    echo -n "* Associando tabela de roteamento da subrede privadas ${private1_routetable_id} a subrede ${subnetid_2}: "
    aws --profile ${profile} ec2 associate-route-table \
        --subnet-id ${subnetid_2} \
        --route-table-id ${private1_routetable_id}

echo; echo =================================================================================; echo

# Subrede Pública 02 - ${cidr}.32.0/20 - zona de disponibilidade ${availability_zone_2}.

    echo -n "* Criando subrede pública 02 - ${cidr}.32.0/20 - ${availability_zone_2}: "
    subnetid_3=$(aws --profile ${profile} ec2 create-subnet \
        --vpc-id ${vpc_id} --cidr-block ${cidr}.32.0/20 \
        --availability-zone ${availability_zone_2} \
        --output text \
        --query 'Subnet.SubnetId')
    echo SubnetId=${subnetid_3}

    echo "* Instâncias criadas na subrede ${subnetid_3} devem ser criadas com um IP público"
    aws --profile ${profile} ec2 modify-subnet-attribute \
        --subnet-id ${subnetid_3} \
        --map-public-ip-on-launch

    echo "* Alterando Tag Name da subrede para '${vpc_name} - Subrede Pública 02'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${subnetid_3} \
        --tags Key=Name,Value="${vpc_name} - Subrede Publica 02"

    echo -n "* Associando tabela de roteamento das subredes públicas ${public_routetable_id} a subrede ${subnetid_3}: "
    aws --profile ${profile} ec2 associate-route-table \
        --subnet-id ${subnetid_3} \
        --route-table-id ${public_routetable_id}

echo; echo =================================================================================; echo

# Subrede Privada 02 - ${cidr}.48.0/20 - zona de disponibilidade ${availability_zone_2}.

    echo -n "* Criando subrede privada 02 - ${cidr}.48.0/20 - ${availability_zone_2}: "
    subnetid_4=$(aws --profile ${profile} ec2 create-subnet \
        --vpc-id ${vpc_id} \
        --cidr-block ${cidr}.48.0/20 \
        --availability-zone ${availability_zone_2} \
        --output text \
        --query 'Subnet.SubnetId')
    echo "SubnetId=${subnetid_4}"

    echo "* Instâncias criadas na subrede ${subnetid_4} devem ser criadas sem IP público"
    aws --profile ${profile} ec2 modify-subnet-attribute \
        --subnet-id ${subnetid_4} \
        --no-map-public-ip-on-launch

    echo "* Alterando Tag Name da subrede para '${vpc_name} - Subrede Privada 02'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${subnetid_4} \
        --tags Key=Name,Value="${vpc_name} - Subrede Privada 02"

    echo -n "* Associando tabela de roteamento da subrede privada ${private2_routetable_id} a subrede ${subnetid_4}: "
    aws --profile ${profile} ec2 associate-route-table \
        --subnet-id ${subnetid_4} \
        --route-table-id ${private2_routetable_id}

echo; echo =================================================================================; echo

# Subrede Pública 03 - ${cidr}.64.0/20 - zona de disponibilidade ${availability_zone_3}.

    echo -n "* Criando subrede pública 03 - ${cidr}.64.0/20 - ${availability_zone_3}: "
    subnetid_5=$(aws --profile ${profile} ec2 create-subnet \
        --vpc-id ${vpc_id} \
        --cidr-block ${cidr}.64.0/20 \
        --availability-zone ${availability_zone_3} \
        --output text \
        --query 'Subnet.SubnetId')
    echo "SubnetId=${subnetid_5}"

    echo "* Instâncias criadas na subrede ${subnetid_5} devem ser criadas com um IP público"
    aws --profile ${profile} ec2 modify-subnet-attribute \
        --subnet-id ${subnetid_5} \
        --map-public-ip-on-launch

    echo "* Alterando Tag Name da subrede para '${vpc_name} - Subrede Pública 03'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${subnetid_5} \
        --tags Key=Name,Value="${vpc_name} - Subrede Publica 03"

    echo -n "* Associando tabela de roteamento das subredes públicas ${public_routetable_id} a subrede ${subnetid_5}: "
    aws --profile ${profile} ec2 associate-route-table \
        --subnet-id ${subnetid_5} \
        --route-table-id ${public_routetable_id}

echo; echo =================================================================================; echo

# Subrede Privada 03 - ${cidr}.80.0/20 - zona de disponibilidade ${availability_zone_3}.

    echo -n "* Criando subrede privada 03 - ${cidr}.80.0/20 - ${availability_zone_3}: "
    subnetid_6=$(aws --profile ${profile} ec2 create-subnet \
        --vpc-id ${vpc_id} \
        --cidr-block ${cidr}.80.0/20 \
        --availability-zone ${availability_zone_3} \
        --output text \
        --query 'Subnet.SubnetId')
    echo "SubnetId=${subnetid_6}"

    echo "* Instâncias criadas na subrede ${subnetid_6} devem ser criadas sem IP público"
    aws --profile ${profile} ec2 modify-subnet-attribute \
        --subnet-id ${subnetid_6} \
        --no-map-public-ip-on-launch

    echo "* Alterando Tag Name da subrede para '${vpc_name} - Subrede Privada 03'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${subnetid_6} \
        --tags Key=Name,Value="${vpc_name} - Subrede Privada 03"

    echo -n "* Associando tabela de roteamento da subrede privada ${private3_routetable_id} a subrede ${subnetid_6}: "
    aws --profile ${profile} ec2 associate-route-table \
        --subnet-id ${subnetid_6} \
        --route-table-id ${private3_routetable_id}

echo; echo =================================================================================; echo

# Subrede Pública 04 - ${cidr}.96.0/20 - zona de disponibilidade ${availability_zone_4}.

    echo -n "* Criando subrede pública 04 - ${cidr}.96.0/20 - ${availability_zone_4}: "
    subnetid_7=$(aws --profile ${profile} ec2 create-subnet \
        --vpc-id ${vpc_id} \
        --cidr-block ${cidr}.96.0/20 \
        --availability-zone ${availability_zone_4} \
        --output text \
        --query 'Subnet.SubnetId')
    echo "SubnetId=${subnetid_7}"

    echo "* Instâncias criadas na subrede ${subnetid_7} devem ser criadas com um IP público"
    aws --profile ${profile} ec2 modify-subnet-attribute \
        --subnet-id ${subnetid_7} \
        --map-public-ip-on-launch

    echo "* Alterando Tag Name da subrede para '${vpc_name} - Subrede Pública 04'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${subnetid_7} \
        --tags Key=Name,Value="${vpc_name} - Subrede Publica 04"

    echo -n "* Associando tabela de roteamento das subredes públicas ${public_routetable_id} a subrede ${subnetid_7}: "
    aws --profile ${profile} ec2 associate-route-table \
        --subnet-id ${subnetid_7} \
        --route-table-id ${public_routetable_id}

echo; echo =================================================================================; echo

# Subrede Privada 04 - ${cidr}.112.0/20 - zona de disponibilidade ${availability_zone_4}.

    echo -n "* Criando subrede privada 04 - ${cidr}.112.0/20 - ${availability_zone_4}: "
    subnetid_8=$(aws --profile ${profile} ec2 create-subnet \
        --vpc-id ${vpc_id} \
        --cidr-block ${cidr}.112.0/20 \
        --availability-zone ${availability_zone_4} \
        --output text --query 'Subnet.SubnetId')
    echo "SubnetId=${subnetid_8}"

    echo "* Instâncias criadas na subrede ${subnetid_8} devem ser criadas sem IP público"
    aws --profile ${profile} ec2 modify-subnet-attribute \
        --subnet-id ${subnetid_8} \
        --no-map-public-ip-on-launch

    echo "* Alterando Tag Name da subrede para '${vpc_name} - Subrede Privada 04'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${subnetid_8} \
        --tags Key=Name,Value="${vpc_name} - Subrede Privada 04"

    echo -n "* Associando tabela de roteamento da subrede privada ${private4_routetable_id} a subrede ${subnetid_8}: "
    aws --profile ${profile} ec2 associate-route-table \
        --subnet-id ${subnetid_8} \
        --route-table-id ${private4_routetable_id}

echo; echo =================================================================================; echo

# Criar grupos de segurança para as instâncias NAT, localizadas nas subredes
# Públicas, liberando acesso para as subredes privadas acessarem a internet.

    echo "* Criando grupo de segurança para instancia NAT, na subrede Pública 01/${availability_zone_1}, liberando acesso para a subrede privada 01"
    security_group_NAT1=$(aws --profile ${profile} ec2 create-security-group \
        --group-name "${vpc_name}-NAT-${availability_zone_1}" \
        --description "${vpc_name} - Regras de Seguranca para a instancia NAT" \
        --vpc-id ${vpc_id} \
        --query 'GroupId')

    echo "* Alterando Tag Name do grupo de segurança para '${vpc_name} - SecGrpNAT1'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${security_group_NAT1} \
        --tags Key=Name,Value="${vpc_name} - SecGrpNAT1"

    aws --profile ${profile} ec2 authorize-security-group-ingress \
        --group-id ${security_group_NAT1} \
        --protocol -1 \
        --port -1 \
        --cidr ${cidr}.16.0/20

    aws --profile ${profile} ec2 authorize-security-group-ingress \
        --group-id ${security_group_NAT1} \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# Criar grupos de segurança para as instâncias NAT, localizadas nas subredes
# Públicas, liberando acesso para as subredes privadas acessarem a internet.

    echo "* Criando grupo de segurança para instancia NAT, na subrede Pública 02/${availability_zone_2}, liberando acesso para a subrede privada 02"
    security_group_NAT3=$(aws --profile ${profile} ec2 create-security-group \
        --group-name "${vpc_name}-NAT-${availability_zone_2}" \
        --description "${vpc_name} - Regras de Seguranca para a instancia NAT" \
        --vpc-id ${vpc_id} \
        --query 'GroupId')

    echo "* Alterando Tag Name do grupo de segurança para '${vpc_name} - SecGrpNAT3'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${security_group_NAT3} \
        --tags Key=Name,Value="${vpc_name} - SecGrpNAT3"

    aws --profile ${profile} ec2 authorize-security-group-ingress \
        --group-id ${security_group_NAT3} \
        --protocol -1 \
        --port -1 \
        --cidr ${cidr}.48.0/20

    aws --profile ${profile} ec2 authorize-security-group-ingress \
        --group-id ${security_group_NAT3} \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# Criar grupos de segurança para as instâncias NAT, localizadas nas subredes
# Públicas, liberando acesso para as subredes privadas acessarem a internet.

    echo "* Criando grupo de segurança para instancia NAT, na subrede Pública 03/${availability_zone_3}, liberando acesso para a subrede privada 03"
    security_group_NAT5=$(aws --profile ${profile} ec2 create-security-group \
        --group-name "${vpc_name}-NAT-${availability_zone_3}" \
        --description "${vpc_name} - Regras de Seguranca para a instancia NAT" \
        --vpc-id ${vpc_id} \
        --query 'GroupId')

    echo "* Alterando Tag Name do grupo de segurança para '${vpc_name} - SecGrpNAT5'"
    aws --profile ${profile} ec2 create-tags --resources ${security_group_NAT5} --tags Key=Name,Value="${vpc_name} - SecGrpNAT5"

    aws --profile ${profile} ec2 authorize-security-group-ingress \
        --group-id ${security_group_NAT5} \
        --protocol -1 \
        --port -1 \
        --cidr ${cidr}.80.0/20

    aws --profile ${profile} ec2 authorize-security-group-ingress \
        --group-id ${security_group_NAT5} \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# Criar grupos de segurança para as instâncias NAT, localizadas nas subredes
# Públicas, liberando acesso para as subredes privadas acessarem a internet.

    echo "* Criando grupo de seguranca para instancia NAT, na subrede Pública 04/${availability_zone_4}, liberando acesso para a subrede privada 04"
    security_group_NAT7=$(aws --profile ${profile} ec2 create-security-group \
        --group-name "${vpc_name}-NAT-${availability_zone_4}" \
        --description "${vpc_name} - Regras de Seguranca para a instancia NAT" \
        --vpc-id ${vpc_id} \
        --query 'GroupId')

    echo "* Alterando Tag Name do grupo de segurança para '${vpc_name} - SecGrpNAT7'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${security_group_NAT7} \
        --tags Key=Name,Value="${vpc_name} - SecGrpNAT7"

    aws --profile ${profile} ec2 authorize-security-group-ingress \
        --group-id ${security_group_NAT7} \
        --protocol -1 \
        --port -1 \
        --cidr ${cidr}.112.0/20

    aws --profile ${profile} ec2 authorize-security-group-ingress \
        --group-id ${security_group_NAT7} \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# Criar conjunto de opções do DHCP para a vpc.
# O nome da vpc será usado como nome de domínio.

    echo "* Criando conjunto de opções de DHCP para a vpc. O nome da vpc, ${vpc_name}, será usado como nome de domínio"
    dhcp_options_id=$(aws --profile ${profile} ec2 create-dhcp-options \
        --dhcp-configuration "Key=domain-name,Values=${vpc_name}" "Key=domain-name-servers,Values=AmazonProvidedDNS" \
        --query 'DhcpOptions.DhcpOptionsId')

    echo "* Associando conjunto de opções de DHCP com a vpc ${vpc_name}"
    aws --profile ${profile} ec2 associate-dhcp-options \
        --dhcp-options-id ${dhcp_options_id} \
        --vpc-id ${vpc_id}

    echo "* Alterando Tag Name do conjunto de opções de DHCP para '${vpc_name} - Conjunto de Opcoes do DHCP'"
    aws --profile ${profile} ec2 create-tags \
        --resources ${dhcp_options_id} \
        --tags Key=Name,Value="${vpc_name} - Conjunto de Opcoes do DHCP"

echo; echo =================================================================================; echo

# Criar domínio interno da VPC.

    echo "* Criando domínio interno da VPC ${vpc_name}"
    aws --profile ${profile} route53 create-hosted-zone \
        --name ${vpc_name} \
        --vpc "VPCRegion=us-east-1,VPCId=${vpc_id}" \
        --caller-reference $(date +%Y%m%d-%H%M) \
        --hosted-zone-config "Comment=Dominio privado da vpc ${vpc_name}" \
        --output text > create_hosted_zone_output.txt

    hosted_zone_id=$(grep HOSTEDZONE create_hosted_zone_output.txt | awk '{print $3}' | cut -d/ -f3)
    change_info_id=$(grep CHANGEINFO create_hosted_zone_output.txt | awk '{print $2}' | cut -d/ -f3)

    rm create_hosted_zone_output.txt

    echo -n "* Aguardando pelo INSYNC"
    while state=$(aws --profile ${profile} route53 get-change \
        --id ${change_info_id} \
        --output text \
        --query 'ChangeInfo.Status'); test "${state}" = "PENDING"; do
        echo -n . ; sleep 3;
    done; echo " OK!"

echo; echo =================================================================================; echo

# Criar arquivo ${vpc_name}_vars.sh com o dump das variáveis de ambiente.

    dump_file=${vpc_name}_vars.sh

    echo "#!/bin/bash" > ${dump_file}
    echo "" >> ${dump_file}

# Dump das variáveis de ambiente, usadas em outros scripts.

    echo "export profile=${profile}" | tee -a ${dump_file}
    echo "export cidr=${cidr}" | tee -a ${dump_file}
    echo "export vpc_name=${vpc_name}" | tee -a ${dump_file}
    echo "export vpc_id=${vpc_id}" | tee -a ${dump_file}
    echo "export internet_gateway_id=${internet_gateway_id}" | tee -a ${dump_file}
    echo "export public_routetable_id=${public_routetable_id}" | tee -a ${dump_file}
    echo "export private1_routetable_id=${private1_routetable_id}" | tee -a ${dump_file}
    echo "export private2_routetable_id=${private2_routetable_id}" | tee -a ${dump_file}
    echo "export private3_routetable_id=${private3_routetable_id}" | tee -a ${dump_file}
    echo "export private4_routetable_id=${private4_routetable_id}" | tee -a ${dump_file}
    echo "export subnetid_1=${subnetid_1}" | tee -a ${dump_file}
    echo "export subnetid_2=${subnetid_2}" | tee -a ${dump_file}
    echo "export subnetid_3=${subnetid_3}" | tee -a ${dump_file}
    echo "export subnetid_4=${subnetid_4}" | tee -a ${dump_file}
    echo "export subnetid_5=${subnetid_5}" | tee -a ${dump_file}
    echo "export subnetid_6=${subnetid_6}" | tee -a ${dump_file}
    echo "export subnetid_7=${subnetid_7}" | tee -a ${dump_file}
    echo "export subnetid_8=${subnetid_8}" | tee -a ${dump_file}
    echo "export security_group_NAT1=${security_group_NAT1}" | tee -a ${dump_file}
    echo "export security_group_NAT3=${security_group_NAT3}" | tee -a ${dump_file}
    echo "export security_group_NAT5=${security_group_NAT5}" | tee -a ${dump_file}
    echo "export security_group_NAT7=${security_group_NAT7}" | tee -a ${dump_file}
    echo "export dhcp_options_id=${dhcp_options_id}" | tee -a ${dump_file}
    echo "export hosted_zone_id=${hosted_zone_id}" | tee -a ${dump_file}

echo; echo =================================================================================
