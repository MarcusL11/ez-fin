from django.shortcuts import render, get_object_or_404
from django.http import (
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseNotAllowed,
)
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
from django.core.paginator import Paginator
from django.shortcuts import redirect


def my_docs(request):
    if not request.user.is_anonymous and request.user.has_verified_email:
        user = request.user
        # get documents of user
        documents = Document.objects.filter(user=user).all()
        context = {"documents": documents}
        return render(request, "upload_doc/my_docs.html", context)
    else:
        return HttpResponseForbidden("Forbidden")


def my_docs_detail(request, pk=None, transaction_type_slug=None):
    if request.method == "GET":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            document = get_object_or_404(Document, pk=pk, user=user)

            transaction_type = get_object_or_404(
                TransactionType, slug=transaction_type_slug
            )
            print("transaction_type_slug: " + str(transaction_type.slug))

            transactions = document.transaction_details.all()

            paginator = Paginator(transactions, 10)
            page_number = request.GET.get("page", 1)
            page_obj = paginator.get_page(page_number)
            print("Page Number: " + str(page_number))

            if transaction_type.slug == "credit-card":
                print("Credit Card Template was accessed")
                context = {
                    "document": document,
                    "page_obj": page_obj,
                }
                return render(
                    request, "upload_doc/my_docs_detail_credit_card.html", context
                )
            elif transaction_type.slug == "bank-statement":
                print("Bank Statement Template was accessed")
                context = {
                    "document": document,
                    "page_obj": page_obj,
                }
                return render(request, "upload_doc/my_docs_detail_bs.html", context)
            else:
                return HttpResponseForbidden("Forbidden")
        else:
            return HttpResponseForbidden("Forbidden")

    else:
        return HttpResponseNotAllowed("Only GET method is allowed")


# TODO: Change this to be a view with parameters to define the page number and the document id
def pagination_view(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            request_next_page_number = request.POST.get("next_page_number")
            request_previous_page_number = request.POST.get("previous_page_number")
            doucment_id = request.POST.get("document_id")

            print("Next page number: ", request_next_page_number)
            print("Previous page number: ", request_previous_page_number)
            print("Document ID: ", doucment_id)

            document = Document.objects.get(pk=doucment_id, user=user)
            transactions = document.transaction_details.all()

            paginator = Paginator(transactions, 10)

            if request_next_page_number is not None:
                page_obj = paginator.get_page(request_next_page_number)
            else:
                page_obj = paginator.get_page(request_previous_page_number)

            context = {
                "document": document,
                "transactions": transactions,
                "page_obj": page_obj,
            }
            return render(request, "upload_doc/partials/pagination_view.html", context)
        else:
            return HttpResponseForbidden("Forbidden")
    else:
        return HttpResponseNotAllowed("Only POST method is allowed")


def delete_doc(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            document_ids = request.POST.getlist("document_ids")
            print("Document IDs: ", document_ids)
            for pk in document_ids:
                try:
                    document = get_object_or_404(Document, pk=pk, user=user)
                    document.delete()
                except Exception as e:
                    print("Error: " + str(e))
                    return HttpResponseNotFound("Document not found")
            context = {"documents": Document.objects.filter(user=user).all}
            return render(
                request,
                "upload_doc/partials/delete_doc.html",
                context,
            )
        else:
            return HttpResponseForbidden("Forbidden")
    else:
        return HttpResponseNotAllowed("Only POST method is allowed")


def upload_doc(request):
    if not request.user.is_anonymous and request.user.has_verified_email:
        form = UploadFileForm()
        user = request.user

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
                        None,
                        "File size is too large. Please upload a file less than 2MB.",
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

                # S3 file name
                s3_file_name = str(user, "_", file_name)

                print("Sanitize File Name: " + file_name)
                print("Uploading file to S3")
                success = upload_file_to_s3(file, bucket, s3_file_name)
                print("Upload status: " + str(success))

                if success:
                    # if success, create a document variable that takes the file name
                    job_id = start_document_analysis(s3_file_name)
                    print("Job ID: " + job_id)

                    # TODO: Change this to a better way of waiting for the job to complete
                    # https://www.youtube.com/watch?v=kzOBNLzpRLE <--- Tuturial on how to setup invoking Lambda on uploads
                    time.sleep(60)

                    if doc_type == "Credit Card":
                        # Start the get_doc_analysis_results function to get the results of the analysis
                        data_frames_dicts = get_doc_analysis_results(job_id)

                        # Create a document object in the database
                        document, created = Document.objects.get_or_create(
                            date_uploaded=timezone.now(),
                            user=user,
                            file_name=file_name,
                            s3_file_name=s3_file_name,
                        )

                        # Save the data to the all models with its relationships
                        try:
                            print("Saving data to models")
                            # TODO: Consider adding Bank Type as a parameter instead of hardcoding
                            save_data_to_models(data_frames_dicts, document)

                        except Exception as e:
                            print("Error: " + str(e))

                        context = {
                            "message": "Uploaded succesfully",
                            "job_id": job_id,
                            "file_name": file_name,
                            "document": document,
                            "doc_type": doc_type,
                        }
                        print("Redirecting to my_docs_detail")
                        return redirect(
                            "my_docs_detail",
                            pk=document.pk,
                            transaction_type_slug="credit-card",
                        )

                    elif doc_type == "Bank Statement":
                        # create a dataframe dic using get_doc_analysis_results_bs function and job_id as its parameter
                        data_frames_dicts = get_doc_analysis_results_bs(job_id)

                        # Debug:
                        print("DataFrame Dicts:", data_frames_dicts)

                        # create the document
                        document, created = Document.objects.get_or_create(
                            date_uploaded=timezone.now(),
                            user=user,
                        )
                        # Save the data to all models with its relationships
                        try:
                            print("Saving data to models")
                            save_data_to_models_bs(
                                file_name, data_frames_dicts, document
                            )
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
    else:
        return HttpResponseForbidden("Forbidden")
