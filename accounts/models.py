import arrow
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from phonenumber_field.modelfields import PhoneNumberField
from multiselectfield import MultiSelectField
from common.utils import SOURCES, STAGES, BUSINESS_TYPES, COMMERCIAL_INSURANCE_TYPES, COMMERCIAL_LIABILITY_LIMITS

from common import utils
from common.models import Org, Profile, CustomPhoneNumberField
from common.utils import COUNTRIES, INDCHOICES
from contacts.models import Contact
from teams.models import Teams
from common.base import BaseModel


class Tags(BaseModel):
    name = models.CharField(max_length=20)
    slug = models.CharField(max_length=20, unique=True, blank=True)


    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        db_table = "tags"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name}"


    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Account(BaseModel):

    ACCOUNT_STATUS_CHOICE = (("open", "Open"), ("close", "Close"))

    name = models.CharField(pgettext_lazy("Name of Account", "Name"), max_length=64)
    email = models.EmailField()
    phone = CustomPhoneNumberField(null=True, blank=True)
    date_of_birth = models.DateField()

    industry = models.CharField(
        _("Industry Type"), max_length=255, choices=INDCHOICES, blank=True, null=True
    )
    # billing_address = models.ForeignKey(
    #     Address, related_name='account_billing_address', on_delete=models.CASCADE, blank=True, null=True)
    # shipping_address = models.ForeignKey(
    #     Address, related_name='account_shipping_address', on_delete=models.CASCADE, blank=True, null=True)
    billing_address_line = models.CharField(
        _("Address"), max_length=255, blank=True, null=True
    )
    billing_street = models.CharField(_("Street"), max_length=55, blank=True, null=True)
    billing_city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    billing_state = models.CharField(_("State"), max_length=255, blank=True, null=True)
    billing_postcode = models.CharField(
        _("Post/Zip-code"), max_length=64, blank=True, null=True
    )
    billing_country = models.CharField(
        max_length=3, choices=COUNTRIES, blank=True, null=True
    )

    previous_residency_address_line = models.CharField(
        _("Previous Address"), max_length=255, blank=True, null=True
    )
    previous_residency_street = models.CharField(_("Previous Street"), max_length=55, blank=True, null=True)
    previous_residency_city = models.CharField(_("Previous City"), max_length=255, blank=True, null=True)
    previous_residency_state = models.CharField(_("Previous State"), max_length=255, blank=True, null=True)
    previous_residency_postcode = models.CharField(
        _("Previous Post/Zip-code"), max_length=64, blank=True, null=True
    )
    previous_residency_country = models.CharField(
        max_length=3, choices=COUNTRIES, blank=True, null=True
    )
    website = models.URLField(_("Website"), blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    # created_by = models.ForeignKey(
    #     Profile, related_name="account_created_by", on_delete=models.SET_NULL, null=True
    # )
    is_active = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tags, blank=True)
    status = models.CharField(
        choices=ACCOUNT_STATUS_CHOICE, max_length=64, default="open"
    )
    lead = models.ForeignKey(
        "leads.Lead", related_name="account_leads", on_delete=models.SET_NULL, null=True
    )
    contact_name = models.CharField(
        pgettext_lazy("Name of Contact", "Contact Name"), max_length=120
    )
    contacts = models.ManyToManyField(
        "contacts.Contact", related_name="account_contacts"
    )
    assigned_to = models.ManyToManyField(Profile, related_name="account_assigned_users")
    teams = models.ManyToManyField(Teams, related_name="account_teams")
    org = models.ForeignKey(
        Org,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="account_org",
    )

    driver_liscence_number = models.CharField(max_length=255, blank=True, null=True)

    married = models.BooleanField(default=False)
    violations = models.BooleanField(default=False)
    rated_driver_or_excluded = models.CharField(max_length=255, blank=True, null=True)
    occupation = models.CharField(max_length=255, blank=True, null=True)
    current_insurance_company = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        db_table = "accounts"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name}"

    def get_complete_address(self):
        """Concatenates complete address."""
        address = ""
        add_to_address = [
            self.billing_street,
            self.billing_city,
            self.billing_state,
            self.billing_postcode,
            self.get_billing_country_display(),
        ]
        address = utils.append_str_to(address, *add_to_address)

        return address

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_at).humanize()

    @property
    def contact_values(self):
        contacts = list(self.contacts.values_list("id", flat=True))
        return ",".join(str(contact) for contact in contacts)

    @property
    def get_team_users(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        return Profile.objects.filter(id__in=team_user_ids)

    @property
    def get_team_and_assigned_users(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        assigned_user_ids = list(self.assigned_to.values_list("id", flat=True))
        user_ids = team_user_ids + assigned_user_ids
        return Profile.objects.filter(id__in=user_ids)

    @property
    def get_assigned_users_not_in_teams(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        assigned_user_ids = list(self.assigned_to.values_list("id", flat=True))
        user_ids = set(assigned_user_ids) - set(team_user_ids)
        return Profile.objects.filter(id__in=list(user_ids))


class AccountEmail(BaseModel):
    from_account = models.ForeignKey(
        Account, related_name="sent_email", on_delete=models.SET_NULL, null=True
    )
    recipients = models.ManyToManyField(Contact, related_name="recieved_email")
    message_subject = models.TextField(null=True)
    message_body = models.TextField(null=True)
    timezone = models.CharField(max_length=100, default="UTC")
    scheduled_date_time = models.DateTimeField(null=True)
    scheduled_later = models.BooleanField(default=False)
    from_email = models.EmailField()
    rendered_message_body = models.TextField(null=True)

    class Meta:
        verbose_name = "Account Email"
        verbose_name_plural = "Account Emails"
        db_table = "account_email"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.message_subject}"

class AccountEmailLog(BaseModel):
    """this model is used to track if the email is sent or not"""

    email = models.ForeignKey(
        AccountEmail, related_name="email_log", on_delete=models.SET_NULL, null=True
    )
    contact = models.ForeignKey(
        Contact, related_name="contact_email_log", on_delete=models.SET_NULL, null=True
    )
    is_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "EmailLog"
        verbose_name_plural = "EmailLogs"
        db_table = "emailLogs"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.email.message_subject}"

class RentersIntake(BaseModel):
    account = models.ForeignKey(
        Account,
        related_name="renters_intake_accoumt",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )   
    secondary_owner_name = models.CharField(max_length=255, blank=True, null=True)
    secondary_owner_date_of_birth = models.DateField(null=True, blank=True)
    secondary_owner_email = models.EmailField(max_length=255, blank=True, null=True)
    lease_start_date = models.DateField(null=True, blank=True)
    limit_of_coverage_desired = models.BooleanField(null=True, blank=True)
    has_dogs = models.BooleanField()
    number_of_dogs = models.IntegerField(null=True, blank=True)
    dog_breeds = models.CharField(max_length=255, blank=True, null=True)
    org = models.ForeignKey(
        Org,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="renters_intake_org",
    )

class CommercialIntake(BaseModel):
    account = models.ForeignKey(
        Account,
        related_name="commercial_intake_account",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )   
    business_name = models.CharField(_("Business Name"), null=False, blank=False, max_length=255)
    business_address_line_1 = models.CharField(_("Business Address Line 1"), null=False, blank=False, max_length=255)
    business_address_line_2 = models.CharField(_("Business Address Line 2"), null=True, blank=True, max_length=255)
    business_city = models.CharField(_("Business City"), null=False, blank=False, max_length=255)
    business_state = models.CharField(_("Business State"), null=False, blank=False, max_length=255)
    business_postal_code = models.CharField(_("Business Postal Code"), null=False, blank=False, max_length=10)
    business_mailing_address_line_1 = models.CharField(_("Business Mailing Address Line 1"), null=False, blank=False, max_length=255)
    business_mailing_address_line_2 = models.CharField(_("Business Mailing Address Line 2"), null=True, blank=True, max_length=255)
    business_mailing_city = models.CharField(_("Business Mailing City"), null=False, blank=False, max_length=255)
    business_mailing_state = models.CharField(_("Business Mailing State"), null=False, blank=False, max_length=255)
    business_mailing_postal_code = models.CharField(_("Business Mailing Postal Code"), null=False, blank=False, max_length=10)
    business_website = models.CharField(_("Business Website"), null=True, blank=True, max_length=255)
    nature_of_business = models.CharField(_("Nature of Business\\Services Offered"), null=True, blank=True, max_length=255)
    business_type = models.CharField(
        pgettext_lazy("Type of Business", "Type of Business"), max_length=64, choices=BUSINESS_TYPES
    )
    coverage_requested = MultiSelectField(choices=COMMERCIAL_INSURANCE_TYPES)
    liability_limit_requested = models.CharField(
        pgettext_lazy("Liability Limits Requested", "Liability Limits Requested"), max_length=64, choices=COMMERCIAL_LIABILITY_LIMITS
    )
    number_of_owners = models.IntegerField(_("Number of Owners"), null=False, blank=False)
    number_of_employees = models.IntegerField(_("Number of Employees"), null=False, blank=False)
    employee_annual_payroll = models.BigIntegerField(_("Employee Annual Payroll"), null=False, blank=False)
    annual_revenue = models.BigIntegerField(_("Annual Revenue"), null=False, blank=False)
    years_in_business = models.IntegerField(_("Years in Business"), null=False, blank=False)
    years_experience = models.IntegerField(_("Years Experience"), null=False, blank=False)
    number_of_contracted_employees = models.IntegerField(_("Number of Contracted Employees"), null=False, blank=False)
    cost_of_contracted_employees = models.IntegerField(_("Cost of Contracted Employees"), null=False, blank=False)
    contractors_liability_required = models.BooleanField(_("Is Contractor Liability Coverage Required?"), null=False, blank=False, default=False)
    additional_insured = models.CharField(_("Additional Insured"), null=True, blank=True, max_length=255)
    current_insurance_company = models.CharField(_("Current Insurance Company"), null=True, blank=True, max_length=255)
    effective_date = models.DateField(_("Effective Date"), null=True, blank=True)
    current_bodily_injury_limits = models.CharField(_("Current Bodily Injury Limits"), null=True, blank=True, max_length=255)
    any_losses = models.BooleanField(_("Any Losses?"), null=False, blank=False, default=False)
    org = models.ForeignKey(
        Org,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commercial_intake_org",
    )

class AutoIntake(BaseModel): 
    VIN = models.CharField(_("VIN"), null=False, blank=False, max_length=255)
    model_year = models.IntegerField(_("Car Model Year"), null=False, blank=False)
    make  = models.CharField(_("Car Make"), null=True, blank=True, max_length=255)
    model = models.CharField(_("Car Model"), null=False, blank=False, max_length=255)
    liability_coverage = models.BooleanField(_("Liability Coverage"), null=False, blank=False)
    collision_coverage = models.BooleanField(_("Collision Coverage"), null=False, blank=False)
    comprehensive_coverage = models.BooleanField(_("Comprehensive Coverage"), null=False, blank=False)
    personal_injury_protection_pip = models.BooleanField(_("Personal Injury Protection (PIP)"), null=False, blank=False)
    medical_payments = models.BooleanField(_("Medical Payments"), null=False, blank=False)
    uninsured_underinsured_motorist_coverage = models.BooleanField(_("Uninsured/Underinsured Motorist Coverage"), null=False, blank=False)
    rental_reimbursement_coverage = models.BooleanField(_("Rental Reimbursement Coverage"), null=False, blank=False)
    roadside_assistance = models.BooleanField(_("Roadside Assistance"), null=False, blank=False)
    gap_insurance = models.BooleanField(_("Gap Insurance"), null=False, blank=False)
    custom_parts_and_equipment_coverage = models.BooleanField(_("Custom Parts and Equipment Coverage"), null=False, blank=False)
    accident_forgiveness = models.BooleanField(_("Accident Forgiveness"), null=False, blank=False)
    new_car_replacement = models.BooleanField(_("New Car Replacement"), null=False, blank=False)
    loss_of_use = models.BooleanField(_("Loss of Use"), null=False, blank=False)
    org = models.ForeignKey(
        Org,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auto_intake_org",
    )

class Driver(BaseModel):
    account = models.ForeignKey(
        Account,
        related_name="auto_intake_driver",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    auto_intake = models.ForeignKey(
        AutoIntake,
        related_name="account_auto_driver",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )