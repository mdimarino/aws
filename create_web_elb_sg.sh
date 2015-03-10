#!/bin/bash

    vpcid=vpc-2997d84c

    aws ec2 create-security-group --group-name prod_web_elb --description  --vpc-id $vpcid 
