from django import forms
from django.conf import settings
from django.db import models
from django.forms.widgets import HiddenInput
from django.template.defaultfilters import filesizeformat, slugify
from django.utils.encoding import smart_str
from django.utils.html import strip_tags
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.forms import BooleanField, ChoiceField, FileField

from contactform.fields import PickledObjectField
from contactform.settings import MAX_FILE_SIZE
from contactform.field_loader import WIDGET_TYPES, FIELD_TYPES, load_class, TitlePseudoField
from contactform import south_introspections

from cms.models import Page
from django.utils.translation import gettext_lazy as _


def _site_contact_email():
    if 'siteinfo' in settings.INSTALLED_APPS:
        try:
            from siteinfo.models import SiteSettings
            site_contact_email = SiteSettings.objects.get_current().email
        except:
            site_contact_email = 'n/a'
    else:
        site_contact_email = 'n/a'
    return site_contact_email


site_contact_email = lazy(_site_contact_email, str)


def _make_helper(layout_fields):
    from uni_form.helpers import Layout, Fieldset, FormHelper
    helper = FormHelper()
    helper.add_layout(Layout(*[str(field) if isinstance(field, str) else field for field in layout_fields]))
    return helper


class ContactForm(models.Model):
    language = models.CharField(_('language'), max_length=15, choices=settings.LANGUAGES)
    name = models.CharField(_('name'), max_length=255)
    title = models.CharField(_('title'), max_length=255, null=True, blank=True)
    description = models.TextField(_('description'), blank=True)
    submit_label = models.CharField(_('submit label'), max_length=30, blank=True,
                                    help_text='%s: "%s"' % (_('default'), _('submit')))
    success_message = models.TextField(_('success message'), blank=True)
    recipients = models.ManyToManyField('Recipient', verbose_name=_('recipients'))
    cc_managers = models.BooleanField(_('CC to managers'), default=False, help_text=_(
        'Check to send a copy to the site managers (%s).' % (','.join([manager[1] for manager in settings.MANAGERS]))))
    cc_site_contact = models.BooleanField(_('CC to site contact'), default=False, help_text=_(
        'Check to send a copy to the site contact (%s).' % (site_contact_email)))
    has_captcha = models.BooleanField(_("has a captcha"), default=False, help_text=_(
        "Should the user be required to fill up a captcha to verify he is human?"))
    css_class = models.CharField(_('CSS class'), null=True, blank=True, max_length=255)
    # this sucks, because it makes this app depend on the cms :-(
    success_page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.CASCADE)
    notification_email_subject = models.CharField(
        verbose_name=_('notification email subject'),
        max_length=200,
        blank=True
    )
    notification_email_body = models.TextField(
        verbose_name=_('notification email body'),
        blank=True
    )

    def __str__(self):
        return '%s (%s)' % (self.name, self.language)

    def get_form_base_class(self):
        from .forms import ContactFormFormBase

        return ContactFormFormBase

    def get_form_class(self, unique_form_id=None):
        """
        Constructs a real django.forms Form() class out of this ContactForm instance and provides
        functionality for handling form submission.
        """

        ContactFormFormBase = self.get_form_base_class()

        attrs = {
            'model_instance_id': self.id,
            'contactform_id': forms.CharField(initial=self.pk, widget=HiddenInput),
            'model': self.__class__,
        }
        if unique_form_id:
            attrs['unique_form_id'] = forms.CharField(initial=unique_form_id, widget=HiddenInput)

        count = -1
        layout = ["contactform_id"]

        for field in self.field_set.all().order_by("position"):
            count += 1
            if field.widget == '':
                widget = None
            else:
                widget = load_class(field.widget)
            label = field.label
            field_class = load_class(field.field_type)
            if issubclass(field_class, BooleanField):
                label = mark_safe(label)
                if field.initial and field.initial.lower() in ['1', 'checked', 'yes', 'true']:
                    checked = True
                else:
                    checked = False
                form_field = field_class(required=field.required, widget=widget, label=label, initial=checked)
            elif issubclass(field_class, ChoiceField):
                txt_choices = field.choices.replace('\n', '').replace('\r', '').split(';')
                choices = []
                for txt in txt_choices:
                    txt = txt.strip()
                    if txt != '':
                        choices.append((slugify(strip_tags(txt)), mark_safe(txt)))
                try:
                    initial = choices[int(field.initial.strip()) - 1][0]
                except:
                    initial = None
                form_field = field_class(required=field.required, widget=widget,
                                         label=label, initial=initial,
                                         choices=choices)
                # ..., initial=field.initial, help_text=field.help_text)
            elif issubclass(field_class, FileField):
                form_field = field_class(required=field.required, widget=widget,
                                         label='%s (%s %s)' % (label, _('max.'), filesizeformat(MAX_FILE_SIZE)),
                                         initial=field.initial)
                # ..., initial=field.initial, help_text=field.help_text)
            elif field_class is TitlePseudoField:
                if "uni_form" in settings.INSTALLED_APPS:
                    from uni_form.helpers import HTML
                    layout.append(HTML("<h3>%s</h3>" % label))
                continue
            else:
                form_field = field_class(required=field.required, widget=widget,
                                         label=label, initial=field.initial)
                # ... , initial=field.initial, help_text=field.help_text)
            layout.append("%s_%s" % (slugify(field.label), count))
            if field.css_class:
                form_field.widget.attrs['class'] = field.css_class
            attrs["%s_%s" % (slugify(field.label), count)] = form_field

        has_captcha = 'captcha' in settings.INSTALLED_APPS and self.has_captcha
        attrs['has_captcha'] = has_captcha

        if has_captcha:
            from captcha.fields import CaptchaField
            attrs['captcha'] = CaptchaField(label=_("Enter the characters showed in the image below."))

        if "uni_form" in settings.INSTALLED_APPS:
            attrs['uni_form_helper'] = _make_helper(layout)

        form_class = type(smart_str(slugify(self.name) + 'Form'), (ContactFormFormBase,), attrs)
        return form_class

    def get_submit_label(self):
        return self.submit_label or _('submit')

    class Meta:
        verbose_name = _('contact form')
        verbose_name_plural = _('contact forms')


