from datetime import date
from rest_framework import serializers
from .models import UserProfile
import re

PHONE_RE = re.compile(r'^\+?\d{10,15}$')

class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'auth_id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone', 'date_of_birth', 'gender', 'address',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        if self.instance:
            for f in ('auth_id', 'email', 'username'):
                if f in attrs and attrs[f] != getattr(self.instance, f):
                    raise serializers.ValidationError({f: 'This field cannot be updated.'})
        return attrs

    def validate_date_of_birth(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value
    
    def validate_first_name(self, value):
        if value and len(value) > 50:
            raise serializers.ValidationError("First name too long (max 50).")
        return value

    def validate_last_name(self, value):
        if value and len(value) > 50:
            raise serializers.ValidationError("Last name too long (max 50).")
        return value
    
    def validate_phone(self, value):
        if not value:
            return value

        v = re.sub(r'[ \-()\u00A0]', '', str(value)).strip()

        if not PHONE_RE.fullmatch(v):
            raise serializers.ValidationError("Phone must be 10–15 digits, optional leading +.")

        qs = UserProfile.objects.filter(phone=v)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This phone is already in use.")

        return v


    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or None