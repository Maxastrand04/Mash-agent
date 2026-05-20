from mash.helpers.commands.reference import COMMANDS, formatted as COMMANDS_LIST
from mash.helpers.commands.templates import TEMPLATES, formatted as TEMPLATES_LIST
from mash.helpers.commands.sanitize import (
    normalize_template_verb,
    apply_source,
    apply_destination,
    apply_rename,
    apply_filename,
    strip_recursive_flags,
)
