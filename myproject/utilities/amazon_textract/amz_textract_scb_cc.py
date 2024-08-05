import boto3
from botocore.exceptions import ClientError
import logging
from django.conf import settings
import time
import pandas as pd
import json


def upload_file_to_s3(file, bucket, object_name):
    """Upload a file-like object to an S3 bucket

    :param file: File-like object to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name
    :return: True if file was uploaded, else False
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    try:
        s3_client.upload_fileobj(file, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False

    return True


def start_document_analysis(document):
    """Start a document analysis job on an S4 object
    This function creates a quque, sns topic, and subscribes the queue to the topic
    and returns the job_id of the document analysis job
    """
    sqs = boto3.client("sqs")
    sns = boto3.client("sns")

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
    start_doc_analysis_response = client.start_document_analysis(
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": document}},
        FeatureTypes=["TABLES", "FORMS"],
        NotificationChannel={
            "RoleArn": roleArn,
            "SNSTopicArn": snsTopicArn,
        },
    )

    job_id = start_doc_analysis_response["JobId"]

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

    if value.endswith("-"):
        value = "-" + value[:-1]  # Move the minus sign to the front

    # Replace commas with empty string and ensure only the last period is kept
    try:
        # Check if there are two periods; if so, remove all commas and then the first period
        if value.count(".") > 1:
            value = value.replace(".", "", value.count(".") - 1)
        # Now replace commas
        value = value.replace(",", "")

        return float(value)
    except ValueError:
        print(f"Could not convert '{value}' to float.")
        return None  # Return None if conversion fails


HEADERS_CREDIT_CARD_SUMMARY = ["Card Number", "Credit Limit", "Closing Date"]
HEADERS_BALANCE_AND_PAYMENT = ["New Balance", "Minimum Payment", "Payment Date"]
HEADERS_TRANSACTION_DETAILS = [
    "Posting Date",
    "Transaction Date",
    "Description",
    "Foreign Currency",
    "Amount",
]


def assign_headers(df):
    if "CARD NUMBER" in df.iloc[0, 0].upper():
        df.columns = HEADERS_CREDIT_CARD_SUMMARY
    if "NEW BALANCE" in df.iloc[0, 0].upper():
        df.columns = HEADERS_BALANCE_AND_PAYMENT
    if "POSTING DATE" in df.iloc[0, 0].upper():
        df.columns = HEADERS_TRANSACTION_DETAILS

    return df


def clean_credit_card_summary(df):
    # Remove leading and trailing spaces
    df["Credit Limit"] = df["Credit Limit"].str.replace(",", "").astype(int)

    # Strip spaces from the date column
    df["Closing Date"] = df["Closing Date"].str.strip()

    # Replace empty strings with NaT
    df["Closing Date"] = df["Closing Date"].replace("", pd.NaT)

    # Convert to datetime, coercing errors
    df["Closing Date"] = pd.to_datetime(
        df["Closing Date"], format="%d/%m/%y", errors="coerce"
    )

    # Optionally, print or log invalid dates for debugging
    invalid_dates = df[df["Closing Date"].isna()]
    if not invalid_dates.empty:
        print("Invalid dates found:", invalid_dates)
    return df


def clean_balance_and_payment(df):
    # Apply the conversion to the 'New Balance' and 'Minimum Payment' columns
    df["New Balance"] = df["New Balance"].apply(convert_to_float)
    df["Minimum Payment"] = df["Minimum Payment"].apply(convert_to_float)
    df["Payment Date"] = pd.to_datetime(
        df["Payment Date"].str.strip(), format="%d/%m/%y", errors="coerce"
    )
    return df


def clean_transaction_details(df, closing_date):
    # Extract year from closing_date
    year = pd.to_datetime(closing_date, format="%d/%m/%y").year

    # Process each row to handle dates
    def process_date(row_date, year):
        if pd.isna(row_date) or row_date.strip() == "":
            return pd.NaT
        try:
            full_date_str = row_date.strip() + f"/{year}"
            return pd.to_datetime(full_date_str, format="%d/%m/%Y", errors="coerce")
        except ValueError:
            print(f"Invalid date: {row_date}")
            return pd.NaT

    # Apply date processing
    df["Posting Date"] = df["Posting Date"].apply(lambda x: process_date(x, year))
    df["Transaction Date"] = df["Transaction Date"].apply(
        lambda x: process_date(x, year)
    )
    df["Amount"] = df["Amount"].apply(convert_to_float)

    # Reformat the 'Description' column for items that are credit vouchers
    indices_to_remove = []
    for index, row in df.iterrows():
        if pd.isna(row["Posting Date"]) and pd.isna(row["Transaction Date"]):
            if (
                index > 0
                and "CREDIT VOUCHER" in df.at[index - 1, "Description"]
                and row["Description"].strip() != ""
            ):
                df.at[index - 1, "Description"] += " " + row["Description"].strip()
                indices_to_remove.append(index)
            else:
                indices_to_remove.append(index)

    df = df.drop(indices_to_remove).reset_index(drop=True)

    # Adjust the Years' posting and transaction date if the month is greater than the closing date's month
    df.loc[df["Posting Date"].dt.month > closing_date.month, "Posting Date"] -= (
        pd.DateOffset(years=1)
    )
    df.loc[
        df["Transaction Date"].dt.month > closing_date.month, "Transaction Date"
    ] -= pd.DateOffset(years=1)

    return df


def generate_data_frame(blocks):
    """Generate DataFrames from the blocks
    This function uses Amazon's Textract API to extract data from the blocks
    The type of data is set to TABLE and the data is extracted from the blocks
    """
    blocks_map = {block["Id"]: block for block in blocks}
    table_blocks = [block for block in blocks if block["BlockType"] == "TABLE"]
    closing_date = None
    data_frames = []

    # Track headeres thats been processed
    headers_processed = {
        "credit_card_summary": False,
        "balance_and_payment": False,
    }

    for table in table_blocks:
        rows = get_rows_columns_map(table, blocks_map)
        table_data = []

        for row_index in sorted(rows.keys()):
            row = rows[row_index]
            row_data = [row.get(col_index, "") for col_index in sorted(row.keys())]
            table_data.append(row_data)

        df = pd.DataFrame(table_data)

        # Set headers
        df = assign_headers(df)
        # Remove the first row
        df = df[1:]
        df.reset_index(drop=True, inplace=True)

        # Clean the DataFrame
        if (
            df.columns.tolist() == HEADERS_CREDIT_CARD_SUMMARY
            and not headers_processed["credit_card_summary"]
        ):
            df = clean_credit_card_summary(df)
            closing_date = (
                df["Closing Date"].iloc[0]
                if not df["Closing Date"].isna().iloc[0]
                else None
            )
            headers_processed["credit_card_summary"] = True
            data_frames.append(df)
        if (
            df.columns.tolist() == HEADERS_BALANCE_AND_PAYMENT
            and not headers_processed["balance_and_payment"]
        ):
            df = clean_balance_and_payment(df)
            headers_processed["balance_and_payment"] = True
            data_frames.append(df)
        if df.columns.tolist() == HEADERS_TRANSACTION_DETAILS:
            if closing_date:
                df = clean_transaction_details(df, closing_date)
                data_frames.append(df)
            else:
                print("Closing date not found")

        print(df)

    return data_frames


def get_doc_analysis_results(job_id):
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

    # Prepare a dictionary to store categorized DataFrames
    data_frames_dicts = {
        "credit_card_summary": None,
        "balance_and_payment": None,
        "transaction_details": [],
    }

    for df in data_frames:
        if df.columns.tolist() == HEADERS_CREDIT_CARD_SUMMARY:
            data_frames_dicts["credit_card_summary"] = df
        elif df.columns.tolist() == HEADERS_BALANCE_AND_PAYMENT:
            data_frames_dicts["balance_and_payment"] = df
        else:
            data_frames_dicts["transaction_details"].append(df)

    # Convert DataFrame list to single DataFrame for transaction details
    if data_frames_dicts["transaction_details"]:
        data_frames_dicts["transaction_details"] = pd.concat(
            data_frames_dicts["transaction_details"], ignore_index=True
        )

    return data_frames_dicts
