import boto3
from botocore.exceptions import ClientError
import logging
from django.conf import settings
import time
import pandas as pd
from datetime import datetime


def start_document_analysis_bs(document):
    """Start a document analysis job on an S4 object
    This function creates a quque, sns topic, and subscribes the queue to the topic
    and returns the job_id of the document analysis job
    """
    sqs = boto3.client("sqs")
    sns = boto3.client("sns")
    print(sqs)
    print(sns)

    millis = str(int(round(time.time() * 1000)))

    # Create SNS topic
    snsTopicName = "AmazonTextractTopic" + millis

    topicResponse = sns.create_topic(Name=snsTopicName)
    snsTopicArn = topicResponse["TopicArn"]

    # create SQS queue
    sqsQueueName = "AmazonTextractQueue" + millis
    sqs.create_queue(QueueName=sqsQueueName)
    sqsQueueUrl = sqs.get_queue_url(QueueName=sqsQueueName)["QueueUrl"]

    attribs = sqs.get_queue_attributes(
        QueueUrl=sqsQueueUrl, AttributeNames=["QueueArn"]
    )["Attributes"]

    sqsQueueArn = attribs["QueueArn"]

    # Subscribe SQS queue to SNS topic
    sns.subscribe(TopicArn=snsTopicArn, Protocol="sqs", Endpoint=sqsQueueArn)

    # Authorize SNS to write SQS queue
    policy = """
        {{
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
        }}""".format(sqsQueueArn, snsTopicArn)

    sqs.set_queue_attributes(QueueUrl=sqsQueueUrl, Attributes={"Policy": policy})

    roleArn = settings.AWS_ROLE_ARN
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    region_name = settings.AWS_REGION

    client = boto3.client(
        "textract",
        region_name=region_name,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    start_doc_analysis_respons = client.start_document_analysis(
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": document}},
        FeatureTypes=["TABLES", "FORMS"],
        NotificationChannel={
            "RoleArn": roleArn,
            "SNSTopicArn": snsTopicArn,
        },
    )

    job_id = start_doc_analysis_respons["JobId"]

    return job_id


def get_text(result, blocks_map):
    text = ""
    if "Relationships" in result:
        for relationship in result["Relationships"]:
            if relationship["Type"] == "CHILD":
                for child_id in relationship["Ids"]:
                    try:
                        word = blocks_map[child_id]
                        if word["BlockType"] == "WORD":
                            text += word["Text"] + " "
                        if word["BlockType"] == "SELECTION_ELEMENT":
                            if word["SelectionStatus"] == "SELECTED":
                                text += "X "
                    except KeyError:
                        print("Error extracting Table data - {}:".format(KeyError))

    return text


def get_rows_columns_map(table_result, blocks_map):
    rows = {}
    for relationship in table_result["Relationships"]:
        if relationship["Type"] == "CHILD":
            for child_id in relationship["Ids"]:
                try:
                    cell = blocks_map[child_id]
                    if cell["BlockType"] == "CELL":
                        row_index = cell["RowIndex"]
                        col_index = cell["ColumnIndex"]
                        if row_index not in rows:
                            # create new row
                            rows[row_index] = {}

                        # get the text value
                        rows[row_index][col_index] = get_text(cell, blocks_map)
                except KeyError:
                    print("Error extracting Table data - {}:".format(KeyError))
                    pass
    return rows


def convert_to_float(value):
    """
    Converts a string to a float, handling various number formats including
    those with misplaced commas and periods.
    """
    value = value.strip()  # Remove leading/trailing whitespace

    # Replace commas with empty string and ensure only the last period is kept
    try:
        value = value.replace(",", "")

        return float(value)
    except ValueError:
        print(f"Could not convert '{value}' to float.")
        return None  # Return None if conversion fails


HEADERS_BANK_TRANSACTION = [
    "Transaction Date",
    "Code",
    "Debit",
    "Credit",
    "Balance",
    "Description",
]


def assign_headers(df):
    df.columns = HEADERS_BANK_TRANSACTION

    return df[1:].reset_index(drop=True)


def clean_and_format_data(df, is_first, is_last):
    # Remove the first row if it's the first dataframe
    if is_first:
        df = df.iloc[1:].reset_index(drop=True)

    # Remove the last two rows if it's the last dataframe
    if is_last:
        df = df.iloc[:-2].reset_index(drop=True)

    # Convert Transaction Date to the appropriate format
    def convert_date(date_str):
        if date_str:
            try:
                return datetime.strptime(date_str.strip(), "%d/%m/%y %H:%M").date()
            except ValueError:
                return None
        return None

    # Convert Transaction Date to the appropriate format
    df["Transaction Date"] = df["Transaction Date"].apply(convert_date)
    df = df.dropna(subset=["Transaction Date"]).reset_index(drop=True)

    # Convert Debit, Credit, and Balance to numeric types
    df["Debit"] = pd.to_numeric(
        df["Debit"].str.replace(",", "").str.replace("*", ""), errors="coerce"
    ).fillna(0)
    df["Credit"] = pd.to_numeric(
        df["Credit"].str.replace(",", "").str.replace("*", ""), errors="coerce"
    ).fillna(0)
    df["Balance"] = pd.to_numeric(
        df["Balance"].str.replace(",", "").str.replace("*", ""), errors="coerce"
    ).fillna(0)

    # Create Amount column: Debit as negative and Credit as positive values
    df["Amount"] = df["Credit"] - df["Debit"]

    # Drop the Debit and Credit columns
    df = df.drop(columns=["Debit", "Credit"])

    # Define a function to extract the note
    # def extract_and_remove_note(description):
    #     if "NOTE" in description:
    #         note_index = description.find("NOTE")
    #         note = description[note_index + len("NOTE") :].strip()
    #         note = note.replace(":", "").replace(",", "")
    #         description = description[:note_index].strip()
    #         return note, description
    #     return "", description

    # Apply the function to the Description column
    # notes = df["Description"].apply(lambda x: extract_and_remove_note(x))
    # df["Note"] = notes.apply(lambda x: x[0])
    # df["Description"] = notes.apply(lambda x: x[1])

    return df


def generate_data_frame(blocks):
    """Generate DataFrames from the blocks
    This function uses Amazon's Textract API to extract data from the blocks
    The type of data is set to TABLE and the data is extracted from the blocks
    """
    blocks_map = {block["Id"]: block for block in blocks}
    table_blocks = [block for block in blocks if block["BlockType"] == "TABLE"]
    data_frames = []

    for i, table in enumerate(table_blocks):
        rows = get_rows_columns_map(table, blocks_map)
        table_data = []

        for row_index in sorted(rows.keys()):
            row = rows[row_index]
            row_data = [row.get(col_index, "") for col_index in sorted(row.keys())]
            table_data.append(row_data)

        df = pd.DataFrame(table_data)

        # Set headers
        df = assign_headers(df)

        # Drop the 2nd column
        df = df.drop(columns=df.columns[1])

        # Clean and format data
        df = clean_and_format_data(
            df, is_first=(i == 0), is_last=(i == len(table_blocks) - 1)
        )

        data_frames.append(df)

    return data_frames


def get_doc_analysis_results_bs(job_id):
    region_name = settings.AWS_REGION
    textract = boto3.client("textract", region_name=region_name)

    max_results = 1000
    pagination_token = None
    finished = False
    all_blocks = []

    while not finished:
        response = None

        if pagination_token == None:
            response = textract.get_document_analysis(
                JobId=job_id, MaxResults=max_results
            )
        else:
            response = textract.get_document_analysis(
                JobId=job_id, MaxResults=max_results, NextToken=pagination_token
            )
        blocks = response["Blocks"]
        all_blocks.extend(blocks)

        if "NextToken" in response:
            pagination_token = response["NextToken"]
        else:
            finished = True

    data_frames = generate_data_frame(all_blocks)

    return data_frames
