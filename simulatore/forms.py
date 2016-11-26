from django import forms
import datetime


class FormTakeSingolo(forms.Form):
    def __init__(self, *args, **kwargs):
        self.data_oggi = datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y")
        self.data_max = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(days=15),
                                                   "%d/%m/%Y")
        self.request = kwargs.pop('request')
        self.isin_conf = kwargs.pop('isin_conf')
        if self.request.user.is_authenticated and self.request.user.has_perm('simulatore.take_fisso'):
            self.id_data_inizio = 'crea_singolo_data_inizio_libero'
            self.id_data_fine = 'crea_singolo_data_fine_libero'
            if self.request.session.get('data_inizio') and self.request.session.get('data_fine'):
                self.default_data_inizio = self.request.session['data_inizio']
                self.default_data_fine = self.request.session['data_fine']
            else:
                self.default_data_inizio = datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y")
                self.default_data_fine = datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y")
        else:
            self.id_data_inizio = 'crea_singolo_data_inizio_limitato'
            self.id_data_fine = 'crea_singolo_data_fine_limitato'
            if self.request.session.get('data_inizio') and self.request.session.get('data_fine'):
                self.default_data_inizio = self.request.session['data_inizio']
                self.default_data_fine = self.request.session['data_fine']
            else:
                self.default_data_fine = datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y")
                self.default_data_inizio = datetime.datetime.strftime(
                    datetime.date.today() - datetime.timedelta(days=15), "%d/%m/%Y")
        if self.request.session.get('in_carico') == 0:
            self.in_carico = 0
        elif self.request.session.get('in_carico'):
            self.in_carico = self.request.session.get('in_carico')
        else:
            self.in_carico = None
        super(FormTakeSingolo, self).__init__(*args, **kwargs)
        self.fields['isin'] = forms.ChoiceField(widget=forms.Select(attrs={'id': 'isin', 'class': 'form-control'}),
                                                choices=self.isin_conf, label='Titolo',
                                                initial=self.request.session.get('isin'))
        self.fields['crea_data_inizio'] = forms.CharField(
            widget=forms.TextInput(attrs={'id': self.id_data_inizio, 'class': 'form-control'}),
            initial=self.default_data_inizio, label='Data inizio', required=False)
        self.fields['crea_data_fine'] = forms.CharField(
            widget=forms.TextInput(attrs={'id': self.id_data_fine, 'class': 'form-control'}),
            initial=self.default_data_fine, label='Data fine', required=False)
        self.fields['crea_limite_inferiore'] = forms.DecimalField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 5.0}),
            initial=self.request.session.get('limite_inferiore'), decimal_places=4)
        self.fields['crea_limite_superiore'] = forms.DecimalField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 10.0}),
            initial=self.request.session.get('limite_superiore'), decimal_places=4)
        self.fields['primo_acquisto'] = forms.DecimalField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 6.0}),
            initial=self.request.session.get('primo_acquisto'), decimal_places=4)
        self.fields['in_carico'] = forms.IntegerField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 1, 'placeholder': 10}),
            initial=self.in_carico)
        self.fields['step'] = forms.DecimalField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 0.1}),
            initial=self.request.session.get('step'), decimal_places=4)
        self.fields['take'] = forms.DecimalField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 0.1}),
            initial=self.request.session.get('take_inizio'), decimal_places=4)
        self.fields['quantita_acquisto'] = forms.IntegerField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 1, 'placeholder': 100}),
            initial=self.request.session.get('quantita_acquisto'))
        self.fields['quantita_vendita'] = forms.IntegerField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 1, 'placeholder': 100}),
            initial=self.request.session.get('quantita_vendita'))
        self.fields['commissioni_tipo'] = forms.ChoiceField(
            widget=forms.Select(attrs={'id': 'commissioni_tipo', 'class': 'form-control'}),
            choices=[('P', 'Percentuale'), ('F', 'Fissa')], label='Tipo commissioni',
            initial=self.request.session.get('tipo_commissione'))
        self.fields['commissioni_importo'] = forms.DecimalField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 0.19}),
            initial=self.request.session.get('commissione'), decimal_places=4)
        self.fields['commissioni_min'] = forms.DecimalField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 1}),
            initial=self.request.session.get('min_commissione'), decimal_places=4)
        self.fields['commissioni_max'] = forms.DecimalField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 18}),
            initial=self.request.session.get('max_commissione'), decimal_places=4)
        # self.fields['aggiustamento'] = forms.BooleanField(
        #     widget=forms.CheckboxInput)
        self.fields['aggiustamento'] = forms.ChoiceField(
            widget=forms.Select(attrs={'id': 'aggiustamento', 'class': 'form-control'}),
            choices=[(True, 'Sì'), (False, 'No')], label='Aggiustamento',
            initial=self.request.session.get('aggiustamento'))
        self.fields['aggiustamento_step'] = forms.IntegerField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 1, 'placeholder': 2}),
            initial=self.request.session.get('aggiustamento_step'))
        self.fields['aggiustamento_limite_inferiore'] = forms.DecimalField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 4}),
            initial=self.request.session.get('aggiustamento_limite_inferiore'), label='Agg. limite inferiore')
        self.fields['aggiustamento_limite_superiore'] = forms.DecimalField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 2}),
            initial=self.request.session.get('aggiustamento_limite_superiore'), label='Agg. limite superiore')
        self.fields['capitale'] = forms.DecimalField(
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 20000}),
            initial=self.request.session.get('capitale'), label='Capitale iniziale')

    def clean_crea_data_inizio(self):

        if not self.request.user.is_authenticated and not self.request.user.has_perm('simulatore.take_fisso') and \
                        self.cleaned_data.get('crea_data_inizio', '') < (datetime.datetime.today() -
                                                                         datetime.timedelta(days=15)):
            raise ValidationError("La data inizio non è permessa.")

        return self.cleaned_data.get('crea_data_inizio', '')


