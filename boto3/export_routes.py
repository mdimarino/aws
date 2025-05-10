#!/usr/bin/env python

""" exporta rotas de uma tabela de roteamento de um transit gateway """

import boto3
import json

def exporta_rotas_tgw(route_table_id, static_output_file, propagated_output_file):
    ec2 = boto3.client('ec2')
    try:
        # Busca rotas na tabela de rotas do Transit Gateway
        response = ec2.search_transit_gateway_routes(
            TransitGatewayRouteTableId=route_table_id,
            Filters=[
                {'Name': 'state', 'Values': ['active', 'blackhole']}
            ]
        )
        
        routes = response.get('Routes', [])
        print(f"{len(routes)} rota(s) na tabela {route_table_id} encontrada(s).")

        # Separate routes by type
        static_routes = [route for route in routes if route.get('Type') == 'static']
        propagated_routes = [route for route in routes if route.get('Type') == 'propagated']

        # Save static routes to a file
        with open(static_output_file, 'w') as static_file:
            json.dump(static_routes, static_file, indent=4)
        print(f"Rotas estáticas exportadas para {static_output_file}")

        # Save propagated routes to a file
        with open(propagated_output_file, 'w') as propagated_file:
            json.dump(propagated_routes, propagated_file, indent=4)
        print(f"Rotas propagadas exportadas para {propagated_output_file}")

    except Exception as e:
        print(f"Erro ao exportar rotas: {e}")


if __name__ == "__main__":
    route_table_id = input("Entre com o ID da tabela de roteamento do Transit Gateway: ")
    static_output_file = input("Entre com o nome do arquivo de output das rotas estáticas (e.g., rotas_estaticas.json): ")
    propagated_output_file = input("Entre com o nome do arquivo de output das rotas propagadas (e.g., rotas_propagadas.json): ")
    exporta_rotas_tgw(route_table_id, static_output_file, propagated_output_file)

# tgw-rtb-0bb2ebd73bf274fdc
