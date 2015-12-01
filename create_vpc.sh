#!/bin/bash

# Automatização da criação de VPCs na Amazon Web Services

profile=$1
vpc_name=$2
cidr=$3

# Cada região da AWS tem cinco zonas de disponibilidade: a,b,c,d,e. Somente quatro podem ser usadas, uma fica reservada.
# Liste aqui suas zonas de disponibilidade

availability_zone_1=us-east-1a
availability_zone_2=us-east-1c
availability_zone_3=us-east-1d
availability_zone_4=us-east-1e

echo =================================================================================; echo

# Criar VPC com CIDR ${cidr}.0.0/16

    echo -n "* Criando VPC ${vpc_name} com CIDR ${cidr}.0.0/16: "
    vpc_id=$(aws --profile ${profile} ec2 create-vpc --cidr-block ${cidr}.0.0/16 --output text --query 'Vpc.VpcId')
    echo vpc_id=${vpc_id}

    echo "* Alterando Tag Name da vpc para '${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${vpc_id} --tags Key=Name,Value=${vpc_name}

    echo -n "* Aguardando pela VPC..."
    while state=$(aws --profile ${profile} ec2 describe-vpcs --filters Name=tag-key,Values=vpc_name --filters Name=tag-value,Values=${vpc_name} --output text --query 'Vpcs[*].State'); test "${state}" = "pending"; do
        echo -n . ; sleep 3;
    done; echo " ${state}"

    echo "* Habilitando atributos dns-support e dns-hostnames da vpc ${vpc_name}"
    aws --profile ${profile} ec2 modify-vpc-attribute --vpc-id ${vpc_id} --enable-dns-support "{\"Value\":true}"
    aws --profile ${profile} ec2 modify-vpc-attribute --vpc-id ${vpc_id} --enable-dns-hostnames "{\"Value\":true}"

echo; echo =================================================================================; echo

# Criar um internet gateway (para permitir subredes públicas terem acesso à internet)

    echo -n "* Criando um internet gateway: "
    internet_gateway_id=$(aws --profile ${profile} ec2 create-internet-gateway --output text --query 'InternetGateway.InternetGatewayId')
    echo internet_gateway_id=${internet_gateway_id}

    echo "* Alterando Tag Name do internet gateway para 'Gateway das Subredes Públicas - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${internet_gateway_id} --tags Key=Name,Value="Gateway das Subredes Publicas - ${vpc_name}"

echo; echo =================================================================================; echo

# Ligar o internet gateway à vpc

    echo "* Ligando o internet gateway à vpc ${vpc_name}"
    aws --profile ${profile} ec2 attach-internet-gateway --internet-gateway-id ${internet_gateway_id} --vpc-id ${vpc_id}

echo; echo =================================================================================; echo