class FormField(models.Model):
    form = models.ForeignKey(ContactForm, related_name='field_set', on_delete=models.CASCADE)
    label = models.CharField(_('label'), max_length=255)
    field_type = models.CharField(_('field type'), choices=FIELD_TYPES, max_length=100)
    widget = models.CharField(_('widget'), choices=WIDGET_TYPES, max_length=50, blank=True)
    required = models.BooleanField(_('required'), default=False)
    initial = models.CharField(_('initial'), max_length=64, null=True, blank=True)
    choices = models.TextField(_('choices'), null=True, blank=True,
                               help_text=_('enter choices divided by a semicolon (;) for ChoiceFields'))
    css_class = models.CharField(_('CSS class'), null=True, blank=True, max_length=255)
    position = models.IntegerField(_('position'), default=1)

    def __str__(self):
        return '%s, %s field %s' % (self.label, self.field_type, self.widget)

    class Meta:
        ordering = ('position',)

    def get_label(self):
        return self.label


class Recipient(models.Model):
    name = models.CharField(_('name'), max_length=100, blank=True)
    email = models.EmailField(_('email'))

    def __str__(self):
        return '%s, %s' % (self.name, self.email)

    class Meta:
        verbose_name = _('recipient')
        verbose_name_plural = _('recipients')


class ContactFormSubmission(models.Model):
    form = models.ForeignKey(ContactForm, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(_('submit date/time'), auto_now_add=True)
    sender_ip = models.CharField(_('sender IP address'), max_length=40)
    form_url = models.URLField(_('form URL'))
    language = models.CharField(_('language'), default='unknown', max_length=255)
    form_data = models.TextField(_('form data'), null=True, blank=True)
    form_data_pickle = PickledObjectField(_('form data pickle'), null=True, blank=True, editable=False)

    def __str__(self):
        return '%s' % (self.form)

    class Meta:
        ordering = ("-submitted_at",)
        verbose_name = _('contact form submission')
        verbose_name_plural = _('contact form submissions')


class ContactFormSubmissionAttachment(models.Model):
    submission = models.ForeignKey(
        to=ContactFormSubmission,
        related_name="attachments",
        verbose_name=_('submission'),
        on_delete=models.CASCADE
    )
    file = models.FileField(
        verbose_name=_('file'),
        upload_to="private/contactform/submissions/%Y-%m-%d",
        max_length=200,
    )

    class Meta:
        verbose_name = _('contact form submission attachment')
        verbose_name_plural = _('contact form submission attachments')


if 'cms' in settings.INSTALLED_APPS:
    from cms.models import CMSPlugin


    class ContactFormIntermediate(CMSPlugin):
        form = models.ForeignKey(ContactForm, verbose_name=_('form'), on_delete=models.CASCADE)

        def __str__(self):
            return '%s (%s)' % (self.form.name, self.form.language)


    if 'reversion' in settings.INSTALLED_APPS:
        import reversion

        reversion.register(ContactFormIntermediate, follow=["cmsplugin_ptr"])
