from weboot.resources.root.object import RootObject

class Tree(RootObject):
    def __init__(self, request, root_object):
        super(Tree, self).__init__(request, root_object)
    
    @property
    def content(self):
        content = ('<a href="!tohist/{0}/">{0}</a><br />'.format(l.GetName())
                   for l in self.obj.GetListOfLeaves())
        return ["<p><pre>{0}</pre></p>".format("\n".join(content))]
