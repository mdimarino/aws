#!/usr/bin/env bash

# AWS_PROFILE=MSP-Embratel-786154173690 aws organizations list-accounts | jq '.Accounts[] | {Id, Name}'

# Não gerenciamos recursos nas contas:
# * dns-aws 648500770435
# * AWS-Backup-PMC 845241617835
# * MSP-Security-Monitor 956947876752

# for i in Audit-347198027193 \
#          Automation-creation-linked-891377085911 \
#          Log-archive-392101129325 \
#          MSP-Embratel-786154173690 \
#          MSP-Backup-242816904968 \
#          MSP-DirectConnect-875199729706 \
#          MSP-ESD-Communication-Customer-381785467984 \
#          MSP-Management-601156111743 \
#          MSP-Management-02-348920800148 \
#          MSP-Management-03-809830003573 \
#          MSP-Management-embratel.1036514-1 \
#          MSP-Management-embratel.1036514-2 \
#          MSP-Management-embratel.1036514-11
# do
#     echo "=== Credenciais para o profile: ${i} ==="
#     aws sso login --profile ${i}
# done

export AWS_REGION=us-east-1

for i in Audit-347198027193 \
         Automation-creation-linked-891377085911 \
         Log-archive-392101129325 \
         MSP-Embratel-786154173690 \
         MSP-Backup-242816904968 \
         MSP-DirectConnect-875199729706 \
         MSP-ESD-Communication-Customer-381785467984 \
         MSP-Management-601156111743 \
         MSP-Management-02-348920800148 \
         MSP-Management-03-809830003573 \
         EBT-Gestao-322963330866 \
         EBT-Gov-281949160503 \
         Resold-CSP-882591113908 \
         Resold-NO-CSP-605212350047
do
    echo "=== Execução do script para conta: ${i} ==="
    AWS_PROFILE=${i} ./list_resources_arn.py
    sleep 120
done
