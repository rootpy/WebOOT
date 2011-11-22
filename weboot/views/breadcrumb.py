from pyramid.location import lineage

def build_breadcrumbs(context):
    complete_lineage = reversed(list(lineage(context)))
    
    content = []; a = content.append
    
    a('<ul id="menu">')
    for c in complete_lineage:
        a('<li><a href="#">{0}</a><ul><li><a href="">Everything</a></li></ul></li>'.format(c.__name__))
    a('</ul>')
    
    return "".join(content)

    return "".join('<span class="breadcrumb">{0}</span>'.format(l.__name__) 
                    for l in reversed(list(lineage(context))) if l.__name__)
