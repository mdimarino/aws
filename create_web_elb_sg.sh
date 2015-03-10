#!/bin/bash

echo; echo =================================================================================; echo

    echo "Carregando variáveis de ambiente"
    . ./vars.sh

echo; echo =================================================================================; echo

    echo "Criando grupo de segurança prod_web_elb"
    security_group_web_elb=$(aws ec2 create-security-group --group-name prod-casamento-elb --description "Load Balance Blog Casamento" --vpc-id $vpcid --query 'GroupId')

    echo "Criando regra no grupo de segurança prod-web-elb liberando acesso na porta 80 com origem 0.0.0.0/0"    
    aws ec2 authorize-security-group-ingress --group-id $security_group_web_elb --protocol tcp --port 80 --cidr 0.0.0.0/0

    
echo; echo =================================================================================; echo

    DNSName=$(aws elb create-load-balancer --load-balancer-name prod-casamento-elb --listeners Protocol=HTTP,LoadBalancerPort=80,InstanceProtocol=HTTP,InstancePort=80 --subnets $subnetid_0 $subnetid_2 $subnetid_4 $subnetid_6 --security-groups $security_group_web_elb)
    
    echo DNSName=$DNSName
