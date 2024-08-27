import arrow
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from contacts.models import Contact
from common.base import BaseModel


# Create your models here.
class Lender(BaseModel):
    name = models.CharField(pgettext_lazy("Name of Lender", "Name"), max_length=64)
    contacts = models.ManyToManyField(Contact)