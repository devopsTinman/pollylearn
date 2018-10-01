import boto3
import StringIO
import zipfile
import mimetypes

def lambda_handler(event, context):


    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:250231550228:deployPortfolioTopic')

    try:

        job = event.get("CodePipeline.job")

        location = {
            "bucketName": "pollylearnbuild.allbeelean.com",
            "objectKey": "pollylearnbuild.zip"
        }

        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "PollylearnBuild":
                    location = artifact["location"]["s3Location"]


        print "Building porfolio from " + str(location)

        s3 = boto3.resource('s3')

        portfolio_bucket = s3.Bucket('pollylearn.allbeelean.com')
        build_bucket = s3.Bucket(location["bucketName"])


        portfolio_zip = StringIO.StringIO()
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm,
                    ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        print "Job done!"
        topic.publish(Subject='Polly Learn Deployed', Message='Polly Learn Deployed Successfully')
        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId=job["id"])

    except:
        topic.publish(Subject='Polly Learn Deploy Failed', Message='Polly Learn Did not deploy Successfully')
        raise
    return 'Hello from Lambda'
