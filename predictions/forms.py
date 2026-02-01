from django import forms
from .models import Prediction, Driver


class PredictionForm(forms.ModelForm):
    """Form for creating/editing a race prediction."""

    class Meta:
        model = Prediction
        fields = ["p1", "p2", "p3", "p4", "p5", "alonso_pos_guess"]

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

        # Alonso position field (0=DNF, 1-20)
        alonso_choices = [(0, "DNF")] + [(i, str(i)) for i in range(1, 21)]
        self.fields["alonso_pos_guess"] = forms.ChoiceField(
            choices=alonso_choices,
            label="Posición de Alonso",
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
