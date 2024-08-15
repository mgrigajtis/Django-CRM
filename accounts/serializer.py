from rest_framework import serializers

from accounts.models import Account, AccountEmail, Tags, AccountEmailLog, RentersIntake, CommercialIntake
from common.serializer import (
    AttachmentsSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    UserSerializer
)
from contacts.serializer import ContactSerializer
from leads.serializer import LeadSerializer
from teams.serializer import TeamsSerializer


class TagsSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class AccountSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    lead = LeadSerializer()
    org = OrganizationSerializer()
    tags = TagsSerailizer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    account_attachment = AttachmentsSerializer(read_only=True, many=True)

    class Meta:
        model = Account
        # fields = ‘__all__’
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "date_of_birth",
            "industry",
            "billing_address_line",
            "billing_street",
            "billing_city",
            "billing_state",
            "billing_postcode",
            "billing_country",
            "previous_residency_address_line",
            "previous_residency_street",
            "previous_residency_city",
            "previous_residency_state",
            "previous_residency_postcode",
            "previous_residency_country",
            "website",
            "description",
            "account_attachment",
            "created_by",
            "created_at",
            "is_active",
            "tags",
            "status",
            "lead",
            "contact_name",
            "contacts",
            "assigned_to",
            "teams",
            "org",
        )


class EmailSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = AccountEmail
        fields = (
            "message_subject",
            "message_body",
            "timezone",
            "scheduled_date_time",
            "scheduled_later",
            "created_at",
            "from_email",
            "rendered_message_body",
        )

    def validate_message_body(self, message_body):
        count = 0
        for i in message_body:
            if i == "{":
                count += 1
            elif i == "}":
                count -= 1
            if count < 0:
                raise serializers.ValidationError(
                    "Brackets do not match, Enter valid tags."
                )
        if count != 0:
            raise serializers.ValidationError(
                "Brackets do not match, Enter valid tags."
            )
        return message_body


class EmailLogSerializer(serializers.ModelSerializer):
    email = EmailSerializer()

    class Meta:
        model = AccountEmailLog
        fields = ["email", "contact", "is_sent"]


class AccountReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = ["name", "billing_city", "tags"]

class AccountWriteSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Account
        fields = ["name","phone", "email", "billing_address_line","billing_street","billing_city", "billing_state", "billing_postcode","billing_country","contacts", "teams", "assigned_to","tags","account_attachment", "website", "status","lead"]


class AccountCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        account_view = kwargs.pop("account", False)
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.fields["status"].required = False
        if account_view:
            self.fields["billing_address_line"].required = True
            self.fields["billing_street"].required = True
            self.fields["billing_city"].required = True
            self.fields["billing_state"].required = True
            self.fields["billing_postcode"].required = True
            self.fields["billing_country"].required = True

        if self.instance:
            self.fields["lead"].required = False
        self.fields["lead"].required = False
        self.org = request_obj.profile.org

    def validate_name(self, name):
        if self.instance:
            if self.instance.name != name:
                if not Account.objects.filter(name__iexact=name, org=self.org).exists():
                    return name
                raise serializers.ValidationError(
                    "Account already exists with this name"
                )
            return name
        if not Account.objects.filter(name__iexact=name, org=self.org).exists():
            return name
        raise serializers.ValidationError("Account already exists with this name")

    class Meta:
        model = Account
        fields = (
            "name",
            "phone",
            "email",
            "date_of_birth",
            "website",
            "industry",
            "description",
            "status",
            "billing_address_line",
            "billing_street",
            "billing_city",
            "billing_state",
            "billing_postcode",
            "billing_country",
            "previous_residency_address_line",
            "previous_residency_street",
            "previous_residency_city",
            "previous_residency_state",
            "previous_residency_postcode",
            "previous_residency_country",
            "lead",
            "contact_name",
        )

class AccountDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    account_attachment = serializers.FileField()

class AccountCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()

class EmailWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountEmail
        fields = ("from_email", "recipients", "message_subject","scheduled_later","timezone","scheduled_date_time","message_body")

class RentersIntakeSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
    class Meta:
        model = RentersIntake
        fields = (
            "account",
            "secondary_owner_name",
            "secondary_owner_date_of_birth",
            "secondary_owner_email",
            "lease_start_date",
            "limit_of_coverage_desired",
            "has_dogs",
            "number_of_dogs",
            "dog_breeds",
            "org"
        )
        extra_kwargs = {
            'number_of_dogs': {'allow_null': True},
        }

    def validate(self, data):
        if data.get('has_dogs') and data.get('number_of_dogs') is None:
            raise serializers.ValidationError(
                {"number_of_dogs": "This field is required if there are dogs."}
            )
        return data

class RentersIntakeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentersIntake
        fields = (
            "account",
            "secondary_owner_name",
            "secondary_owner_date_of_birth",
            "secondary_owner_email",
            "lease_start_date",
            "limit_of_coverage_desired",
            "has_dogs",
            "number_of_dogs",
            "dog_breeds",
            "org",
            "id"
        )


class CommercialIntakeSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
    class Meta:
        model = CommercialIntake
        fields = (
            "account",
            "business_name",
            "business_address_line_1",
            "business_address_line_2",
            "business_city",
            "business_state",
            "business_postal_code",
            "business_mailing_address_line_1",
            "business_mailing_address_line_2",
            "business_mailing_city",
            "business_mailing_state",
            "business_mailing_postal_code",
            "business_website",
            "nature_of_business",
            "business_type",
            "coverage_requested",
            "liability_limit_requested",
            "number_of_owners",
            "number_of_employees",
            "employee_annual_payroll",
            "annual_revenue",
            "years_in_business",
            "years_experience",
            "number_of_contracted_employees",
            "cost_of_contracted_employees",
            "contractors_liability_required",
            "additional_insured",
            "current_insurance_company",
            "effective_date",
            "current_bodily_injury_limits",
            "any_losses",
            "org",
        )

class CommercialIntakeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommercialIntake
        fields = (
            "account",
            "business_name",
            "business_address_line_1",
            "business_address_line_2",
            "business_city",
            "business_state",
            "business_postal_code",
            "business_mailing_address_line_1",
            "business_mailing_address_line_2",
            "business_mailing_city",
            "business_mailing_state",
            "business_mailing_postal_code",
            "business_website",
            "nature_of_business",
            "business_type",
            "coverage_requested",
            "liability_limit_requested",
            "number_of_owners",
            "number_of_employees",
            "employee_annual_payroll",
            "annual_revenue",
            "years_in_business",
            "years_experience",
            "number_of_contracted_employees",
            "cost_of_contracted_employees",
            "contractors_liability_required",
            "additional_insured",
            "current_insurance_company",
            "effective_date",
            "current_bodily_injury_limits",
            "any_losses",
            "org",
            "id"
        )