from weboot.resources.root.object import RootObject

class Graph(RootObject):
    def __init__(self, request, root_object):
        super(Graph, self).__init__(request, root_object)
    
    @property
    def content(self):
        return ['<p><img class="plot" src="{0}" /></p>'.format(self.sub_url(query={"render":None, "resolution":70}))]
