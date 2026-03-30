from django import forms
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User
from django.contrib.auth.models import Group


class RegistrationForm(forms.ModelForm):
    """
    Comprehensive academic user registration form
    Supports international naming conventions and academic affiliations
    """
    
    # === Personal Information ===
    email = forms.EmailField(
        label=_("Email Address"),
        max_length=254,
        required=True,
        validators=[EmailValidator()],
        help_text=_("Your institutional or personal email address"),
        widget=forms.EmailInput(attrs={
            'placeholder': 'name@institution.edu',
            'autocomplete': 'email'
        })
    )
    
    prefix = forms.CharField(
        label=_("Prefix"),
        max_length=32,
        required=False,
        help_text=_("Optional: e.g. Dr, Prof, Mr, Mrs")
    )

    first_name = forms.CharField(
        label=_("First Name"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'John',
            'autocomplete': 'given-name'
        })
    )

    middle = forms.CharField(
        label=_("Middle Name"),
        max_length=64,
        required=False,
    )

    last_name = forms.CharField(
        label=_("Last Name"),
        max_length=100,
        required=True,
        help_text=_("Surname (e.g., 'Smith' or '李')"),
        widget=forms.TextInput(attrs={
            'placeholder': 'Smith',
            'autocomplete': 'family-name'
        })
    )

    preferred_name = forms.CharField(
        label=_("Preferred Name"),
        max_length=100,
        required=False,
        help_text=_("Optional: How you'd like to be addressed"),
        widget=forms.TextInput(attrs={
            'placeholder': 'Optional'
        })
    )
    
    # === Academic Affiliation ===
    institution = forms.CharField(
        label=_("Institution"),
        max_length=200,
        required=True,
        help_text=_("University, research center, or organization"),
        widget=forms.TextInput(attrs={
            'placeholder': 'Weizmann Institute of Science',
            'autocomplete': 'organization'
        })
    )
    
    department = forms.CharField(
        label=_("Department/Unit"),
        max_length=200,
        required=False,
        help_text=_("Optional: Department, lab, or group"),
        widget=forms.TextInput(attrs={
            'placeholder': 'Particle Physics and Astrophysics'
        })
    )
    
    position = forms.ChoiceField(
        label=_("Position"),
        choices=[
            ('', '-- Select Position --'),
            ('undergrad', _('Undergraduate Student')),
            ('graduate', _('Graduate Student')),
            ('postdoc', _('Postdoctoral Researcher')),
            ('staff', _('Staff Scientist/Engineer')),
            ('faculty', _('Faculty/Principal Investigator')),
            ('emeritus', _('Emeritus/Retired')),
            ('other', _('Other'))
        ],
        required=True,
        help_text=_("Your current academic or research position")
    )
    
    # === Research Information ===
    ORCID_REGEX = r'^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$'
    
    orcid = forms.CharField(
        label=_("ORCID iD"),
        max_length=19,
        required=False,
        help_text=_("Optional: Your ORCID identifier (e.g., 0000-0002-1825-0097)"),
        widget=forms.TextInput(attrs={
            'placeholder': '0000-0002-1825-0097',
            'pattern': ORCID_REGEX
        })
    )
    
    research_interests = forms.CharField(
        label=_("Research Interests"),
        max_length=500,
        required=False,
        help_text=_("Optional: Brief description of your research focus"),
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'e.g., Time-domain astronomy, spectroscopy of transients, stellar evolution'
        })
    )
    
    # === Contact & Location ===
    country = forms.CharField(
        label=_("Country"),
        max_length=100,
        required=True,
        help_text=_("Country of your institution"),
        widget=forms.TextInput(attrs={
            'placeholder': 'Israel',
            'autocomplete': 'country-name'
        })
    )
    
    # === Account Purpose ===
    intended_use = forms.ChoiceField(
        label=_("Intended Use"),
        choices=[
            ('', '-- Select Primary Use --'),
            ('observation', _('Active observations')),
            ('data_analysis', _('Data access and analysis')),
            ('collaboration', _('Collaboration/co-investigator')),
            ('education', _('Educational purposes')),
            ('technical', _('Technical support/development')),
            ('other', _('Other'))
        ],
        required=True,
        help_text=_("How do you plan to use MAST?")
    )
    
    additional_info = forms.CharField(
        label=_("Additional Information"),
        max_length=1000,
        required=False,
        help_text=_("Optional: Any additional context for your access request"),
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'e.g., Collaboration details, project information'
        })
    )
    
    # === Terms & Conditions ===
    agree_terms = forms.BooleanField(
        label=_("I agree to the MAST Terms of Use and Data Policy"),
        required=True,
        error_messages={
            'required': _('You must agree to the terms to create an account')
        }
    )
    
    agree_citation = forms.BooleanField(
        label=_("I agree to acknowledge MAST in publications using this data"),
        required=True,
        error_messages={
            'required': _('Citation agreement is required')
        }
    )

    # === Additional Registration Fields ===
    username = forms.CharField(
        label=_("Username"),
        max_length=64,
        required=True,
        help_text=_("Choose a unique username for your account"),
        widget=forms.TextInput(attrs={
            'placeholder': 'johndoe',
            'autocomplete': 'username'
        })
    )
    
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        initial=lambda: Group.objects.filter(name='everybody'),
        label=_("User Groups"),
        help_text=_("Optional: Select groups you wish to join")
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'prefix', 'first_name', 'middle', 'last_name', 'email', 'affiliation', 'groups']

class LocalSignupForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        label="Email address",
        help_text="Required. This will be used as your username."
    )
    first_name = forms.CharField(max_length=30, required=True, label="First name")
    last_name = forms.CharField(max_length=30, required=True, label="Last name")
    affiliation = forms.CharField(max_length=100, required=True, label="Affiliation")
    phone = forms.CharField(max_length=30, required=False, label="Phone number")
    country = forms.CharField(max_length=50, required=False, label="Country")
    city = forms.CharField(max_length=50, required=False, label="City")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "email", "first_name", "last_name", "affiliation",
            "phone", "country", "city", "password1", "password2"
        )

class ProfileForm(forms.ModelForm):
    prefix = forms.CharField(max_length=32, required=False, label="Prefix",
        help_text="e.g. Dr, Prof, Mr, Mrs")
    first_name = forms.CharField(max_length=64, required=False, label="First name")
    middle = forms.CharField(max_length=64, required=False, label="Middle name")
    last_name = forms.CharField(max_length=64, required=False, label="Last name")
    email = forms.EmailField(max_length=254, required=False, label="Email")
    affiliation = forms.CharField(max_length=128, required=False, label="Affiliation")
    username = forms.CharField(max_length=150, required=True, label="Username")
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.exclude(name='Everybody'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Groups",
    )

    class Meta:
        model = User
        fields = ("username", "prefix", "first_name", "middle", "last_name",
                  "email", "affiliation", "groups")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'groups':
                field.widget.attrs.setdefault('class', 'form-control form-control-sm')

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            everybody = Group.objects.get(name='Everybody')
            user.groups.add(everybody)
        return user
