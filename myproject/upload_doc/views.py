from django.shortcuts import render, get_object_or_404
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseNotAllowed,
)
from django.conf import settings
from pathvalidate import sanitize_filename
from utilities.amazon_textract.amz_textract_scb_cc import (
    upload_file_to_s3,
)
from .forms import UploadFileForm
from utilities.amazon_textract.amz_data_saver_scb_cc import save_data_to_models
from utilities.amazon_textract.amazon_docs import main as process_doc
from .models import (
    Document,
    TransactionType,
    BalanceAndPayment,
    CreditCardSummary,
    Bank,
)
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import redirect


def my_docs(request):
    if not request.user.is_anonymous and request.user.has_verified_email:
        user = request.user
        documents = Document.objects.filter(user=user).all().order_by("date_uploaded")
        transaction_types = (
            documents.values_list("transaction_type__name", flat=True)
            .distinct()
            .order_by("transaction_type__name")
        )

        banks = (
            documents.values_list("bank__name", flat=True)
            .distinct()
            .order_by("bank__name")
        )

        if request.method == "GET":
            paginator = Paginator(documents, 10)
            page_number = request.GET.get("page", 1)
            page_obj = paginator.get_page(page_number)

            context = {
                "documents": documents,
                "page_obj": page_obj,
                "transaction_types": transaction_types,
                "banks": banks,
            }

            return render(request, "upload_doc/my_docs.html", context)

        # TODO: Move this to my_docs_pagination_view so pagination will be done on filtered items
        if request.method == "POST":
            paginator = Paginator(documents, 10)
            page_number = request.GET.get("page", 1)
            page_obj = paginator.get_page(page_number)
            print("Page Number: " + str(page_number))

            context = {
                "documents": documents,
                "page_obj": page_obj,
                "transaction_types": transaction_types,
                "banks": banks,
            }
            return render(request, "upload_doc/my_docs.html", context)

    else:
        return HttpResponseForbidden()


# TODO: Convert to reusable component
def my_docs_pagination_view(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            request_next_page_number = request.POST.get("next_page_number")
            request_previous_page_number = request.POST.get("previous_page_number")

            print("Next page number: ", request_next_page_number)
            print("Previous page number: ", request_previous_page_number)

            document = Document.objects.filter(user=user).order_by("date_uploaded")

            paginator = Paginator(document, 10)

            if request_next_page_number is not None:
                page_obj = paginator.get_page(request_next_page_number)
            else:
                page_obj = paginator.get_page(request_previous_page_number)

            context = {
                "document": document,
                "page_obj": page_obj,
            }
            return render(
                request, "upload_doc/partials/my_docs_pagination_view.html", context
            )
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseNotAllowed(permitted_methods=["POST"])


def my_docs_detail(request, pk=None, transaction_type_slug=None):
    if request.method == "GET":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            document = get_object_or_404(Document, pk=pk, user=user)
            balance_and_payment = get_object_or_404(
                BalanceAndPayment,
                document=document,
                user=user,
            )
            credit_card_summary = get_object_or_404(
                CreditCardSummary,
                document=document,
                user=user,
            )
            transaction_type = get_object_or_404(
                TransactionType,
                slug=transaction_type_slug,
            )
            print("transaction_type_slug: " + str(transaction_type.slug))

            transactions = document.transaction_details.all().order_by(
                "transaction_date"
            )

            paginator = Paginator(transactions, 10)
            page_number = request.GET.get("page", 1)
            page_obj = paginator.get_page(page_number)
            print("Page Number: " + str(page_number))

            if transaction_type.slug == "credit-card":
                print("Credit Card Template was accessed")
                context = {
                    "document": document,
                    "balance_and_payment": balance_and_payment,
                    "credit_card_summary": credit_card_summary,
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
                return HttpResponseBadRequest()
        else:
            return HttpResponseForbidden()

    else:
        return HttpResponseNotAllowed(permitted_methods=["GET"])


# TODO: Convert to reusable component
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
            balance_and_payment = get_object_or_404(
                BalanceAndPayment,
                document=document,
                user=user,
            )
            credit_card_summary = get_object_or_404(
                CreditCardSummary,
                document=document,
                user=user,
            )
            transactions = document.transaction_details.all().order_by(
                "transaction_date"
            )

            paginator = Paginator(transactions, 10)

            if request_next_page_number is not None:
                page_obj = paginator.get_page(request_next_page_number)
            else:
                page_obj = paginator.get_page(request_previous_page_number)

            context = {
                "document": document,
                "balance_and_payment": balance_and_payment,
                "credit_card_summary": credit_card_summary,
                "transactions": transactions,
                "page_obj": page_obj,
            }
            return render(request, "upload_doc/partials/pagination_view.html", context)
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseNotAllowed(permitted_methods=["POST"])


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
                    return HttpResponseNotFound()
            context = {"documents": Document.objects.filter(user=user).all}
            return render(
                request,
                "upload_doc/partials/delete_doc.html",
                context,
            )
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseNotAllowed(permitted_methods=["POST"])


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

                # S3 file name is the user's primary key and the file name
                s3_file_name = f"{user.pk}_{file_name}"

                print("Sanitize File Name: " + file_name)
                print("S3 File Name: " + s3_file_name)
                print("Uploading file to S3")
                success = upload_file_to_s3(file, bucket, s3_file_name)
                print("Upload status: " + str(success))

                if success:
                    if doc_type == "Credit Card":
                        # Start the get_doc_analysis_results function to get the results of the analysis
                        # data_frames_dicts = get_doc_analysis_results(job_id)

                        bank_instance, _ = Bank.objects.get_or_create(name="SCB")
                        print("Bank Instance: " + str(bank_instance.name))

                        # Ensure TransactionType instance
                        transaction_type_instance, _ = (
                            TransactionType.objects.get_or_create(name="Credit Card")
                        )
                        print(
                            "Transaction Type Instance: "
                            + str(transaction_type_instance.name)
                        )

                        document, _ = Document.objects.get_or_create(
                            date_uploaded=timezone.now(),
                            user=user,
                            name=file_name,
                            s3_file_name=s3_file_name,
                            bank=bank_instance,
                            transaction_type=transaction_type_instance,
                        )
                        print("Document: " + str(document))

                        balance_and_payment, _ = (
                            BalanceAndPayment.objects.get_or_create(
                                user=user,
                                document=document,
                            )
                        )

                        credit_card_summary, _ = (
                            CreditCardSummary.objects.get_or_create(
                                user=user,
                                document=document,
                            )
                        )

                        data_frames_dicts = process_doc(s3_file_name)
                        if data_frames_dicts is None:
                            form.add_error(
                                None,
                                "File upload failed. Please try again.",
                            )
                            return render(
                                request,
                                "upload_doc/partials/upload_doc_errors.html",
                                context={"form": form},
                            )

                        # Save the data to the all models with its relationships
                        try:
                            print("Saving data to models")
                            save_data_to_models(
                                data_frames_dicts,
                                document,
                                credit_card_summary,
                                balance_and_payment,
                            )

                        except Exception as e:
                            print("Error: " + str(e))
                            form.add_error(
                                None,
                                "File upload failed. Please try again.",
                            )
                            return render(
                                request,
                                "upload_doc/partials/upload_doc_errors.html",
                                context={"form": form},
                            )

                        print("Redirecting to my_docs_detail")
                        return redirect(
                            "my_docs_detail",
                            pk=document.pk,
                            transaction_type_slug=document.transaction_type.slug,
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
        return HttpResponseForbidden()
