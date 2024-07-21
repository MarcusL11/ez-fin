# In a file called [project root]/components/calendar/calendar.py
from django_components import component
import datetime


@component.register("calendar")
class Calendar(component.Component):
    # Templates inside `[your apps]/components` dir and `[project root]/components` dir
    # will be automatically found. To customize which template to use based on context
    # you can override method `get_template_name` instead of specifying `template_name`.
    #
    # `template_name` can be relative to dir where `calendar.py` is, or relative to STATICFILES_DIRS
    template_name = "template.html"

    # This component takes one parameter, a date string to show in the template
    def get_context_data(self, date):
        today = datetime.date.today()
        date = today
        return {
            "date": date,
        }

    # Both `css` and `js` can be relative to dir where `calendar.py` is, or relative to STATICFILES_DIRS
    class Media:
        css = "style.css"
        js = "script.js"
