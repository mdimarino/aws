#!/usr/bin/env python

""" importa rotas para uma tabela de roteamento de um transit gateway """

import boto3
import json

def importa_rotas_tgw(route_table_id, input_file):
    ec2 = boto3.client('ec2')
    try:
        with open(input_file, 'r') as file:
            routes = json.load(file)
        
        print(f"{len(routes)} rota(s) no arquivo {input_file} encontrada(s).")
        
        for route in routes:
            destination = route.get('DestinationCidrBlock')
            target = route.get('TransitGatewayAttachments', [{}])[0].get('TransitGatewayAttachmentId')
            
            if not destination:
                print("Pulando rotas sem DestinationCidrBlock.")
                continue
            
            if target:
                ec2.create_transit_gateway_route(
                    TransitGatewayRouteTableId=route_table_id,
                    DestinationCidrBlock=destination,
                    TransitGatewayAttachmentId=target
                )
                print(f"Rota adicionada: {destination} -> {target}")
            else:
                ec2.create_transit_gateway_route(
                    TransitGatewayRouteTableId=route_table_id,
                    DestinationCidrBlock=destination,
                    Blackhole=True
                )
                print(f"Rota blackhole adicionada: {destination}")
        
        print(f"Rotas importadas na tabela de roteamento {route_table_id}.")
    except Exception as e:
        print(f"Erro importando rotas: {e}")

if __name__ == "__main__":
    route_table_id = input("Entre com o ID da tabela de roteamento do Transit Gateway: ")
    input_file = input("Entre com o nome do arquivo de rotas: ")
    importa_rotas_tgw(route_table_id, input_file)

# tgw-rtb-0b6487e790db977ae