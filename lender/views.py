from django.db.models import Q
from django.shortcuts import render
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from lender.models import Lender
from lender.serializer import *
from common.models import Profile
from drf_spectacular.utils import extend_schema
from common.serializer import ProfileSerializer


# Create your views here.
class LenderListView(APIView, LimitOffsetPagination):

    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Lender

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by("-id")
        contacts = Contact.objects.filter(org=self.request.profile.org)
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
            ).distinct()
            contacts = contacts.filter(
                Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
            ).distinct()

        if params:
            if params.get("name"):
                queryset = queryset.filter(name__icontains=params.get("name"))

        context = {}
        results_opportunities = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        lenders = LenderSerializer(results_opportunities, many=True).data
        if results_opportunities:
            offset = queryset.filter(id__gte=results_opportunities[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context.update(
            {
                "lenders_count": self.count,
                "offset": offset,
            }
        )
        context["lenders"] = lenders
        context["contacts_list"] = ContactSerializer(contacts, many=True).data

        return context

    @extend_schema(
        tags=["Lenders"]
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Lenders"],
        request=LenderCreateSwaggerSerializer
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        serializer = LenderCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            lender_obj = serializer.save(
                created_by=request.profile.user,
                closed_on=params.get("due_date"),
                org=request.profile.org,
            )

            if params.get("contacts"):
                contacts_list = params.get("contacts")
                contacts = Contact.objects.filter(id__in=contacts_list, org=request.profile.org)
                lender_obj.contacts.add(*contacts)

            return Response(
                {"error": False, "message": "Lender Created Successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LenderDetailView(APIView):
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Lender

    def get_object(self, pk):
        return self.model.objects.filter(id=pk).first()

    @extend_schema(
        tags=["Lenders"],
        request=LenderCreateSwaggerSerializer
    )
    def put(self, request, pk, format=None):
        params = request.data
        lender_object = self.get_object(pk=pk)
        if lender_object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile == lender_object.created_by)
                or (self.request.profile in lender_object.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = LenderCreateSerializer(
            lender_object,
            data=params,
            request_obj=request
        )

        if serializer.is_valid():
            lender_object = serializer.save()
            lender_object.contacts.clear()
            if params.get("contacts"):
                contacts_list = params.get("contacts")
                contacts = Contact.objects.filter(id__in=contacts_list, org=request.profile.org)
                lender_object.contacts.add(*contacts)

            return Response(
                {"error": False, "message": "Lender Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Lenders"]
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.profile != self.object.created_by:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        self.object.delete()
        return Response(
            {"error": False, "message": "Lender Deleted Successfully."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Lenders"]
    )
    def get(self, request, pk, format=None):
        self.opportunity = self.get_object(pk=pk)
        context = {}
        context["lender_obj"] = LenderSerializer(self.opportunity).data
        if self.opportunity.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile == self.opportunity.created_by)
                or (self.request.profile in self.opportunity.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        context.update(
            {
                "contacts": ContactSerializer(
                    self.opportunity.contacts.all(), many=True
                ).data,
                "users": ProfileSerializer(
                    Profile.objects.filter(
                        is_active=True, org=self.request.profile.org
                    ).order_by("user__email"),
                    many=True,
                ).data,
            }
        )
        return Response(context)

    @extend_schema(
        tags=["Lenders"]
    )
    def post(self, request, pk, **kwargs):
        params = request.data
        context = {}
        self.lender_obj = Lender.objects.get(pk=pk)
        if self.lender_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(context)