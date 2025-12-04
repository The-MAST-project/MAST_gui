from django import forms
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _

class UserRegistrationForm(forms.Form):
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
    
    TITLE_CHOICES = [
        ('', '-- Select Title (Optional) --'),
        ('dr', _('Dr.')),
        ('prof', _('Prof.')),
        ('prof_dr', _('Prof. Dr.')),
        ('mr', _('Mr.')),
        ('ms', _('Ms.')),
        ('mx', _('Mx.')),
    ]
    
    title = forms.ChoiceField(
        label=_("Title"),
        choices=TITLE_CHOICES,
        required=False,
        help_text=_("Optional: Academic or professional title")
    )
    
    # International name fields (Western and Eastern order support)
    given_name = forms.CharField(
        label=_("Given Name(s)"),
        max_length=100,
        required=True,
        help_text=_("First and middle names (e.g., 'John William' or '明')"),
        widget=forms.TextInput(attrs={
            'placeholder': 'John William',
            'autocomplete': 'given-name'
        })
    )
    
    family_name = forms.CharField(
        label=_("Family Name"),
        max_length=100,
        required=True,
        help_text=_("Last name or surname (e.g., 'Smith' or '李')"),
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
    
    POSITION_CHOICES = [
        ('', '-- Select Position --'),
        ('undergrad', _('Undergraduate Student')),
        ('graduate', _('Graduate Student')),
        ('postdoc', _('Postdoctoral Researcher')),
        ('staff', _('Staff Scientist/Engineer')),
        ('faculty', _('Faculty/Principal Investigator')),
        ('emeritus', _('Emeritus/Retired')),
        ('other', _('Other'))
    ]
    
    position = forms.ChoiceField(
        label=_("Position"),
        choices=POSITION_CHOICES,
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
    INTENDED_USE_CHOICES = [
        ('', '-- Select Primary Use --'),
        ('observation', _('Active observations')),
        ('data_analysis', _('Data access and analysis')),
        ('collaboration', _('Collaboration/co-investigator')),
        ('education', _('Educational purposes')),
        ('technical', _('Technical support/development')),
        ('other', _('Other'))
    ]
    
    intended_use = forms.ChoiceField(
        label=_("Intended Use"),
        choices=INTENDED_USE_CHOICES,
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
