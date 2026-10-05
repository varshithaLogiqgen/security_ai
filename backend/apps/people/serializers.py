from rest_framework import serializers

def person(user):
    return {'id':str(user.pk),'name':user.name,'email':user.email,'title':user.title,'team':user.directory_team,'bio':user.bio}

class WorkProfileInput(serializers.Serializer):
    bio = serializers.CharField(max_length=1000,allow_blank=True)

class PersonalInput(serializers.Serializer):
    phone = serializers.CharField(max_length=40,allow_blank=True)
    address = serializers.CharField(max_length=1000,allow_blank=True)
    emergency_contact = serializers.CharField(max_length=300,allow_blank=True)
