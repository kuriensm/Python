#!/usr/bin/env python
# Author : Kuriens Maliekal
# Date : 7 Dec 2015
# Description : Get consolidated AWS Cloudfront logs from S3 to a file

import boto3
import subprocess
import os
import sys
import getopt
import time
import re

def usage():
	print "Usage: " + sys.argv[0] + " [OPTION].. [FILE]"
	print "Get consolidated AWS Cloudfront logs from S3 to [FILE]."
	print
	print "     --profile [PROFILE]   Specify the AWS profile to connect to"
	print "     -b [BUCKET_NAME]      Specify the S3 bucket name"
	print "     -p [S3_PATH]          Specify the sub-folder(s) path in the S3 bucket where logs are stored (if any)"
	print "     -i [CF_DIST_ID]       Specify the AWS Cloudfront distribution ID"
	print "     -d [DATE]             Specify the date to retrieve the logs in the format YYYY-MM-DD"
	print
	print "Example:"
	print "    " + str(sys.argv[0]) + " --profile=my-aws-account -b sfg-dev-log -p cloudfront-logger -i EZN19MZ573BSM -d 2015-12-07 /home/user/output.txt"

if len(sys.argv) < 2:
	usage()
	sys.exit(1)

try:
	opts, args = getopt.getopt(sys.argv[1:], "b:p:i:d:", ["profile="])
except getopt.GetoptError as err:
	print str(err)
	usage()
	sys.exit(1)

bucket = ''
path = ''
dist = ''
date = ''
profile = 'default'

for o, a in opts:
	if o == '-b':
		bucket = a
	elif o == '-p':
		path = a
	elif o == '-i':
		dist = a
	elif o == '-d':
		date = a
	elif o == '--profile':
		profile = a
	else:
		print "\nInvalid options!\n"
		usage()
		sys.exit(1)

if bucket == '' or dist == '' or date == '':
	print "\nAll required options not specified!\n"
	usage()
	sys.exit(1)

if len(args) < 1:
	print "\nNo file specified to write output!\n"
	usage()
	sys.exit(1)

# Connect to the S3 bucket.
session = boto3.session.Session(profile_name=profile)
client = session.client('s3')

# Get the list of log files to download
prefix = str(path) + "/" + str(dist) + "." + str(date)
response = client.list_objects(Bucket=bucket, Prefix=prefix)
OBJ = []
for i in response["Contents"]:
	OBJ.append(i["Key"])

# Create temporary working directory
ENV_TMP_DIR = os.environ["TMP"]
timestamp = int(time.time())
tmp_dir = str(ENV_TMP_DIR) + "/cflogger_tmp_" + str(timestamp)
try:
	os.makedirs(tmp_dir)
except OSError as exception:
	print str(exception)
	sys.exit(1)

# Download the log files
count=0
for i in OBJ:
	count = count + 1
	path = tmp_dir + "/" + str(count) + '.gz'
	session.resource('s3').meta.client.download_file(bucket, i, path)

# Create output file
output_filename = args[0]
try:
	output = open(output_filename, 'w')
except OSError as exception:
	print str(exception)
	sys.exit(1)

# Magic
for i in range(count):
	i = i + 1
	file_name = str(tmp_dir) + "/" + str(i) + ".gz"
	if os.path.isfile(file_name):
		contents = subprocess.Popen(["zcat", file_name], stdout=subprocess.PIPE).stdout.read()
		split_contents = contents.splitlines(1)
		for j in split_contents:
			if i != 1:
				if j[0] != '#':
					output.write(j)
			elif i == 1:
				line = j.replace('#Fields: ', '')
				output.write(line)
		os.remove(file_name)
try:
	os.rmdir(tmp_dir)
except OSError as exception:
	print str(exception)
	sys.exit(1)