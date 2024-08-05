import boto3
import json
import sys
import time
from django.conf import settings
from . import amz_textract_scb_cc as get_result_scb_cc


class ProcessType:
    DETECTION = 1
    ANALYSIS = 2


class DocumentProcessor:
    jobId = ""
    region_name = ""

    roleArn = ""
    bucket = ""
    document = ""

    sqsQueueUrl = ""
    snsTopicArn = ""
    processType = ""

    def __init__(self, role, bucket, document, region):
        self.roleArn = role
        self.bucket = bucket
        self.document = document
        self.region_name = region

        self.textract = boto3.client("textract", region_name=self.region_name)
        self.sqs = boto3.client("sqs", region_name=self.region_name)
        self.sns = boto3.client("sns", region_name=self.region_name)

    def ProcessDocument(self, type):
        jobFound = False

        self.processType = type
        validType = False

        # Determine which type of processing to perform
        if self.processType == ProcessType.DETECTION:
            response = self.textract.start_document_text_detection(
                DocumentLocation={
                    "S3Object": {"Bucket": self.bucket, "Name": self.document}
                },
                NotificationChannel={
                    "RoleArn": self.roleArn,
                    "SNSTopicArn": self.snsTopicArn,
                },
            )
            print("Processing type: Detection")
            validType = True

        # For document analysis, select which features you want to obtain with the FeatureTypes argument
        if self.processType == ProcessType.ANALYSIS:
            print("Starting analysis of document: ")

            response = self.textract.start_document_analysis(
                DocumentLocation={
                    "S3Object": {"Bucket": self.bucket, "Name": self.document}
                },
                FeatureTypes=["TABLES", "FORMS"],
                NotificationChannel={
                    "RoleArn": self.roleArn,
                    "SNSTopicArn": self.snsTopicArn,
                },
            )
            print("Processing type: Analysis")
            validType = True

        if validType == False:
            print("Invalid processing type. Choose Detection or Analysis.")
            return

        print("Start Job Id: " + response["JobId"])
        dotLine = 0
        while jobFound == False:
            print("Getting SQS Response: ")
            sqsResponse = self.sqs.receive_message(
                QueueUrl=self.sqsQueueUrl,
                MessageAttributeNames=["ALL"],
                MaxNumberOfMessages=10,
            )

            print("Checking if SQS Response is True: ")

            if sqsResponse:
                print("SQS Response is True: ")
                if "Messages" not in sqsResponse:
                    print("Messages is not in sqsResponse")
                    if dotLine < 40:
                        print(".", end="")
                        dotLine = dotLine + 1
                    else:
                        print()
                        dotLine = 0
                    sys.stdout.flush()
                    time.sleep(5)
                    continue

                print("Messages is in sqsResponse")

                for message in sqsResponse["Messages"]:
                    notification = json.loads(message["Body"])
                    textMessage = json.loads(notification["Message"])
                    print("JOB ID: ", textMessage["JobId"])
                    print("STATUS: ", textMessage["Status"])
                    job_id = textMessage["JobId"]
                    if str(textMessage["JobId"]) == response["JobId"]:
                        print("Matching Job Found:" + textMessage["JobId"])
                        jobFound = True

                        # TEST: Replace GetResult with your custom get_document_analysis function
                        # self.GetResults(textMessage["JobId"])

                        # WARNING: Calling from another file
                        # TODO: Need to reactor all of this shit
                        data_frames_dicts = get_result_scb_cc.get_doc_analysis_results(
                            textMessage["JobId"]
                        )

                        self.sqs.delete_message(
                            QueueUrl=self.sqsQueueUrl,
                            ReceiptHandle=message["ReceiptHandle"],
                        )
                        return data_frames_dicts
                    else:
                        print(
                            "Job didn't match:"
                            + str(textMessage["JobId"])
                            + " : "
                            + str(response["JobId"])
                        )

                        # Delete the unknown message. Consider sending to dead letter queue
                        self.sqs.delete_message(
                            QueueUrl=self.sqsQueueUrl,
                            ReceiptHandle=message["ReceiptHandle"],
                        )
                        return False, None

    def CreateTopicandQueue(self):
        millis = str(int(round(time.time() * 1000)))

        # Create SNS topic
        print("Creating topic")

        snsTopicName = "AmazonTextractTopic" + millis

        topicResponse = self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse["TopicArn"]

        print("Topic created: ")

        print("Creating queue")

        # create SQS queue
        sqsQueueName = "AmazonTextractQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)["QueueUrl"]

        print("Queue created")

        attribs = self.sqs.get_queue_attributes(
            QueueUrl=self.sqsQueueUrl, AttributeNames=["QueueArn"]
        )["Attributes"]

        sqsQueueArn = attribs["QueueArn"]

        # Subscribe SQS queue to SNS topic
        print("Subscribing queue to topic")

        self.sns.subscribe(
            TopicArn=self.snsTopicArn, Protocol="sqs", Endpoint=sqsQueueArn
        )

        # Authorize SNS to write SQS queue
        policy = """{{
        "Version":"2012-10-17",
        "Statement":[
            {{
            "Sid":"MyPolicy",
            "Effect":"Allow",
            "Principal" : {{"AWS" : "*"}},
            "Action":"SQS:SendMessage",
            "Resource": "{}",
            "Condition":{{
                "ArnEquals":{{
                "aws:SourceArn": "{}"
                }}
            }}
            }}
        ]
        }}""".format(sqsQueueArn, self.snsTopicArn)

        response = self.sqs.set_queue_attributes(
            QueueUrl=self.sqsQueueUrl, Attributes={"Policy": policy}
        )
        print("Topic and Queue subscribeed successfully, response: ", response)

    def DeleteTopicandQueue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)

    # Display information about a block
    def DisplayBlockInfo(self, block):
        print("Block Id: " + block["Id"])
        print("Type: " + block["BlockType"])
        if "EntityTypes" in block:
            print("EntityTypes: {}".format(block["EntityTypes"]))

        if "Text" in block:
            print("Text: " + block["Text"])

        if block["BlockType"] != "PAGE" and "Confidence" in str(block["BlockType"]):
            print("Confidence: " + "{:.2f}".format(block["Confidence"]) + "%")

        print("Page: {}".format(block["Page"]))

        if block["BlockType"] == "CELL":
            print("Cell Information")
            print("\tColumn: {} ".format(block["ColumnIndex"]))
            print("\tRow: {}".format(block["RowIndex"]))
            print("\tColumn span: {} ".format(block["ColumnSpan"]))
            print("\tRow span: {}".format(block["RowSpan"]))

            if "Relationships" in block:
                print("\tRelationships: {}".format(block["Relationships"]))

        if ("Geometry") in str(block):
            print("Geometry")
            print("\tBounding Box: {}".format(block["Geometry"]["BoundingBox"]))
            print("\tPolygon: {}".format(block["Geometry"]["Polygon"]))

        if block["BlockType"] == "SELECTION_ELEMENT":
            print("    Selection element detected: ", end="")
            if block["SelectionStatus"] == "SELECTED":
                print("Selected")
            else:
                print("Not selected")

        if block["BlockType"] == "QUERY":
            print("Query info:")
            print(block["Query"])

        if block["BlockType"] == "QUERY_RESULT":
            print("Query answer:")
            print(block["Text"])

    def GetResults(self, jobId):
        maxResults = 1000
        paginationToken = None
        finished = False

        while finished == False:
            response = None

            if self.processType == ProcessType.ANALYSIS:
                if paginationToken == None:
                    response = self.textract.get_document_analysis(
                        JobId=jobId, MaxResults=maxResults
                    )
                else:
                    response = self.textract.get_document_analysis(
                        JobId=jobId, MaxResults=maxResults, NextToken=paginationToken
                    )

            if self.processType == ProcessType.DETECTION:
                if paginationToken == None:
                    response = self.textract.get_document_text_detection(
                        JobId=jobId, MaxResults=maxResults
                    )
                else:
                    response = self.textract.get_document_text_detection(
                        JobId=jobId, MaxResults=maxResults, NextToken=paginationToken
                    )

            blocks = response["Blocks"]
            print("Detected Document Text")
            print("Pages: {}".format(response["DocumentMetadata"]["Pages"]))

            # TEST: remove # below - Display block information
            # for block in blocks:
            #     self.DisplayBlockInfo(block)
            #     print()
            #     print()

            if "NextToken" in response:
                paginationToken = response["NextToken"]
            else:
                finished = True

    def GetResultsDocumentAnalysis(self, jobId):
        maxResults = 1000
        paginationToken = None
        finished = False

        while finished == False:
            response = None
            if paginationToken == None:
                response = self.textract.get_document_analysis(
                    JobId=jobId, MaxResults=maxResults
                )
            else:
                response = self.textract.get_document_analysis(
                    JobId=jobId, MaxResults=maxResults, NextToken=paginationToken
                )

                # Get the text blocks
            blocks = response["Blocks"]
            print("Analyzed Document Text")
            print("Pages: {}".format(response["DocumentMetadata"]["Pages"]))
            # Display block information
            for block in blocks:
                self.DisplayBlockInfo(block)
                print()
                print()

                if "NextToken" in response:
                    paginationToken = response["NextToken"]
                else:
                    finished = True


def main(document):
    roleArn = settings.AWS_ROLE_ARN
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    region_name = settings.AWS_REGION

    analyzer = DocumentProcessor(roleArn, bucket, document, region_name)
    analyzer.CreateTopicandQueue()
    result = analyzer.ProcessDocument(ProcessType.ANALYSIS)  # set to run analysis
    analyzer.DeleteTopicandQueue()

    return result
