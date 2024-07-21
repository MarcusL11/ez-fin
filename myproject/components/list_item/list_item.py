# In a file called [project root]/components/calendar/calendar.py
from django_components import component


@component.register("list_item")
class ListItem(component.Component):
    # Templates inside `[your apps]/components` dir and `[project root]/components` dir
    # will be automatically found. To customize which template to use based on context
    # you can override method `get_template_name` instead of specifying `template_name`.
    #
    # `template_name` can be relative to dir where `calendar.py` is, or relative to STATICFILES_DIRS
    template_name = "list_item.html"

    # This component takes one parameter, a name string to fetch the correct Model
    def get_context_data(self, name):
        from upload_doc.models import name

        categories = name.objects.all()

        return {
            "categories": categories,
        }

    # Both `css` and `js` can be relative to dir where `calendar.py` is, or relative to STATICFILES_DIRS
    class Media:
        css = "style.css"
        js = "script.js"
