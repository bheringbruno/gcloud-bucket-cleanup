## Gcloud Cleanup Buckets
--------------------------------------------------------

This repository consists of creating a CronJob in Kubernetes to change the settings of a bucket, such as retention policy and storage class.

The change is based on the labels added to each bucket, there are 3 labels that trigger different actions:

### Storage Class Type Used:
**NEARLINE** : Buckets used for reports and metrics, can be accessed frequently.

**COLDLINE**: Buckets used for backups to stored infrequently accessed data.
#

--------------------------------------------------------
### - Reports Buckets:
#### label:
```
{
    "type" : "reports" 
}
```

#### Action:
All bucket with label key "type" and value "reports", will be applied rotation policy with 90 days and change the storage class to NEARLINE.

Also will send a notification to a Slack Channel.

--------------------------------------------------------

### - Backup Buckets :
#### label:
```
{
    "type" : "backup" 
}
```

#### Action:
All bucket with label key "type" and value "backup", will be applied rotation policy with 365 days and change the storage class to COLDLINE.

Also will send a notification to a Slack Channel.

--------------------------------------------------------

### - Unused Buckets :
#### label:
```
{
    "type" : "unused" 
}
```

#### Action:
All buckets with the label key "type" and the value "unused", will be labeled pending delete and deleted on the next execution. 
Also will send a notification to a Slack channel

--------------------------------------------------------
## Other Labels:
You can also add another label, for example:
```
{
    "type" : "service" 
}
```
or
```
{
    "type" : "sqlserver" 
}
```
#### For now, this lables aren't used by script, but all buckets must be labeled to avoid notified by Slack.

--------------------------------------------------------

## Usage:
#

```
python3 main.py --help

usage: main.py [-h] [--project PROJECT] [--channel CHANNEL] [--slack-token SLACK_TOKEN] [--dry-run]

optional arguments:
  -h, --help            show this help message and exit
  --project PROJECT     a valid project name
  --channel CHANNEL     slack channel id
  --slack-token SLACK_TOKEN
                        slack bot token
  --dry-run             print the command without run
```

### Default:  
#
```
python3 main.py --slack-token $SLACK_API_TOKEN --channel $CHANNEL_ID  --project tvg-network
```

## Slack Config:
#
```
Default Channel: #gcloud-cleanup
Default bot user: gcloud-bot-ops
```