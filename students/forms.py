from django import forms
from .models import StudentProfile


class StudentProfileForm(forms.ModelForm):

    class Meta:
        model = StudentProfile

        fields = [
            'user',
            'student_code',
            'gender',
            'date_of_birth',
            'qualification',
            'college_name',
            'passing_year',
            'address',
            'profile_photo',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date'}
            ),

            'address': forms.Textarea(
                attrs={'rows': 3}
            ),
        }