from django import forms

class UploadDataFileForm(forms.Form):
    data_file = forms.FileField()