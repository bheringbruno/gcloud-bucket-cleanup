from google.cloud import storage
from google.cloud.storage import constants
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import sys, json, argparse, os
import subprocess as sp

def check_args(parser):
    parser.add_argument("--project", help="a valid project name", type = str.lower)
    parser.add_argument("--slack-token", help="a valid slack token", type = str)
    parser.add_argument("--channel", help="a valid slack channel", type = str)
    parser.add_argument("--dry-run", help="print the execution plan", action='store_true')
    args = parser.parse_args()
    return args

# Add lifecicle policy:
# NEARLINE = Buckets used for reports and metrics can be accessed frequently, with  60 days minimum retention.
# COLDLINE = Buckets for backups used to stored infrequently accessed data, 365 days minimum retention.

def add_lifecycle_policy_reports(bucket_name,storage_class):
    if args.dry_run:
        print('DRY-RUN | Lifecycle policy rule will be updated on bucket: '+bucket_name)
    else:
        storage_client = storage.Client()
        if storage_class == reports_storage_class:
            print('Updating lifecycle policy rule to 60 days on log bucket: '+bucket_name+'.')
            bucket = storage_client.get_bucket(bucket_name)
            bucket.add_lifecycle_delete_rule(age=60)
            bucket.patch()
        else:
            print('Updating lifecycle policy rule to 365 days on backup bucket: '+bucket_name+'.')
            bucket = storage_client.get_bucket(bucket_name)
            bucket.add_lifecycle_delete_rule(age=365)
            bucket.patch()
    change_storage_class(bucket_name,storage_class)

def change_storage_class(bucket_name,storage_class):
    if args.dry_run:
        print('DRY-RUN | StorageClass will be updated to '+storage_class+' on bucket: '+bucket_name)
    else:
        storage_client = storage.Client()
        if storage_class == reports_storage_class:
            reports_bucket.append(bucket_name)
            print('Updating StorageClass to '+storage_class+' on log bucket '+bucket_name+'.')
            bucket = storage_client.get_bucket(bucket_name)
            bucket.storage_class = constants.NEARLINE_STORAGE_CLASS
            bucket.patch()
        else:
            backup_bucket.append(bucket_name)
            print('Updating StorageClass to '+storage_class+' on backup bucket '+bucket_name+'.')
            bucket = storage_client.get_bucket(bucket_name)
            bucket.storage_class = constants.COLDLINE_STORAGE_CLASS
            bucket.patch()

def pending_delete_bucket(bucket_name):
    if args.dry_run:
        print('DRY-RUN | BUCKET LABELED TO PENDING DELETE: '+bucket_name)
    else:
        pending_delete.append(bucket_name)
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        labels = bucket.labels
        labels["status"] = "pending_delete"
        bucket.labels = labels
        bucket.patch()

def delete_bucket(bucket_name):
    if args.dry_run:
        print('DRY-RUN | BUCKET WILL BE REMOVED: '+bucket_name)
    else:
        deleted_buckets.append(bucket_name)
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        bucket.delete()

def notify():
    if args.dry_run:
        print("DRY-RUN | Slack message is disabled on dry-run")
    else:
        if len(without_label) > 0:
            msg = json.dumps([{"text":separator.join(without_label),"color":"warning"}])
            response = client.chat_postMessage(channel=args.channel, text='*Buckets Without Labels - ('+args.project+')*\nReference: https://bitbucket.org/betfair-us/gcloud-bucket-cleanup/src/master/README.md', attachments=msg)
        if len(reports_bucket) > 0:
            msg = json.dumps([{"text":separator.join(reports_bucket),"color":"good"}])
            response = client.chat_postMessage(channel=args.channel, text='*Updated Buckets - ('+args.project+')*\nStorage Class: NEARLINE\nLifecycle Policy: 90 days', attachments=msg)
        if len(backup_bucket) > 0:
            msg = json.dumps([{"text":separator.join(backup_bucket),"color":"good"}])
            response = client.chat_postMessage(channel=args.channel, text='*Updated Buckets - ('+args.project+')*\nStorage Class: COLDLINE\nLifecycle Policy: 365 days', attachments=msg)
        if len(pending_delete) > 0:
            msg = json.dumps([{"text":separator.join(pending_delete),"color":"warning"}])
            response = client.chat_postMessage(channel=args.channel, text='*Pending Delete Buckets - ('+args.project+')*\n', attachments=msg)
        if len(deleted_buckets) > 0:
            msg = json.dumps([{"text":separator.join(deleted_buckets),"color":"danger"}])
            response = client.chat_postMessage(channel=args.channel, text='*Deleted Buckets - ('+args.project+')*\n', attachments=msg)

def main():
    storage_client = storage.Client()
    buckets = storage_client.list_buckets()
    for bucket in buckets:
        if bucket.labels:
            for k, v in bucket.labels.items():
                 if k == "type":
                        if v == "reports":
                            if list(bucket.lifecycle_rules) == []:
                                add_lifecycle_policy_reports(bucket.name,reports_storage_class)
                            else:
                                change_storage_class(bucket.name,reports_storage_class)
                        if v == "backup":
                            if list(bucket.lifecycle_rules) == []:
                                add_lifecycle_policy_reports(bucket.name,backup_storage_class)
                            else:
                                change_storage_class(bucket.name,backup_storage_class)
                        if v == "unused":
                                pending_delete_bucket(bucket.name)
                 if k == "status":
                     if v == "pending_delete":
                         delete_bucket(bucket.name)
        if bucket.labels == {}:
            without_label.append(bucket.name)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = check_args(parser)
    client = WebClient(token=args.slack_token)
    reports_bucket = []
    deleted_buckets = []
    pending_delete = []
    backup_bucket = []
    without_label = []
    backup_storage_class = "COLDLINE"
    reports_storage_class = "NEARLINE"
    separator = '\n'
    login = sp.getoutput('gcloud config set project '+args.project)
    main()
    notify()
