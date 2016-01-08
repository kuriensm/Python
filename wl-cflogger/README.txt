CFLOGGER
------

Author : Kuriens Maliekal
Date : 7th Dec 2015
Description : Get consolidated AWS Cloudfront logs from S3 to a file
Version : 1.0

USAGE
-----

Usage: ./cflogger.py [OPTION].. [FILE]
Get consolidated AWS Cloudfront logs from S3 to [FILE].

     --profile [PROFILE]   Specify the AWS profile to connect to
     -b [BUCKET_NAME]      Specify the S3 bucket name
     -p [S3_PATH]          Specify the sub-folder(s) path in the S3 bucket where logs are stored (if any)
     -i [CF_DIST_ID]       Specify the AWS Cloudfront distribution ID
     -d [DATE]             Specify the date to retrieve the logs in the format YYYY-MM-DD

Example:
    ./cflogger.py --profile=my-aws-account -b sfg-dev-log -p cloudfront-logger -i EZN19MZ573BSM -d 2015-12-07 /home/user/output.txt