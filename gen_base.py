def expr(l, s, r) :
    return l + " " + s + " " + r

def ass(l, r) :
    return l + "' = " + r

def mklist(ll, sym = ",") :
    n = len(ll)
    s = ""
    for i, x in enumerate(ll) :
        s = s + x
        if (i < n-1) : s = s + " "     + sym + " " 

    return s  

def stripsq(x) :
    return x.strip('[').strip(']')


class base_generator :
    def __init__(self, typ, name = "") :
        self.name = name
        self.typ = typ
        self.out = None
        
    def get_automaton_name(self) :
        return self.typ + "_" + self.name

    def gen_clocks(self) :
        return ""

    def gen_discrete(self) :
        return ""

    def gen_parameters(self) :
        return ""

    def gen_parvalues(self) :
        return ""

    def gen_automaton(self) :
        return ""

    def gen_init(self) :
        return ""

    ######
    #  Internal functions
    ######

    def write_header(self) :
        return "automaton {0}\n".format(self.get_automaton_name())
    
    def prefix(self, val="") :
        return self.name + "_" + val

    def wloc(self, l, inv, stop) :
        if stop != "wait" : stop = "stop {{ {0} }}".format(stop)
        else : stop = "wait {}"
        return "loc {0} : while {1} {2}\n".format(self.loc(l), inv, stop)

    def wgrd(self, cond, sync, act, target) :
        if sync != "" : sync = "sync " + sync
        if act != "" : act = "do {{ {0} }}".format(act)
        if target != "" : target = "goto " + self.loc(target)
        return "    when {0} {1} {2} {3};\n".format(cond, sync, act, target)

    def loc(self, ln) :
        return self.prefix() + "loc_" + ln
    
    def sync(self, ln) :
        return self.prefix() + ln
    
    def gsync(self, pre, ln) :
        return pre + "_" + ln
    

