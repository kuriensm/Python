#!/usr/bin/env python
# Author : Kuriens Maliekal
# Date : 4 March 2016
# Description : Get list of client IP addresses that match a specific regexp on AWS WAF and block them based on count
# Version : 1.0

import boto3
import re
import logging
import time

## Variables to adjust ##

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

#SNS Topic ARN to send WAF notifications to
snsarn = "arn:aws:sns:ap-southeast-2:020071770732:waf-notifications"

## No changes required below this line ##

client = boto3.client('waf')
sns_client = boto3.client('sns', region_name="ap-southeast-2")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def waf_ddos(event, context):
	for x in range(1,5):
		print "Running iteration number " + str(x)
		end_time = int(time.time()) - 10
		start_time = end_time - 70

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
		msg = ""

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
			msg = msg + i + "\n"
			logger.info(msg)
		if len(finalips) == 0:
			msg = "No IP addresses were found matching the DDOS pattern"
			logger.info(msg)
		else:
		    sns_response = sns_client.publish(
		    	TopicArn = snsarn,
		        Message = "The following IP ranges were blocked in WAF.\n\n" + msg + "\n- Special K",
		        Subject = "Pushys DDOS notification",
		    )
		time.sleep(60)