# Criar tabelas de roteamento para subredes públicas e privadas

    echo -n "* Criando tabela de roteamento para subredes Públicas: "
    # Quando a vpc é criada uma tabela de roteamento default é criada automaticamente, vamos usá-la para as subredes públicas
    public_routetable_id=$(aws --profile ${profile} ec2 describe-route-tables --filters Name=vpc-id,Values=${vpc_id} --output text --query 'RouteTables[*].RouteTableId')
    echo RouteTableId=${public_routetable_id}

    echo "* Alterando Tag Name da tabela de roteamento para 'Tabela de Roteamento das Subredes Públicas - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${public_routetable_id} --tags Key=Name,Value="Tabela de Roteamento das Subredes Publicas - ${vpc_name}"

    echo ''

    echo -n "* Criando tabela de roteamento para Subrede Privada 01: "
    private1_routetable_id=$(aws --profile ${profile} ec2 create-route-table --vpc-id ${vpc_id} --output text --query 'RouteTable.RouteTableId')
    echo RouteTableId=${private1_routetable_id}

    echo "* Alterando Tag Name da tabela de roteamento para 'Tabela de Roteamento da Subrede Privada 01 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${private1_routetable_id} --tags Key=Name,Value="Tabela de Roteamento da Subrede Privada 01 - ${vpc_name}"

    echo ''

    echo -n "* Criando tabela de roteamento para Subrede Privada 02: "
    private2_routetable_id=$(aws --profile ${profile} ec2 create-route-table --vpc-id ${vpc_id} --output text --query 'RouteTable.RouteTableId')
    echo RouteTableId=${private2_routetable_id}

    echo "* Alterando Tag Name da tabela de roteamento para 'Tabela de Roteamento da Subrede Privada 02 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${private2_routetable_id} --tags Key=Name,Value="Tabela de Roteamento da Subrede Privada 02 - ${vpc_name}"

    echo ''

    echo -n "* Criando tabela de roteamento para Subrede Privada 03: "
    private3_routetable_id=$(aws --profile ${profile} ec2 create-route-table --vpc-id ${vpc_id} --output text --query 'RouteTable.RouteTableId')
    echo RouteTableId=${private3_routetable_id}

    echo "* Alterando Tag Name da tabela de roteamento para 'Tabela de Roteamento da Subrede Privada 03 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${private3_routetable_id} --tags Key=Name,Value="Tabela de Roteamento da Subrede Privada 03 - ${vpc_name}"

    echo ''

    echo -n "* Criando tabela de roteamento para Subrede Privada 04: "
    private4_routetable_id=$(aws --profile ${profile} ec2 create-route-table --vpc-id ${vpc_id} --output text --query 'RouteTable.RouteTableId')
    echo RouteTableId=${private4_routetable_id}

    echo "* Alterando Tag Name da tabela de roteamento para 'Tabela de Roteamento da Subrede Privada 04 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${private4_routetable_id} --tags Key=Name,Value="Tabela de Roteamento da Subrede Privada 04 - ${vpc_name}"

echo; echo =================================================================================; echo

# Criar rota na tabela de roteamento pública para o internet gateway, ira rotear o tráfego para fora desta rede para internet

    echo "* Criando rota na tabela de roteamento pública para o internet gateway"
    aws --profile ${profile} ec2 create-route --route-table-id ${public_routetable_id} --gateway-id ${internet_gateway_id} --destination-cidr-block 0.0.0.0/0

echo; echo =================================================================================; echo

# Criar subredes:

# Subrede Pública 01 - ${cidr}.0.0/24 - zona de disponibilidade ${availability_zone_1}

    echo -n "* Criando subrede pública 01 - ${cidr}.0.0/24 - ${availability_zone_1}: "
    subnetid_1=$(aws --profile ${profile} ec2 create-subnet --vpc-id ${vpc_id} --cidr-block ${cidr}.0.0/24 --availability-zone ${availability_zone_1} --output text --query 'Subnet.SubnetId')
    echo SubnetId=${subnetid_1}

    echo "* Alterando Tag Name da subrede para 'Subrede Pública 01 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${subnetid_1} --tags Key=Name,Value="Subrede Publica 01 - ${vpc_name}"

    echo -n "* Associando tabela de roteamento das subredes públicas ${public_routetable_id} a subrede ${subnetid_1}: "
    aws --profile ${profile} ec2 associate-route-table --subnet-id ${subnetid_1} --route-table-id ${public_routetable_id}

echo; echo =================================================================================; echo

# Subrede Privada 01 - ${cidr}.1.0/24 - zona de disponibilidade ${availability_zone_1}

    echo -n "* Criando subrede privada 01 - ${cidr}.1.0/24 - ${availability_zone_1}: "
    subnetid_2=$(aws --profile ${profile} ec2 create-subnet --vpc-id ${vpc_id} --cidr-block ${cidr}.1.0/24 --availability-zone ${availability_zone_1} --output text --query 'Subnet.SubnetId')
    echo SubnetId=${subnetid_2}

    echo "* Alterando Tag Name da subrede para 'Subrede Privada 01 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${subnetid_2} --tags Key=Name,Value="Subrede Privada 01 - ${vpc_name}"

    echo -n "* Associando tabela de roteamento da subrede privadas ${private1_routetable_id} a subrede ${subnetid_2}: "
    aws --profile ${profile} ec2 associate-route-table --subnet-id ${subnetid_2} --route-table-id ${private1_routetable_id}

