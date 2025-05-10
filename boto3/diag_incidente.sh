#!/bin/bash

echo "--------------------------------------------------"
echo ">>> INÍCIO DO DIAGNÓSTICO DE INCIDENTE DE SEGURANÇA"
echo "--------------------------------------------------"
# Variáveis
USERS_SUSPEITOS=("aws-app-wstt" "app_ocr")
IP_SUSPEITO="92.223.85.228"
REGION="us-east-1"
DATA_REF="$(date -u -d 'yesterday 22:00' +%Y-%m-%dT22:00:00Z)"
echo ""
echo "[1] Verificando eventos recentes dos usuários suspeitos desde as 22h de ontem..."
for USER in "${USERS_SUSPEITOS[@]}"; do
 echo ">>> Usuário: $USER"
 aws cloudtrail lookup-events \
   --lookup-attributes AttributeKey=Username,AttributeValue=$USER \
   --start-time "$DATA_REF" \
   --max-results 20 \
   --output table
done
echo ""
echo "[2] Buscando eventos recentes do IP suspeito: $IP_SUSPEITO"
aws cloudtrail lookup-events \
 --lookup-attributes AttributeKey=SourceIPAddress,AttributeValue=$IP_SUSPEITO \
 --start-time "$DATA_REF" \
 --max-results 20 \
 --output table
echo ""
echo "[3] Checando usuários IAM com Access Keys ATIVAS..."
aws iam list-users --query 'Users[*].UserName' --output text | tr '\t' '\n' | while read USERNAME; do
 KEY_STATUS=$(aws iam list-access-keys --user-name $USERNAME \
   --query 'AccessKeyMetadata[?Status==`Active`].AccessKeyId' --output text)
 if [[ ! -z "$KEY_STATUS" ]]; then
   echo ">>> Usuário: $USERNAME - Chave(s) ATIVA(S): $KEY_STATUS"
 fi
done
echo ""
echo "[4] Verificando quais usuários NÃO possuem MFA..."
for USER in $(aws iam list-users --query "Users[*].UserName" --output text); do
 MFA_COUNT=$(aws iam list-mfa-devices --user-name $USER --query "length(MFADevices)")
 if [[ "$MFA_COUNT" == "0" ]]; then
   echo ">>> ALERTA: Usuário sem MFA: $USER"
 fi
done
echo ""
echo "[5] Procurando permissões amplas (Admin/FullAccess/*)..."
for USER in $(aws iam list-users --query "Users[*].UserName" --output text); do
 POLICIES=$(aws iam list-attached-user-policies --user-name $USER --query 'AttachedPolicies[*].PolicyName' --output text)
 if echo "$POLICIES" | grep -Ei 'admin|fullaccess|\*'; then
   echo ">>> Usuário $USER com política potencialmente perigosa: $POLICIES"
 fi
done
echo ""
echo "[6] Checando usuários criados recentemente..."
aws cloudtrail lookup-events \
 --lookup-attributes AttributeKey=EventName,AttributeValue=CreateUser \
 --start-time "$DATA_REF" \
 --max-results 10 \
 --output table
echo ""
echo "[7] Checando usuários deletados recentemente..."
aws cloudtrail lookup-events \
 --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteUser \
 --start-time "$DATA_REF" \
 --max-results 10 \
 --output table
echo ""
echo "[8] Listando roles com políticas inline perigosas..."
for ROLE in $(aws iam list-roles --query 'Roles[*].RoleName' --output text); do
 INLINE=$(aws iam list-role-policies --role-name $ROLE --output text)
 if [[ ! -z "$INLINE" ]]; then
   echo ">>> Role com política inline: $ROLE -> $INLINE"
 fi
done
echo ""
echo "[9] Verificando alterações críticas nas 2h anteriores ao incidente..."
# Assume que incidente foi às 23:45 de ontem
START_HORA="2025-05-01T21:45:00Z"
END_HORA="2025-05-01T23:45:00Z"
for EVENT in DeleteUser DeleteAccessKey PutUserPolicy AttachUserPolicy UpdateAssumeRolePolicy; do
 echo ">>> Evento: $EVENT"
 aws cloudtrail lookup-events \
   --start-time "$START_HORA" \
   --end-time "$END_HORA" \
   --lookup-attributes AttributeKey=EventName,AttributeValue=$EVENT \
   --max-results 10 \
   --output table
done
echo ""
echo "--------------------------------------------------"
echo ">>> DIAGNÓSTICO CONCLUÍDO – Avalie os itens com ALERTA"
echo "--------------------------------------------------"