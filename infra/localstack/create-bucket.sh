#!/bin/sh
set -e
awslocal s3api head-bucket --bucket "$LAKE__BUCKET" 2>/dev/null || awslocal s3 mb "s3://$LAKE__BUCKET"