echo; echo =================================================================================; echo

# Subrede Pública 02 - ${cidr}.2.0/24 - zona de disponibilidade ${availability_zone_2}

    echo -n "* Criando subrede pública 02 - ${cidr}.2.0/24 - ${availability_zone_2}: "
    subnetid_3=$(aws --profile ${profile} ec2 create-subnet --vpc-id ${vpc_id} --cidr-block ${cidr}.2.0/24 --availability-zone ${availability_zone_2} --output text --query 'Subnet.SubnetId')
    echo SubnetId=${subnetid_3}

    echo "* Alterando Tag Name da subrede para 'Subrede Pública 02 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${subnetid_3} --tags Key=Name,Value="Subrede Publica 02 - ${vpc_name}"

    echo -n "* Associando tabela de roteamento das subredes públicas ${public_routetable_id} a subrede ${subnetid_3}: "
    aws --profile ${profile} ec2 associate-route-table --subnet-id ${subnetid_3} --route-table-id ${public_routetable_id}

echo; echo =================================================================================; echo

# Subrede Privada 02 - ${cidr}.3.0/24 - zona de disponibilidade ${availability_zone_2}

    echo -n "* Criando subrede privada 02 - ${cidr}.3.0/24 - ${availability_zone_2}: "
    subnetid_4=$(aws --profile ${profile} ec2 create-subnet --vpc-id ${vpc_id} --cidr-block ${cidr}.3.0/24 --availability-zone ${availability_zone_2} --output text --query 'Subnet.SubnetId')
    echo SubnetId=${subnetid_4}

    echo "* Alterando Tag Name da subrede para 'Subrede Privada 02 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${subnetid_4} --tags Key=Name,Value="Subrede Privada 02 - ${vpc_name}"

    echo -n "* Associando tabela de roteamento da subrede privada ${private2_routetable_id} a subrede ${subnetid_4}: "
    aws --profile ${profile} ec2 associate-route-table --subnet-id ${subnetid_4} --route-table-id ${private2_routetable_id}

echo; echo =================================================================================; echo

# Subrede Pública 03 - ${cidr}.4.0/24 - zona de disponibilidade ${availability_zone_3}

    echo -n "* Criando subrede pública 03 - ${cidr}.4.0/24 - ${availability_zone_3}: "
    subnetid_5=$(aws --profile ${profile} ec2 create-subnet --vpc-id ${vpc_id} --cidr-block ${cidr}.4.0/24 --availability-zone ${availability_zone_3} --output text --query 'Subnet.SubnetId')
    echo SubnetId=${subnetid_5}

    echo "* Alterando Tag Name da subrede para 'Subrede Pública 03 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${subnetid_5} --tags Key=Name,Value="Subrede Publica 03 - ${vpc_name}"

    echo -n "* Associando tabela de roteamento das subredes públicas ${public_routetable_id} a subrede ${subnetid_5}: "
    aws --profile ${profile} ec2 associate-route-table --subnet-id ${subnetid_5} --route-table-id ${public_routetable_id}

echo; echo =================================================================================; echo

