from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from django.conf import settings
from pathvalidate import sanitize_filename
from utilities.amazon_textract.amz_textract_scb_cc import (
    upload_file_to_s3,
    start_document_analysis,
    get_doc_analysis_results,
)
from .forms import UploadFileForm
from utilities.amazon_textract.amz_data_saver_scb_cc import save_data_to_models
from utilities.amazon_textract.amz_data_saver_scb_bs import save_data_to_models_bs
from utilities.amazon_textract.amz_textract_scb_bs import (
    get_doc_analysis_results_bs,
)
import time
from .models import Document, TransactionType
from django.utils import timezone


def my_docs(request):
    documents = Document.objects.all()
    context = {"documents": documents}
    return render(request, "upload_doc/my_docs.html", context)


def my_docs_detail(request, pk=None, transaction_type_slug=None):
    if request.method == "GET":
        document = get_object_or_404(Document, pk=pk)
        transaction_type = get_object_or_404(
            TransactionType, slug=transaction_type_slug
        )
        print("transaction_type_slug: " + str(transaction_type.slug))

        if transaction_type.slug == "credit-card":
            print("Credit Card Template was accessed")
            context = {
                "document": document,
            }
            return render(
                request, "upload_doc/my_docs_detail_credit_card.html", context
            )
        elif transaction_type.slug == "bank-statement":
            print("Bank Statement Template was accessed")
            context = {
                "document": document,
            }
            return render(request, "upload_doc/my_docs_detail_bs.html", context)
        else:
            return HttpResponseForbidden("Forbidden")

    else:
        return HttpResponseForbidden("Forbidden")


def upload_doc(request):
    form = UploadFileForm()

    if request.method == "POST":
        print("POST request received")
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            print("Form is valid")
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            bank = request.POST["bank"]
            doc_type = request.POST["doc_type"]
            file_name = request.POST["file_name"]
            file = request.FILES["file"]
            print("Bank: " + bank)
            print("Doc Type:" + doc_type)
            print("File Name: " + file_name)

            # Validate file size to be less than 2MB
            print("Checking file size")
            file_size = file.size
            print("File Size: " + str(file_size))
            file_size_limit = 2 * 1048576
            if file_size > file_size_limit:
                form.add_error(
                    None, "File size is too large. Please upload a file less than 2MB."
                )
                return render(
                    request,
                    "upload_doc/partials/upload_doc_errors.html",
                    context={"form": form},
                )

            # Validate file type
            print("Checking file type")
            allowed_file_types = ["application/pdf", "image/jpeg", "image/png"]
            file_type = file.content_type
            print("File Type: " + file_type)
            if file_type not in allowed_file_types:
                form.add_error(
                    None,
                    "Invalid file type. Please upload a file of type PDF, JPEG or PNG.",
                )
                return render(
                    request,
                    "upload_doc/partials/upload_doc_errors.html",
                    context={"form": form},
                )

            print("Sanitizing file name")
            # Sanitize file_name
            file_name = sanitize_filename(file_name)

            # Remove whitespaces and lowercase all text in file name
            file_name = file_name.replace(" ", "_")
            file_name = file_name.lower()

            # add file type to file name
            file_name = file_name + "." + file_type.split("/")[1]

            print("Sanitize File Name: " + file_name)
            print("Uploading file to S3")
            success = upload_file_to_s3(file, bucket, file_name)
            print("Upload status: " + str(success))

            if success:
                # if success, create a document variable that takes the file name
                job_id = start_document_analysis(file_name)
                print("Job ID: " + job_id)

                # TODO: Change this to a better way of waiting for the job to complete
                # https://www.youtube.com/watch?v=kzOBNLzpRLE <--- Tuturial on how to setup invoking Lambda on uploads
                time.sleep(60)

                if doc_type == "Credit Card":
                    # Start the get_doc_analysis_results function to get the results of the analysis
                    data_frames_dicts = get_doc_analysis_results(job_id)

                    # Create a document object in the database
                    document, created = Document.objects.get_or_create(
                        date_uploaded=timezone.now()
                    )

                    # Save the data to the all models with its relationships
                    try:
                        print("Saving data to models")
                        # TODO: Consider adding Bank Type as a parameter instead of hardcoding
                        save_data_to_models(file_name, data_frames_dicts, document)

                    except Exception as e:
                        print("Error: " + str(e))

                    context = {
                        "message": "Uploaded succesfully",
                        "job_id": job_id,
                        "file_name": file_name,
                        "document": document,
                        "doc_type": doc_type,
                    }
                    # TODO: Just redirect to the doc_detail
                    return render(
                        request,
                        "upload_doc/partials/upload_doc_get_result.html",
                        context=context,
                    )
                elif doc_type == "Bank Statement":
                    # create a dataframe dic using get_doc_analysis_results_bs function and job_id as its parameter
                    data_frames_dicts = get_doc_analysis_results_bs(job_id)

                    # Debug:
                    print("DataFrame Dicts:", data_frames_dicts)

                    # create the document
                    document, created = Document.objects.get_or_create(
                        date_uploaded=timezone.now()
                    )
                    # Save the data to all models with its relationships
                    try:
                        print("Saving data to models")
                        save_data_to_models_bs(file_name, data_frames_dicts, document)
                    except Exception as e:
                        print("Error: " + str(e))
                    context = {
                        "message": "Uploaded succesfully",
                        "job_id": job_id,
                        "file_name": file_name,
                        "document": document,
                    }
                    return render(
                        request,
                        "upload_doc/partials/upload_doc_get_result.html",
                        context=context,
                    )

            else:
                form.add_error(None, "File upload failed. Please try again.")
                return render(
                    request,
                    "upload_doc/partials/upload_doc_errors.html",
                    context={"form": form},
                )
        else:
            form.add_error(None, "Form is invalid. Please try again.")
            return render(request, "upload_doc/upload_doc.html", {"form": form})

    return render(request, "upload_doc/upload_doc.html", {"form": form})
