import time
import json
import boto3
import os
import datetime

statusCode=200

def lambda_handler(event, context):
  try:
    # Initialize session and client
    global statusCode
    src_acct=event["Source_Account_Id"]
    tgt_acct=event["Target_Account_Id"]
    repo=event["Repo"]
    region=event["Region"]
    tagkey01=event["TargetAppTag"]["SERVER_ENV"]
    tagvalue01=event["TargetAppTag"]["SERVER_ENV_VALUE"]
    tagkey02=event["TargetAppTag"]["SERVER_NAME"]
    tagvalu02=event["TargetAppTag"]["SERVER_NAME_VALUE"]
    src_db=event["Source"]
    tgt_db=event["Target"]
    
    sts_connection = boto3.client('sts')
    acct_src = sts_connection.assume_role(
             RoleArn="arn:aws:iam::"+tgt_acct+":role/EbizClone-CrossAccountSharing",
             RoleSessionName="EbizClone-CrossAccountSharing_Src"
             )
         
    ACCESS_KEY = acct_src['Credentials']['AccessKeyId']
    SECRET_KEY = acct_src['Credentials']['SecretAccessKey']
    SESSION_TOKEN = acct_src['Credentials']['SessionToken']

    ec2_client = boto3.client(
                 "ec2",
                 region_name=region,
                 aws_access_key_id=ACCESS_KEY,
                 aws_secret_access_key=SECRET_KEY,
                 aws_session_token=SESSION_TOKEN
                 )
                 
    ec2_resource = boto3.resource(
                 "ec2",
                 region_name=region,
                 aws_access_key_id=ACCESS_KEY,
                 aws_secret_access_key=SECRET_KEY,
                 aws_session_token=SESSION_TOKEN
                 )
                 
    ssm = boto3.client(
                 "ssm",
                 region_name=region,
                 aws_access_key_id=ACCESS_KEY,
                 aws_secret_access_key=SECRET_KEY,
                 aws_session_token=SESSION_TOKEN
                 )
    
    
    reservations = ec2_client.describe_instances(Filters=[
          {
            "Name": "instance-state-name",
            "Values": ["running"],
            "Name": "tag:"+tagkey01,
            "Values": [tagvalue01],
            "Name": "tag:"+tagkey02,
            "Values": [tagvalu02]
          }
        ]).get("Reservations")

    
    if not reservations:
       raise Exception ("Issue in Fetching EC2 Instance Check if Tagging is correct")
        
    instance_id=""   
    for reservation in reservations:
        for instance in reservation["Instances"]:
             if not instance:
                raise Exception ("Issue in Identifying EC2 Instance")
             instance_id = instance["InstanceId"]
             response = ssm.send_command(
             InstanceIds=[instance_id],
             DocumentName="AWS-RunShellScript",
             Parameters={
               "commands": ["runuser -l  applmgr -c 'cd clone_auto; sh appctl -source_db "+src_db+" -target_db "+tgt_db+" -action TARGET_PREP -phase START_APPS'"]
            },  # Command to Start APP Service
        ) 
        
        # fetching command id for the output
        command_id = response["Command"]["CommandId"]
        
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
           raise Exception ("Issue in Starting App Services")

        return {
                 'StatusCode': statusCode,
                 'CommandId' : command_id,
                 'InstanceId': instance_id
               }

  except Exception as e:
    statusCode=201
    print('***Error - Failed to run ssm send command to start application services.')
    print(type(e), ':', e)
    return {
              'StatusCode': statusCode,
              'CommandId' : "NULL",
              'InstanceId': "NULL" 
           }
    

