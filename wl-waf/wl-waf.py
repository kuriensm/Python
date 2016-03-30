#!/usr/bin/env python
# Author : Kuriens Maliekal
# Date : 4 March 2016
# Description : Get list of client IP addresses that match a specific regexp on AWS WAF and block them based on count
# Version : 1.0

import boto3
import time
import re

## Variables to adjust ##

# Specify the log file to write the logs to
log_file = "/var/log/waf.log"

# The Web ACL ID in WAF using "aws waf list-web-acls --limit 5"
webaclid = "5afd520d-644d-49b0-b59b-783f3925f206"

# The WAF rule ID using "aws waf list-rules --limit 5"
ruleid = "93e94878-3ac0-4d73-a5a9-050dda3ec52f"

# The IP set in WAF to add blocked IP addresses to using "aws waf list-ip-sets --limit 5"
ipset = "87d64363-c917-4c5e-9596-f4d43a0e34d0"

# The regexp to match in the sampled requests
regexp = "^/catalogsearch/result/\?q=[0-9]{9,}$"

#The max number of matched requests allowed before the /24 IP range is blocked in WAF
maxrequests = 5

## No changes required below this line ##

client = boto3.client('waf')

end_time = int(time.time()) - 10
start_time = end_time - 130

response = client.get_sampled_requests(
		WebAclId = webaclid,
		RuleId = ruleid,
		TimeWindow = {
			'StartTime': start_time,
			'EndTime': end_time
		},
		MaxItems = 100
	)

matchedips = []
finalips = []

pattern = re.compile("[0-9]*\.[0-9]*\.[0-9]*")
for i in response['SampledRequests']:
	if re.match(regexp, i['Request']['URI']):
		clientip = str(pattern.search(i['Request']['ClientIP']).group(0)) + ".0/24"
		matchedips.append(clientip)

sortedips = sorted(set(matchedips))
for i in sortedips:
	count = 0
	for j in matchedips:
		if j == i:
			count = count + 1
	if count > maxrequests:
		finalips.append(i)

print finalips

fh = open(log_file, 'a')
for i in finalips:
	token = client.get_change_token()
	response = client.update_ip_set(
			IPSetId = ipset,
			ChangeToken = token['ChangeToken'],
			Updates = [
				{
					'Action': 'INSERT',
					'IPSetDescriptor': {
						'Type': 'IPV4',
						'Value': i
					}
				}
			]
		)
	now = time.localtime(time.time())
	msg = time.strftime("%y/%m/%d %H:%M", now) + " - " + i + " requested for blocking in WAF\n"
	fh.write(msg)
fh.close()