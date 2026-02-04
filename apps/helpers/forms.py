from django.forms import BaseInlineFormSet
from django.forms.formsets import TOTAL_FORM_COUNT


class SensibleFormset(BaseInlineFormSet):
    def total_form_count(self):
        """Returns the total number of forms in this FormSet."""
        if self.data or self.files:
            return self.management_form.cleaned_data[TOTAL_FORM_COUNT]
        else:
            if self.initial_form_count() > 0:
                total_forms = self.initial_form_count()
            else:
                total_forms = self.initial_form_count() + self.extra
            if total_forms > self.max_num > 0:
                total_forms = self.max_num
            return total_forms
