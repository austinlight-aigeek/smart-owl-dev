#!/bin/bash
aws dynamodb create-table \
   --table-name openai-call-log \
   --attribute-definitions AttributeName=id,AttributeType=S \
   --key-schema AttributeName=id,KeyType=HASH \
   --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
   --region us-west-2 \
   --endpoint-url http://localhost:8000 \
   --profile local
