from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """
    Form used to register users with email authentication.
    """

    email = forms.EmailField(
        label="Email",
        error_messages={
            "required": "Informe o email.",
            "invalid": "Informe um email válido.",
        },
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite seu email",
                "autocomplete": "email",
            }
        ),
    )

    first_name = forms.CharField(
        label="Nome",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite seu nome",
                "autocomplete": "given-name",
            }
        ),
    )

    last_name = forms.CharField(
        label="Sobrenome",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite seu sobrenome",
                "autocomplete": "family-name",
            }
        ),
    )

    password1 = forms.CharField(
        label="Senha",
        error_messages={
            "required": "Informe uma senha.",
        },
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite sua senha",
                "autocomplete": "new-password",
            }
        ),
    )

    password2 = forms.CharField(
        label="Confirmar senha",
        error_messages={
            "required": "Confirme sua senha.",
        },
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite a senha novamente",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]

    def clean_email(self):
        """
        Validate if email is unique.
        """
        email = self.cleaned_data.get("email")

        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email já está cadastrado.")

        return email


class EmailAuthenticationForm(forms.Form):
    """
    Form used to authenticate users with email and password.
    """

    email = forms.EmailField(
        label="Email",
        error_messages={
            "required": "Informe seu email.",
            "invalid": "Informe um email válido.",
        },
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite seu email",
                "autocomplete": "email",
                "autofocus": True,
            }
        ),
    )

    password = forms.CharField(
        label="Senha",
        error_messages={
            "required": "Informe sua senha.",
        },
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite sua senha",
                "autocomplete": "current-password",
            }
        ),
    )

    def clean(self):
        """
        Validate email and password using Django authentication system.
        """
        cleaned_data = super().clean()

        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user = authenticate(
                username=email,
                password=password,
            )

            if self.user is None:
                raise forms.ValidationError("Email ou senha inválidos.")

            if not self.user.is_active:
                raise forms.ValidationError("Esta conta está inativa.")

        return cleaned_data

    def get_user(self):
        """
        Return the authenticated user.
        """
        return self.user
