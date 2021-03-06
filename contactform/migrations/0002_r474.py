
from south.db import db
from django.db import models
from contactform.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'ContactForm.submit_label'
        db.add_column('contactform_contactform', 'submit_label', models.CharField(_('submit label'), max_length=30))
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'ContactForm.submit_label'
        db.delete_column('contactform_contactform', 'submit_label')
        
    
    
    models = {
        'cms.cmsplugin': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'contactform.recipient': {
            'email': ('models.EmailField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'contactform.contactform': {
            'cc_managers': ('models.BooleanField', ["_('CC to managers')"], {}),
            'cc_site_contact': ('models.BooleanField', ["_('CC to site contact')"], {}),
            'description': ('models.TextField', ["_('description')"], {'blank': 'True'}),
            'has_captcha': ('models.BooleanField', ['_("has a captcha")'], {'default': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', ["_('language')"], {'max_length': '2'}),
            'name': ('models.CharField', ["_('name')"], {'max_length': '100'}),
            'recipients': ('models.ManyToManyField', ["orm['contactform.Recipient']"], {}),
            'submit_label': ('models.CharField', ["_('submit label')"], {'max_length': '30'}),
            'success_message': ('models.TextField', ["_('success message')"], {'blank': 'True'})
        },
        'cms.page': {
            'Meta': {'ordering': "('tree_id','lft')"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'contactform.contactformsubmission': {
            'Meta': {'ordering': '("-submitted_at",)'},
            'form': ('models.ForeignKey', ["orm['contactform.ContactForm']"], {}),
            'form_data': ('models.TextField', [], {'null': 'True', 'blank': 'True'}),
            'form_data_pickle': ('PickledObjectField', [], {'null': 'True', 'editable': 'False', 'blank': 'True'}),
            'form_url': ('models.URLField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'language': ('models.CharField', [], {'default': "'unknown'", 'max_length': '255'}),
            'sender_ip': ('models.IPAddressField', [], {}),
            'submitted_at': ('models.DateTimeField', [], {'auto_now_add': 'True'})
        },
        'contactform.contactformintermediate': {
            'Meta': {'_bases': ['cms.models.CMSPlugin']},
            'cmsplugin_ptr': ('models.OneToOneField', ["orm['cms.CMSPlugin']"], {}),
            'form': ('models.ForeignKey', ["orm['contactform.ContactForm']"], {})
        },
        'contactform.formfield': {
            'Meta': {'ordering': "('position',)", 'unique_together': '(("form","label"),)'},
            'field_type': ('models.CharField', [], {'max_length': '50'}),
            'form': ('models.ForeignKey', ["orm['contactform.ContactForm']"], {'related_name': "'field_set'"}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'label': ('models.CharField', [], {'max_length': '255'}),
            'position': ('models.IntegerField', [], {'default': '1'}),
            'required': ('models.BooleanField', [], {}),
            'widget': ('models.CharField', [], {'blank': 'True', 'max_length': '50'})
        }
    }
    
    complete_apps = ['contactform']
