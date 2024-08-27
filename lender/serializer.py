from rest_framework import serializers

from contacts.serializer import ContactSerializer
from lender.models import Lender

class LenderSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = Lender
        fields = "__all__"


class LenderCreateSerializer(serializers.ModelSerializer):
    probability = serializers.IntegerField(max_value=100)
    closed_on = serializers.DateField

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.profile.org

    def validate_name(self, name):
        if self.instance:
            if (
                Lender.objects.filter(name__iexact=name, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Lender already exists with this name"
                )

        else:
            if Lender.objects.filter(name__iexact=name, org=self.org).exists():
                raise serializers.ValidationError(
                    "Lender already exists with this name"
                )
        return name

    class Meta:
        model = Lender
        fields = "__all__"

class LenderCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lender
        fields = "__all__"