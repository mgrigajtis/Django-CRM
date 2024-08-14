from rest_framework import serializers

from accounts.models import Tags
from accounts.serializer import AccountSerializer
from common.serializer import AttachmentsSerializer, ProfileSerializer,UserSerializer
from contacts.serializer import ContactSerializer
from opportunity.models import Opportunity, CommercialIntake
from teams.serializer import TeamsSerializer


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class CommercialIntakeSerializer:
    class Meta:
        model = CommercialIntake
        fields = "__all__"


class OpportunitySerializer(serializers.ModelSerializer):
    closed_by = ProfileSerializer()
    created_by = UserSerializer()
    tags = TagsSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    opportunity_attachment = AttachmentsSerializer(read_only=True, many=True)

    class Meta:
        model = Opportunity
        fields = "__all__"
    


class OpportunityCreateSerializer(serializers.ModelSerializer):
    closed_on = serializers.DateField

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.profile.org

    class Meta:
        model = Opportunity
        fields = "__all__"

class OpportunityCreateSwaggerSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField()
    opportunity_attachment = serializers.FileField()
    class Meta:
        model = Opportunity
        fields = "__all__"

class OpportunityDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    opportunity_attachment = serializers.FileField()

class OpportunityCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