# Subrede Privada 03 - ${cidr}.5.0/24 - zona de disponibilidade ${availability_zone_3}

    echo -n "* Criando subrede privada 03 - ${cidr}.5.0/24 - ${availability_zone_3}: "
    subnetid_6=$(aws --profile ${profile} ec2 create-subnet --vpc-id ${vpc_id} --cidr-block ${cidr}.5.0/24 --availability-zone ${availability_zone_3} --output text --query 'Subnet.SubnetId')
    echo SubnetId=${subnetid_6}

    echo "* Alterando Tag Name da subrede para 'Subrede Privada 03 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${subnetid_6} --tags Key=Name,Value="Subrede Privada 03 - ${vpc_name}"

    echo -n "* Associando tabela de roteamento da subrede privada ${private3_routetable_id} a subrede ${subnetid_6}: "
    aws --profile ${profile} ec2 associate-route-table --subnet-id ${subnetid_6} --route-table-id ${private3_routetable_id}

echo; echo =================================================================================; echo

# Subrede Pública 04 - ${cidr}.6.0/24 - zona de disponibilidade ${availability_zone_4}

    echo -n "* Criando subrede pública 04 - ${cidr}.6.0/24 - ${availability_zone_4}: "
    subnetid_7=$(aws --profile ${profile} ec2 create-subnet --vpc-id ${vpc_id} --cidr-block ${cidr}.6.0/24 --availability-zone ${availability_zone_4} --output text --query 'Subnet.SubnetId')
    echo SubnetId=${subnetid_7}

    echo "* Alterando Tag Name da subrede para 'Subrede Pública 04 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${subnetid_7} --tags Key=Name,Value="Subrede Publica 04 - ${vpc_name}"

    echo -n "* Associando tabela de roteamento das subredes públicas ${public_routetable_id} a subrede ${subnetid_7}: "
    aws --profile ${profile} ec2 associate-route-table --subnet-id ${subnetid_7} --route-table-id ${public_routetable_id}

echo; echo =================================================================================; echo

# Subrede Privada 04 - ${cidr}.7.0/24 - zona de disponibilidade ${availability_zone_4}

    echo -n "* Criando subrede privada 04 - ${cidr}.7.0/24 - ${availability_zone_4}: "
    subnetid_8=$(aws --profile ${profile} ec2 create-subnet --vpc-id ${vpc_id} --cidr-block ${cidr}.7.0/24 --availability-zone ${availability_zone_4} --output text --query 'Subnet.SubnetId')
    echo SubnetId=${subnetid_8}

    echo "* Alterando Tag Name da subrede para 'Subrede Privada 04 - ${vpc_name}'"
    aws --profile ${profile} ec2 create-tags --resources ${subnetid_8} --tags Key=Name,Value="Subrede Privada 04 - ${vpc_name}"

    echo -n "* Associando tabela de roteamento da subrede privada ${private4_routetable_id} a subrede ${subnetid_8}: "
    aws --profile ${profile} ec2 associate-route-table --subnet-id ${subnetid_8} --route-table-id ${private4_routetable_id}

echo; echo =================================================================================; echo

