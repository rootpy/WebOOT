from pyramid.location import lineage

def build_breadcrumbs(context):
    return "".join('<span class="breadcrumb">{0}</span>'.format(l.__name__) 
                    for l in reversed(list(lineage(context))) if l.__name__)
