
#################################################################################################################################
#     @file     :    form.py   
#
#     @brief    :    Django forms 
#
#     @authors  :    Madi Davis (madelind@andrew.cmu.edu) & Aishwarya Yadav (ayadav2@andrew.cmu.edu)
#################################################################################################################################

# ------------------------------------------------------------------------------------------------------------------------------#
# --- INCLUDES --- #
# ------------------------------------------------------------------------------------------------------------------------------#from django import forms
### Django Modules ####
from django import forms
from django.contrib.auth import authenticate
from soft17.models import Profile



# ------------------------------------------------------------------------------------------------------------------------------#
# --- LOGIN FORMS --- #
# ------------------------------------------------------------------------------------------------------------------------------#
class LoginForm(forms.Form):
    #############################################################################################################################
    # @brief      :       Creates django form class for user logins
    #############################################################################################################################
    username = forms.CharField(max_length = 20)                                         #< Unique Username Input for Site
    password = forms.CharField(max_length = 200, widget=forms.PasswordInput())          #< Unique User Password

    # -- CLASS METHODS -- #
    """
        @brief      :       Custom form validation that applies to multiple fields
        @note       :       Overrides the forms.Form.clean function
    """
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super().clean()

        # Confirm the Password is correct for given username
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise forms.ValidationError("Invalid Username/Password")

        return cleaned_data



# ------------------------------------------------------------------------------------------------------------------------------#
# --- REGISTRATION FORMS --- #
# ------------------------------------------------------------------------------------------------------------------------------#
class RegisterForm(forms.Form):  
    #############################################################################################################################
    # @brief      :       Creates django form class for user account registration
    #############################################################################################################################
    username = forms.CharField(max_length = 20)                                             #< Unique Username Input for Site
    password = forms.CharField(max_length = 200, widget=forms.PasswordInput())              #< Unique User Password
    confirm_password =  forms.CharField(max_length = 200, widget=forms.PasswordInput())     #< Password Confirmation Input
    email = forms.CharField(max_length = 50, widget= forms.EmailInput())                    #< Email Linked to User Account
    first_name = forms.CharField(max_length = 20)                                           #< User's First Name
    last_name = forms.CharField(max_length = 20)                                            #< User's Last Name 


    # -- CLASS METHODS -- #
    """
        @brief      :       Custom form validation that applies to multiple fields
        @note       :       Overrides the forms.Form.clean function
    """
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super().clean()

        # Confirm the Password fields match
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if (password and confirm_password) and (password != confirm_password):
            raise forms.ValidationError("Passwords did not Match")

        return cleaned_data



# ------------------------------------------------------------------------------------------------------------------------------#
# --- PROFILE FORM --- #
# ------------------------------------------------------------------------------------------------------------------------------#
class ProfileForm(forms.ModelForm):
    user_picture = forms.FileField(required=False)
    class Meta:
        model = Profile
        exclude = (
            'content_type',
            'profile_user',
            'multiplayer_room',
            'single_player_room'
        )

    def clean_user_picture(self):
        picture = self.cleaned_data['user_picture']
        if picture:
            if not picture.content_type or not picture.content_type.startswith('image'):
                raise forms.ValidationError('File type is not image')
            if picture.size > 2500000:
                raise forms.ValidationError('File too big (max size is {0} bytes)'.format(2500000))
        return picture
