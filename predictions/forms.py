from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Prediction, Driver


class SignupForm(UserCreationForm):
    """Custom signup form with required unique email."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "tu@email.com"}),
        help_text="Requerido. Introduce un email valido.",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to all fields
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "usuario"})
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "********"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "********"})

    def clean_email(self):
        """Enforce unique email (case-insensitive)."""
        email = self.cleaned_data.get("email", "").lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class PredictionForm(forms.ModelForm):
    """Form for creating/editing a race prediction."""

    class Meta:
        model = Prediction
        fields = ["p1", "p2", "p3", "p4", "p5", "alonso_pos_guess", "sainz_pos_guess"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get active drivers with team for display
        drivers = Driver.objects.filter(active=True).select_related("team")
        driver_choices = [(d.pk, f"{d.name} ({d.team.name})" if d.team else d.name) for d in drivers]

        # Apply to p1-p5 fields
        for i in range(1, 6):
            field_name = f"p{i}"
            self.fields[field_name].queryset = drivers
            self.fields[field_name].label = f"P{i}"
            self.fields[field_name].widget = forms.Select(
                attrs={"class": "form-select"},
                choices=[("", f"-- Selecciona P{i} --")] + driver_choices,
            )
            self.fields[field_name].empty_label = None

        pos_choices = [(0, "DNF")] + [(i, str(i)) for i in range(1, 21)]

        self.fields["alonso_pos_guess"] = forms.ChoiceField(
            choices=pos_choices,
            label="Posicion de Alonso",
            widget=forms.Select(attrs={"class": "form-select"}),
        )

        self.fields["sainz_pos_guess"] = forms.ChoiceField(
            choices=pos_choices,
            label="Posicion de Sainz",
            widget=forms.Select(attrs={"class": "form-select"}),
        )

    def clean(self):
        cleaned_data = super().clean()

        # Validate no repeated drivers
        picks = []
        for i in range(1, 6):
            driver = cleaned_data.get(f"p{i}")
            if driver:
                if driver.pk in picks:
                    raise forms.ValidationError("No puedes repetir pilotos en tu Top 5.")
                picks.append(driver.pk)

        return cleaned_data