# Criar grupos de segurança para as instâncias NAT, localizadas nas subredes Públicas, liberando acesso para as subredes privadas acessarem a internet

    echo "* Criando grupo de segurança para instancia NAT, na subrede Pública 01/${availability_zone_1}, liberando acesso para a subrede privada 01"
    security_group_NAT1=$(aws --profile ${profile} ec2 create-security-group --group-name "NAT-${availability_zone_1}-${vpc_name}" --description "Regras de Seguranca para a instancia NAT - ${vpc_name}" --vpc-id ${vpc_id} --query 'GroupId')

    echo "* Alterando Tag Name do grupo de segurança para 'SecGrpNAT1'"
    aws --profile ${profile} ec2 create-tags --resources ${security_group_NAT1} --tags Key=Name,Value="SecGrpNAT1"

    aws --profile ${profile} ec2 authorize-security-group-ingress --group-id ${security_group_NAT1} --protocol -1 --port -1 --cidr ${cidr}.1.0/24

    aws --profile ${profile} ec2 authorize-security-group-ingress --group-id ${security_group_NAT1} --protocol tcp --port 22 --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# Criar grupos de segurança para as instâncias NAT, localizadas nas subredes Públicas, liberando acesso para as subredes privadas acessarem a internet

    echo "* Criando grupo de segurança para instancia NAT, na subrede Pública 02/${availability_zone_2}, liberando acesso para a subrede privada 02"
    security_group_NAT3=$(aws --profile ${profile} ec2 create-security-group --group-name "NAT-${availability_zone_2}-${vpc_name}" --description "Regras de Seguranca para a instancia NAT - ${vpc_name}" --vpc-id ${vpc_id} --query 'GroupId')

    echo "* Alterando Tag Name do grupo de segurança para 'SecGrpNAT3'"
    aws --profile ${profile} ec2 create-tags --resources ${security_group_NAT3} --tags Key=Name,Value="SecGrpNAT3"

    aws --profile ${profile} ec2 authorize-security-group-ingress --group-id ${security_group_NAT3} --protocol -1 --port -1 --cidr ${cidr}.3.0/24

    aws --profile ${profile} ec2 authorize-security-group-ingress --group-id ${security_group_NAT3} --protocol tcp --port 22 --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# Criar grupos de segurança para as instâncias NAT, localizadas nas subredes Públicas, liberando acesso para as subredes privadas acessarem a internet

    echo "* Criando grupo de segurança para instancia NAT, na subrede Pública 03/${availability_zone_3}, liberando acesso para a subrede privada 03"
    security_group_NAT5=$(aws --profile ${profile} ec2 create-security-group --group-name "NAT-${availability_zone_3}-${vpc_name}" --description "Regras de Seguranca para a instancia NAT - ${vpc_name}" --vpc-id ${vpc_id} --query 'GroupId')

    echo "* Alterando Tag Name do grupo de segurança para 'SecGrpNAT5'"
    aws --profile ${profile} ec2 create-tags --resources ${security_group_NAT5} --tags Key=Name,Value="SecGrpNAT5"

    aws --profile ${profile} ec2 authorize-security-group-ingress --group-id ${security_group_NAT5} --protocol -1 --port -1 --cidr ${cidr}.5.0/24

    aws --profile ${profile} ec2 authorize-security-group-ingress --group-id ${security_group_NAT5} --protocol tcp --port 22 --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# * Criar grupos de seguranca para as instâncias NAT, localizadas nas subredes Públicas, liberando acesso para as subredes privadas acessarem a internet

    echo "* Criando grupo de seguranca para instancia NAT, na subrede Pública 04/${availability_zone_4}, liberando acesso para a subrede privada 04"
    security_group_NAT7=$(aws --profile ${profile} ec2 create-security-group --group-name "NAT-${availability_zone_4}-${vpc_name}" --description "Regras de Seguranca para a instancia NAT - ${vpc_name}" --vpc-id ${vpc_id} --query 'GroupId')

    echo "* Alterando Tag Name do grupo de segurança para 'SecGrpNAT7'"
    aws --profile ${profile} ec2 create-tags --resources ${security_group_NAT7} --tags Key=Name,Value="SecGrpNAT7"

    aws --profile ${profile} ec2 authorize-security-group-ingress --group-id ${security_group_NAT7} --protocol -1 --port -1 --cidr ${cidr}.7.0/24

    aws --profile ${profile} ec2 authorize-security-group-ingress --group-id ${security_group_NAT7} --protocol tcp --port 22 --cidr 0.0.0.0/0

echo; echo =================================================================================; echo

# Criar conjunto de opções de DHCP para a vpc. O nome da vpc será usado como nome de domínio

    echo "* Criando conjunto de opções de DHCP para a vpc. O nome da vpc, ${vpc_name}, será usado como nome de domínio"
    dhcp_options_id=$(aws --profile ${profile} ec2 create-dhcp-options --dhcp-configuration "Key=domain-name,Values=${vpc_name}" "Key=domain-name-servers,Values=AmazonProvidedDNS" --query 'DhcpOptions.DhcpOptionsId')

    echo "* Associando conjunto de opções de DHCP com a vpc ${vpc_name}"
    aws --profile ${profile} ec2 associate-dhcp-options --dhcp-options-id ${dhcp_options_id} --vpc-id ${vpc_id}

