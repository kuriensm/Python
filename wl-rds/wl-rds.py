#!/usr/bin/env python
# Author : Kuriens Maliekal
# Date : 30th Oct 2015
# Description : Script to list RDS databases and any available updates across AWS accounts
# Version : 1.0

# Configuration:
# --------------
# Install boto3 and tabulate python modules using following commands
# pip install boto3
# pip install tabulate
# Use the AWS CLI to configure multiple AWS accounts as per http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html#cli-quick-configuration
# All good to go now.

import boto3
import os
import re
from tabulate import tabulate

main_menu = []
credentials_file = os.path.expanduser("~/.aws/credentials")

try :
	file = open(credentials_file, "r")
except Exception :
	print "AWS credentials file not found"
	exit(1)

creds = file.read()
file.close()
new_creds = creds.splitlines()

for i in new_creds :
	match = re.search('\[(.+?)\]', i)
	if match :
		new_match = re.sub(r'\[|\]','', match.group(0))
		main_menu.append(new_match)

main_menu.insert(0,"ALL")

count = 0
if len(main_menu) <= 0 :
	print "No AWS accounts configured"
	exit(1)

def get_results(profile, dbresponse, updateresponse) :
	servers = []
	for i in updateresponse['PendingMaintenanceActions'] :
		for j in i['PendingMaintenanceActionDetails'] :
			if j['Action'] :
				arn_db_name = i['ResourceIdentifier']
				current_apply_date = j['CurrentApplyDate']
				auto_applied_after = j['AutoAppliedAfterDate']
				forced_apply_date = j['ForcedApplyDate']
				tmp = re.search(r'[^:]*$', arn_db_name)
				db_name = tmp.group(0)
				for k in dbresponse['DBInstances'] :
					if k['DBInstanceIdentifier'] == db_name :
						preferred_maintenance_window = k['PreferredMaintenanceWindow']
						servers.append([ profile, db_name, j['Action'], preferred_maintenance_window, current_apply_date, auto_applied_after, forced_apply_date ])
	return servers

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
profile = main_menu[choice]
servers = []

if profile == "ALL" :
	result = []
	for i in main_menu :
		if not i == "ALL" :
			session = boto3.session.Session(profile_name=i)
			client = session.client('rds')
			updates_response = client.describe_pending_maintenance_actions()
			db_response = client.describe_db_instances()
			result = result + get_results(i, db_response, updates_response)
else :
	session = boto3.session.Session(profile_name=profile)
	client = session.client('rds')
	updates_response = client.describe_pending_maintenance_actions()
	db_response = client.describe_db_instances()
	result = get_results(profile, db_response, updates_response)

result.insert(0, ["Account", "DB Name", "Updates", "Preferred Window", "Apply Date", "Auto Applied After", "Forced Apply Date"])

print
print tabulate(result, headers="firstrow", tablefmt="fancy_grid")
