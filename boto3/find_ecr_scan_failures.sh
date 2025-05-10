#!/usr/bin/bash

#!/bin/bash

# Get a list of all repositories
repositories=$(aws ecr describe-repositories --query 'repositories[*].repositoryName' --output text)

# Loop through each repository
for repo in $repositories; do
    echo "Repository: $repo"
    
    # Get a list of images in the repository
    images=$(aws ecr list-images --repository-name $repo --query 'imageIds[*]' --output json)

    # Loop through each image and check its scan status
    for image in $(echo "$images" | jq -r '.[] | @base64'); do
        _jq() {
            echo ${image} | base64 --decode | jq -r ${1}
        }

        imageDigest=$(_jq '.imageDigest')

        # Get the scan status of the image
        scanStatus=$(aws ecr describe-image-scan-findings --repository-name $repo --image-id imageDigest=$imageDigest --query 'imageScanFindings.imageScanStatus.status' --output text)

        # If the scan status is FAILED, print the image details
        if [ "$scanStatus" == "FAILED" ]; then
            echo "  Image Digest: $imageDigest"
            echo "  Scan Status: $scanStatus"
        fi
    done
done