echo; echo =================================================================================; echo

# Criar domínio interno da VPC

    echo "* Criando domínio interno da VPC ${vpc_name}"
    create_hosted_zone_json_output=$(aws --profile ${profile} route53 create-hosted-zone --name ${vpc_name} --vpc "VPCRegion=us-east-1,VPCId=${vpc_id}" --caller-reference $(date +%Y%m%d-%H%M) --hosted-zone-config "Comment=Dominio privado da vpc ${vpc_name}" --output json)

    hosted_zone_id=$(echo ${create_hosted_zone_json_output} | jq .HostedZone.Id)
    change_info_id=$(echo ${create_hosted_zone_json_output} | jq .ChangeInfo.Id)

    temp="${change_info_id%\"}"
    temp="${temp#\"}"
    change_info_id="${temp}"

    echo -n "* Aguardando pelo INSYNC"
    while state=$(aws --profile ${profile} route53 get-change --id ${change_info_id} --output text --query 'ChangeInfo.Status'); test "${state}" = "PENDING"; do
        echo -n . ; sleep 3;
    done; echo " OK!"

    #temp="${hosted_zone_id%\"}"
    #temp="${temp#\"}"
    #hosted_zone_id="${temp}"

echo; echo =================================================================================; echo

# Criar arquivo ${vpc_name}_vars.sh com o dump das variáveis de ambiente

    dump_file=${vpc_name}_vars.sh

    echo "#!/bin/bash" > ${dump_file}
    echo "" >> ${dump_file}

# Dump das variaveis de ambiente, usadas em outros scripts

    echo export profile=${profile} | tee -a ${dump_file}
    echo export cidr=${cidr} | tee -a ${dump_file}
    echo export vpc_name=${vpc_name} | tee -a ${dump_file}
    echo export vpc_id=${vpc_id} | tee -a ${dump_file}
    echo export internet_gateway_id=${internet_gateway_id} | tee -a ${dump_file}
    echo export public_routetable_id=${public_routetable_id} | tee -a ${dump_file}
    echo export private1_routetable_id=${private1_routetable_id} | tee -a ${dump_file}
    echo export private2_routetable_id=${private2_routetable_id} | tee -a ${dump_file}
    echo export private3_routetable_id=${private3_routetable_id} | tee -a ${dump_file}
    echo export private4_routetable_id=${private4_routetable_id} | tee -a ${dump_file}
    echo export subnetid_1=${subnetid_1} | tee -a ${dump_file}
    echo export subnetid_2=${subnetid_2} | tee -a ${dump_file}
    echo export subnetid_3=${subnetid_3} | tee -a ${dump_file}
    echo export subnetid_4=${subnetid_4} | tee -a ${dump_file}
    echo export subnetid_5=${subnetid_5} | tee -a ${dump_file}
    echo export subnetid_6=${subnetid_6} | tee -a ${dump_file}
    echo export subnetid_7=${subnetid_7} | tee -a ${dump_file}
    echo export subnetid_8=${subnetid_8} | tee -a ${dump_file}
    echo export security_group_NAT1=${security_group_NAT1} | tee -a ${dump_file}
    echo export security_group_NAT3=${security_group_NAT3} | tee -a ${dump_file}
    echo export security_group_NAT5=${security_group_NAT5} | tee -a ${dump_file}
    echo export security_group_NAT7=${security_group_NAT7} | tee -a ${dump_file}
    echo export dhcp_options_id=${dhcp_options_id} | tee -a ${dump_file}
    echo export hosted_zone_id=${hosted_zone_id} | tee -a ${dump_file}

echo; echo =================================================================================
