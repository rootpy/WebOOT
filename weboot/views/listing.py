
from .breadcrumb import build_breadcrumbs


def view_listing(context, request):

    sections = {}
    for item in context.items:
        sections.setdefault(item.section, []).append(item)

    for items in sections.values():
        items.sort(key=lambda o: o.name)

    section_list = []
    for sec in ["root_file", "directory", "hist"]:
        if sec in sections:
            section_list.append((sec, sections.pop(sec)))
    section_list.extend(sections.iteritems())

    return dict(path=build_breadcrumbs(context),
                context=context,
                sections=section_list)
