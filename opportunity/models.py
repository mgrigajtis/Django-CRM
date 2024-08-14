import arrow
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from multiselectfield import MultiSelectField
from accounts.models import Tags
from common.models import Org, Profile
from common.base import BaseModel
from common.utils import SOURCES, STAGES, BUSINESS_TYPES, COMMERCIAL_INSURANCE_TYPES, COMMERCIAL_LIABILITY_LIMITS
from teams.models import Teams
from tasks.models import Task

class CommercialIntake(BaseModel):
    contact_name = models.CharField(_("Contact Name"), null=False, blank=False, max_length=255)
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


class Opportunity(BaseModel):
    account_name = models.CharField(_("Account Name"), max_length=255)
    first_name = models.CharField(_("First name"), null=True, max_length=255)
    last_name = models.CharField(_("Last name"), null=True, max_length=255)
    stage = models.CharField(
        pgettext_lazy("Stage of Opportunity", "Stage"), max_length=64, choices=STAGES
    )
    lead_source = models.CharField(
        _("Source of Lead"), max_length=255, choices=SOURCES, blank=True, null=True
    )
    closed_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="oppurtunity_closed_by",
    )
    closed_on = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ManyToManyField(Profile, related_name="opportunity_assigned_to", blank=True)
    is_active = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tags, blank=True)
    teams = models.ManyToManyField(Teams, related_name="oppurtunity_teams", blank=True)
    tasks = models.ManyToManyField(Task, related_name="opportunity_tasks", blank=True)
    org = models.ForeignKey(
        Org,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="oppurtunity_org",
    )

    class Meta:
        verbose_name = "Opportunity"
        verbose_name_plural = "Opportunities"
        db_table = "opportunity"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name}"

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_at).humanize()

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
