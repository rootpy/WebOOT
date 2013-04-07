from .. import log
log = log[__name__]
from pyramid.location import lineage
import time


def basic_traverse(what, elements):
    context = what
    while context and elements:
        name, elements = elements[0], elements[1:]
        if name.startswith("!"):
            break
        try:
            context = context[name]
        except AssertionError as e:
            # Hack!
            return
    return context


@log.trace()
def build_breadcrumbs(context):
    # return ""
    backwards_lineage = list(lineage(context))
    complete_lineage = list(reversed(backwards_lineage))

    remaining_fragments = [[]]
    for x in backwards_lineage:
        remaining_fragments.append([x.__name__] + remaining_fragments[-1])
    remaining_fragments = list(reversed(remaining_fragments))

    content = []
    a = content.append

    def build_submenu(c, name, fragments):
        content = []
        a = content.append
        if not hasattr(c, "keys"):
            # Not listable, there are no other matches to try
            return ""

        # good_keys = [k for n, k in (basic_traverse(c[k], n) for k in c.keys) if k]
        good_keys = [k for k in c.keys() if k != name and basic_traverse(c[k], fragments)]
        if not good_keys:
            return ""

        final_url_part = "/".join(fragments)
        fmt = ('<li><a href="{0.url}*/{1}/?{2}">*</a> '
               '<a href="{0.url}*/!compose/stack/{1}/?{2}">Compose</a></li>')
        a(fmt.format(c, final_url_part, context.request.environ.get("QUERY_STRING", "")))
        for x in good_keys:
            # a('<li><a href="{0.url}">{0.__name__}</a> <!--<style
            # type="text/css">color:white;</style>({1})--></li>'.format(c[x],
            # "/".join(n)))
            a('<li><a href="{0.url}{1}/{2}/?{3}">{1}</a></li>'.format(
                c, x, final_url_part, context.request.environ.get("QUERY_STRING", "")))

        return "<ul>{0}</ul>".format("".join(content)) if content else ""

    a('<ul id="menu">')
    for this_context, fragments in zip(complete_lineage, remaining_fragments):
        args = this_context, build_submenu(
            this_context.__parent__, this_context.__name__, fragments[1:])
        a('<li><a href="{0.url}">{0.__name__}</a>{1}</li>'.format(*args))
    a('</ul>')

    return "".join(content)

    return "".join('<span class="breadcrumb">{0}</span>'.format(l.__name__)
                   for l in reversed(list(lineage(context))) if l.__name__)