class FormTakeVariabile(forms.Form):
    def __init__(self, *args, **kwargs):
        self.data_oggi = datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y")
        self.data_max = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(days=15),
                                                   "%d/%m/%Y")
        self.request = kwargs.pop('request')
        self.isin_conf = kwargs.pop('isin_conf')
        if self.request.user.is_authenticated and self.request.user.has_perm('simulatore.take_variabile'):
            self.id_data_inizio = 'crea_variabile_data_inizio_libero'
            self.id_data_fine = 'crea_variabile_data_fine_libero'
            if self.request.session.get('data_inizio') and self.request.session.get('data_fine'):
                self.default_data_inizio = self.request.session['data_inizio']
                self.default_data_fine = self.request.session['data_fine']
            else:
                self.default_data_inizio = datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y")
                self.default_data_fine = datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y")
        else:
            self.default_data_inizio = datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y")
            self.default_data_fine = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(days=15),
                                                                "%d/%m/%Y")
        if self.request.session.get('in_carico') == 0:
            self.in_carico = 0
        elif self.request.session.get('in_carico'):
            self.in_carico = self.request.session.get('in_carico')
        else:
            self.in_carico = None
        if self.request.user.is_authenticated and self.request.user.has_perm('simulatore.take_variabile'):
            super(FormTakeVariabile, self).__init__(*args, **kwargs)
            self.fields['isin'] = forms.ChoiceField(widget=forms.Select(attrs={'id': 'isin', 'class': 'form-control'}),
                                                    choices=self.isin_conf, label='Titolo',
                                                    initial=self.request.session.get('isin'))
            self.fields['crea_data_inizio'] = forms.CharField(
                widget=forms.TextInput(attrs={'id': self.id_data_inizio, 'class': 'form-control'}),
                initial=self.default_data_inizio, label='Data inizio', required=False)
            self.fields['crea_data_fine'] = forms.CharField(
                widget=forms.TextInput(attrs={'id': self.id_data_fine, 'class': 'form-control'}),
                initial=self.default_data_fine, label='Data fine', required=False)
            self.fields['crea_limite_inferiore'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 5.0}),
                initial=self.request.session.get('limite_inferiore'), decimal_places=4)
            self.fields['crea_limite_superiore'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 10.0}),
                initial=self.request.session.get('limite_superiore'), decimal_places=4)
            self.fields['primo_acquisto'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 6.0}),
                initial=self.request.session.get('primo_acquisto'), decimal_places=4)
            self.fields['in_carico'] = forms.IntegerField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 1, 'placeholder': 10}),
                initial=self.in_carico)
            self.fields['step'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 0.1}),
                initial=self.request.session.get('step'), decimal_places=4)
            self.fields['take_inizio'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 6.0}),
                initial=self.request.session.get('take_inizio'), decimal_places=4)
            self.fields['take_fine'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 6.0}),
                initial=self.request.session.get('take_fine'), decimal_places=4)
            self.fields['take_incremento'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 6.0}),
                initial=self.request.session.get('take_incremento'), decimal_places=4)
            self.fields['quantita_acquisto'] = forms.IntegerField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 1, 'placeholder': 100}),
                initial=self.request.session.get('quantita_acquisto'))
            self.fields['quantita_vendita'] = forms.IntegerField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 1, 'placeholder': 100}),
                initial=self.request.session.get('quantita_vendita'))
            self.fields['commissioni_tipo'] = forms.ChoiceField(
                widget=forms.Select(attrs={'id': 'commissioni_tipo', 'class': 'form-control'}),
                choices=[('P', 'Percentuale'), ('F', 'Fissa')], label='Tipo commissioni',
                initial=self.request.session.get('tipo_commissione'))
            self.fields['commissioni_importo'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 0.19}),
                initial=self.request.session.get('commissione'), decimal_places=4)
            self.fields['commissioni_min'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 1}),
                initial=self.request.session.get('min_commissione'), decimal_places=4)
            self.fields['commissioni_max'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 18}),
                initial=self.request.session.get('max_commissione'), decimal_places=4)
            self.fields['autoaggiustamento_step'] = forms.IntegerField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 1, 'placeholder': 2}),
                initial=self.request.session.get('autoaggiustamento_step'))
            self.fields['autoaggiustamento_limite_inferiore'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 4.0}),
                initial=self.request.session.get('autoaggiustamento_limite_inferiore'), decimal_places=4)
            self.fields['autoaggiustamento_limite_superiore'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 11.0}),
                initial=self.request.session.get('autoaggiustamento_limite_superiore'), decimal_places=4)


class FormCostruzione(forms.Form):
    def __init__(self, *args, **kwargs):
        self.data_oggi = datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y")
        self.request = kwargs.pop('request')
        if self.request.user.is_authenticated and self.request.user.has_perm('simulatore.take_variabile'):
            super(FormCostruzione, self).__init__(*args, **kwargs)
            self.fields['primo_acquisto'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 6.0}),
                initial=self.request.session.get('costruisci_primo_acquisto'), decimal_places=4)
            self.fields['step_iniziale'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 0.01}),
                initial=self.request.session.get('costruisci_step_iniziale'), decimal_places=4)
            self.fields['step_finale'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 0.5}),
                initial=self.request.session.get('costruisci_step_finale'), decimal_places=4)
            self.fields['incremento_step'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.0001, 'placeholder': 0.01}),
                initial=self.request.session.get('costruisci_incremento_step'), decimal_places=4)
            self.fields['copertura'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01, 'placeholder': 0.30}),
                initial=self.request.session.get('costruisci_copertura'), decimal_places=2)
            self.fields['capitale'] = forms.IntegerField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 1, 'placeholder': 20000}),
                initial=self.request.session.get('costruisci_capitale'))
