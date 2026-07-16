from django import template

register = template.Library()

@register.filter
def get_field(form, eleve_pk):
    """Retourne le champ de note pour un élève donné."""
    field_name = f'note_{eleve_pk}'
    return form[field_name] if field_name in form.fields else ''
