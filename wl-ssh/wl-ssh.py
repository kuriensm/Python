#!/usr/bin/env python
# Author : Kuriens Maliekal
# Date : 20th Oct 2015
# Description : Script to SSH into running instances on various AWS accounts
# Version : 1.0

# Configuration:
# --------------
# Install boto3 python module using the command "pip install boto3"
# Use the AWS CLI to configure multiple AWS accounts as per http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html#cli-quick-configuration
# Ensure you have all the SSH keys under "~/keys" directory with 400 unix permissions
# All good to go now.

import boto3
import os
import re
import subprocess

# Set a default SSH user
default_user = "ec2-user"

# AWS credentials file
credentials_file = os.path.expanduser("~/.aws/credentials")

main_menu = []

# Check if the AWS credentials file exist
try :
	file = open(credentials_file, "r")
except Exception :
	print "AWS credentials file not found"
	exit(1)

# Read the AWS credentials file and get the accounts list
creds = file.read()
file.close()
new_creds = creds.splitlines()
for i in new_creds :
	match = re.search('\[(.+?)\]', i)
	if match :
		main_menu.append(match.group(0))

# Printing the list of AWS profiles
count = 0
if len(main_menu) <= 0 :
	print "No AWS accounts configured"
	exit(1)
print
print "*************"
print "AWS Accounts"
print "*************"
print ""
for i in range(len(main_menu)) :
	print "%s. %s" % (i+1, main_menu[i])
print ""
choice = raw_input("Enter the choice: ")
if int(choice) > len(main_menu) :
	print "Invalid choice"
	exit(1)
choice = int(choice) - 1
profile = re.sub(r'\[|\]',"", main_menu[choice])

# Setting environment variable for the specific AWS account
os.environ["AWS_PROFILE"] = profile

# Servers list - will be a dictionary array
servers = []

# Boto magic
client = boto3.client('ec2')
response = client.describe_instances()
for i in response["Reservations"] :
	for j in i["Instances"] :
		if j["State"]["Code"] == 16 :
			if 'Tags' in j and "KeyName" in j :
				for k in j["Tags"] :
					if k["Key"] == "Name" :
						if "PublicIpAddress" in j :
							pub_ip = j["PublicIpAddress"]
							if 'VpcId' in j :
								tmp = {"Name" : k["Value"], "Key" : j["KeyName"], "IP" : pub_ip, "Flag" : 0, "VPC" : j["VpcId"]}
							else :
								tmp = {"Name" : k["Value"], "Key" : j["KeyName"], "IP" : pub_ip, "Flag" : 0, "VPC" : ""}
							servers.append(tmp)
						else :
							pri_ip = j["PrivateIpAddress"]
							if 'VpcId' in j :
								tmp = {"Name" : k["Value"], "Key" : j["KeyName"], "IP" : pri_ip, "Flag" : 1, "VPC" : j["VpcId"]}
							else :
								tmp = {"Name" : k["Value"], "Key" : j["KeyName"], "IP" : pri_ip, "Flag" : 1, "VPC" : ""}
							servers.append(tmp)

# Print server list.
if len(servers) <= 0 :
	print "No running servers found in this account."
	exit(0)
print ""
print "*************"
print "EC2 Instances"
print "*************"
print ""
for i in range(len(servers)) :
	print "%s. %s [%s]" % (i+1, servers[i]["Name"], servers[i]["IP"])
print ""
choice = raw_input("Enter your choice: ")
if int(choice) > len(servers) :
	print "Invalid choice"
	exit(1)
choice = int(choice) - 1
print ""

# If the server does not have a public IP
if servers[choice]["Flag"] == 1 :
	flag = 1
	vpc = servers[choice]["VPC"]
	pub_server = {}
	for i in servers :
		if i["Flag"] == 0 and i["VPC"] == vpc :
			flag = 0
			pub_server = i
			break
	if flag == 1 :
		print "No servers with public IP address in the same VPC"
		exit(1)
	else :
		print ""
		user1 = raw_input("Enter public SSH username for " + str(pub_server["Name"]) + " [" + default_user + "]: ") or default_user
		user2 = raw_input("Enter private SSH username for " + str(servers[choice]["Name"]) + " [" + default_user + "]: ") or default_user
		scp_command = "scp -i ~/keys/" + pub_server["Key"] + ".pem " + "~/keys/" + servers[choice]["Key"] + ".pem " + user1 + "@" + pub_server["IP"] + ":~"
		ssh_command = "ssh -i ~/keys/" + pub_server["Key"] + ".pem -A -t " + user1 + "@" + pub_server["IP"] + " ssh -A -o StrictHostKeyChecking=no -i ~" + user1 + "/" + servers[choice]["Key"] + ".pem " + user2 + "@" + servers[choice]["IP"]
		subprocess.call(scp_command, shell=True)
		subprocess.call(ssh_command, shell=True)
else :
	user = raw_input("Enter SSH username for " + str(servers[choice]["Name"]) + " [" + default_user + "]: ") or default_user
	ssh_command = "ssh -i ~/keys/" + servers[choice]["Key"] + ".pem " + user + "@" + servers[choice]["IP"]
	subprocess.call(ssh_command, shell=True)