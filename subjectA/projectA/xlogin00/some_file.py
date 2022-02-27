""" first line """
class Request:
    def __init__(self, time, src, dst, weight, content):
        self.req_time = time
        self.src = src
        self.dst = dst
        self.weight = weight
        self.content = content
        self.slot = -1
        self.to_unload = False # vozik je v cielovej stanici, teda treba vylozit naklad
        self.loaded = False
        self.unloaded = False
	def foo(self):
        pass

    def __str__(self):
        return '%s: %s -> %s (%d) %s %s' % (self.content, self.src, self.dst, self.weight, 
        "loaded on %s" %(self.slot) if self.slot >= 0 else "", "- to unload " if self.to_unload else "")

    def loading(self,slot_id):
        self.slot = slot_id
        self.loaded = True
 
# d
# asdasdasdasdasdeasd
# f
    def unloading(self):
        self.slot = -1
        self.to_unload = False
        self.unloaded = True  ef on_destination(self):
        self.to_unload = True

# ziadosti o presun
requests = []

# obsadenost slotov (1=obsadeny, 0=volny)
slots = [0,0,0,0]

# pokrytie
to_cover = [('A',0),('A',1),('A',2),('A',3),
            ('B',0),('B',1),('B',2),('B',3),
            ('C',0),('C',1),('C',2),('C',3),
            ('D',0),('D',1),('D',2),('D',3)]
