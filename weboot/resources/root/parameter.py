from weboot.resources.root.object import RootObject

class Parameter(RootObject):
    def __init__(self, request, root_object):
        super(Parameter, self).__init__(request, root_object)
    
    @property
    def content(self):
        return ["<p>{0} : {1}</p>".format(self.obj.GetName(), self.obj.GetVal())]
