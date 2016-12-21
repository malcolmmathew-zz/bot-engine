"""
	Helper functions to be used in Engine class.
"""

def format_string(string_template, **kwargs):
    """
        Helper method to perform custom string templating. Allows the inclusion
        of dictionaries in strings.

        Parameters
        ----------
        string_template : {str}
            main string to be reformatted using the new templating structure.

        kwargs : {dict}
            keyword arguments corresponding to template placeholders
    """
    template_char = '~'

    # identify all occurences of templates
    idx = 0

    templates = []

    while idx < len(string_template):
        start_idx = string_template[idx:].find(template_char)
        
        if start_idx == -1:
            # we've found all occurences of the templates
            break

        start_idx += idx

        end_idx = \
            string_template[start_idx+1:].find(template_char) + start_idx + 1 
        templates.append(string_template[start_idx:end_idx+1])
        idx = end_idx+1

    for tpl in templates:
        string_template = string_template.replace(tpl, str(kwargs[tpl[1:-1]]))

    return string_template
    