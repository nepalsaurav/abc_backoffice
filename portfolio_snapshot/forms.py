from django import forms

class ImportTransactionsForm(forms.Form):
    file = forms.FileField(
        label='Upload File (CSV/Excel)',
        help_text='Please upload your daily broker transaction export.',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.csv, .xlsx, .xls'
        })
    )
