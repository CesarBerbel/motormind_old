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




class AdministrativeUserForm(forms.ModelForm):
    """
    Form used by administrators to create and update internal employee users.

    Superuser creation is intentionally not available here. A superuser must be
    created only by the Django createsuperuser command. Customer users must be
    created by the customer/portal flow, not by the internal employee form.
    """

    groups = forms.ModelMultipleChoiceField(
        label="Perfis de acesso",
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    password1 = forms.CharField(
        label="Senha",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
    )

    password2 = forms.CharField(
        label="Confirmar senha",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
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
            "is_active",
            "groups",
        ]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        from django.contrib.auth.models import Group

        super().__init__(*args, **kwargs)
        self.fields["groups"].queryset = Group.objects.order_by("name")

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if not email:
            return email

        query = User.objects.filter(email=email)

        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise forms.ValidationError("Este email já está cadastrado para outro usuário.")

        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if self.instance and self.instance.pk:
            if self.instance.is_superuser:
                raise forms.ValidationError(
                    "Superuser não pode ser gerenciado por esta tela. Use apenas comandos administrativos."
                )

            if self.instance.is_customer:
                raise forms.ValidationError(
                    "Usuário de cliente não pode ser gerenciado pela tela de funcionários."
                )

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("As senhas informadas não conferem.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        user.is_customer = False
        user.is_employee = True

        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)

        if commit:
            user.save()
            self.save_m2m()

        return user
