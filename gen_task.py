from gen_base import *

class task_automaton(base_generator) :           
    """
    Generates the task automaton for arbitrary deadline tasks

    clocks: c, d, urgent
    discrete: n_inst
    parameters: D
    
    C cannot be a parameter currently, because I cannot express a
    multiplication of the type (C * n_inst) in a guard.  

    To re-introduce C as a parameter, we need to unroll the loop in
    location act and exe, and eliminate n_inst

    (Warning!! Notice that this trick only works for fixed priority
    scheduling, therefore it is not possible to use this same model
    for dynamic schedulers like EDF)
    """
    def __init__(self, taskname, ctime, deadline, max_inst = 3) :
        base_generator.__init__(self, "Task", taskname)
        self.taskname = taskname
        self.CTIME = "{0}".format(ctime)
        self.DTIME = self.prefix("D") 
        self.c_clock = self.prefix("c") 
        self.d_clock = self.prefix("d")
        self.x_clock = self.name + "_arr_x";
        self.urgent = self.prefix("urgent")
        self.n_inst = self.prefix("inst")
        self.ini_deadline = deadline
        self.max_inst = str(max_inst)
    
    def gen_clocks(self) :
        return "{0}".format(self.c_clock)
        #return "{0}, {1}, {2}".format(self.c_clock, self.d_clock, self.urgent)
        #return "{0}, {1}".format(self.c_clock, self.d_clock)

    def gen_discrete(self) :
        return "{0}".format(self.n_inst)

    def gen_parameters(self) :
        if self.ini_deadline == "" or self.ini_deadline.find("..") != -1 or self.ini_deadline.find("[") != -1 : 
            return self.DTIME
        else : return self.DTIME + " = " + self.ini_deadline

    def gen_parvalues(self) :
        # if self.ini_deadline.find("[") != -1: 
        #     dl = self.ini_deadline.strip("[").strip("]")
        # else : dl = self.ini_deadline
        return self.DTIME + " = " + stripsq(self.ini_deadline)

    def gen_init(self) :
        s = "    loc[{0}] = {1} &\n".format(self.get_automaton_name(), self.loc("idle"))
        s = s + "    True &" #{0} = 0 &".format(self.urgent)
        s = s + "    {0} = 0 &\n".format(self.c_clock)
        s = s + "    {0} = 0 &\n".format(self.n_inst)
        s = s + "    {0} >= 0 &\n".format(self.DTIME)
        return s

    def gen_automaton(self) :
        s = "automaton {0}\n".format(self.get_automaton_name())
        s = s + "synclabs : " + mklist([self.sync("arr_event"),
                                        self.sync("arr"),
                                        self.sync("dis"), 
                                        self.sync("pre"),
                                        self.sync("end"),
                                        self.sync("miss")]) + ";\n"
        
        s = s + self.wloc("idle", "True", "wait")
        s = s + self.wgrd("True", 
                          sync = self.sync("arr_event"),
                          #act = ass(self.urgent, "0"),
                          act = "", #ass(self.urgent, "0"),
                          target = "act_event")
        
        s = s + "urgent " + self.wloc("act_event", 
                          #inv = self.urgent + " <= 0",
                          inv = " True",
                          stop = "wait")
        s = s + self.wgrd("True", #expr(self.urgent, "=", "0"), 
                          sync = self.sync("arr"),
                          act = mklist([ass(self.c_clock, "0"), ass(self.n_inst, "1")]),
                          #act = mklist([ass(self.c_clock, "0"), ass(self.d_clock, "0"), ass(self.n_inst, "1")]),
                          target = "act")
        
        s = s + self.wloc("act", 
                          inv = expr(self.x_clock, "<=", self.DTIME), 
                          stop = self.c_clock)
        s = s + self.wgrd(cond = "True",
                          sync = self.sync("dis"),
                          act = "",
                          target = "exe")
        s = s + self.wgrd(cond = expr(self.x_clock, " >= ", self.DTIME),
                          sync = self.sync("miss"),
                          act = "",
                          target = "miss")
        s = s + self.wgrd(cond = self.n_inst + "<" + self.max_inst,
                          sync = self.sync("arr_event"),
                          act = mklist([ass(self.n_inst, self.n_inst+"+1")]),
                          #act = mklist([ass(self.n_inst, self.n_inst+"+1"), ass(self.d_clock,"0")]),
                          target = "act")
        s = s + self.wgrd(cond = self.n_inst + "=" + self.max_inst,
                          sync = self.sync("arr_event"),
                          act = "",
                          target = "miss")
        s = s + self.wgrd(cond = self.n_inst + "<" + self.max_inst,
                          sync = self.sync("arr_event"),
                          act = "",
                          target = "act")
        
        s = s + self.wloc("exe", 
                          inv = mklist([expr(self.x_clock, "<=", self.DTIME), 
                                        expr(self.c_clock, "<=", expr(self.CTIME, "*", self.n_inst))], "&"), 
                          stop = "wait")
        s = s + self.wgrd(cond = self.c_clock + "<" + self.CTIME + "*" + self.n_inst,
                          sync = self.sync("pre"),
                          act = "",
                          target = "act")
        s = s + self.wgrd(cond = mklist([expr(self.x_clock, ">=", self.DTIME),
                                         expr(self.c_clock, "<", expr(self.CTIME, "*", self.n_inst))], "&"),
                          sync=self.sync("miss"), 
                          act="",
                          target="miss")
        s = s + self.wgrd(cond = self.n_inst + "<" + self.max_inst,
                          sync = self.sync("arr_event"),
                          act = mklist([ass(self.n_inst, self.n_inst +"+1")]),
                                        #ass(self.d_clock, "0")]),
                          target="exe")
        s = s + self.wgrd(cond = self.n_inst + "=" + self.max_inst,
                          sync = self.sync("arr_event"),
                          act = "",
                          target="miss")
        s = s + self.wgrd(cond=self.n_inst + "<" + self.max_inst,
                          sync = self.sync("arr_event"),
                          act="",
                          target="exe")
        s = s + self.wgrd(cond=expr(self.c_clock, "=", self.CTIME + "*" + self.n_inst),
                          sync = self.sync("end"),
                          act="",
                          target="idle")
                
        s = s + self.wloc("miss", "True", "wait")

        s = s + "end\n\n"
        return s
            


class task_impldline_automaton(task_automaton) :
    """Generates the task automaton for implicit deadline tasks

    clocks: c, d, urgent
    parameters: C

    This is simpler than the generic one because there can be only one
    instance per task. Therefore, C is now a parameter. However, this
    needs to be connected to an arrival automaton which has a
    parameter P in it, and fixes the deadline equal to P. Also, if an
    activation arrives before the previous instance has completed,
    this is seen as a deadline miss.
    """
    def __init__(self, taskname, ctime, arr_automaton_name) :
        task_automaton.__init__(self, taskname, ctime, 0)
        self.DTIME = arr_automaton_name + "_P"
        self.CTIME = self.prefix("C")
        self.ini_ctime = ctime

    def gen_discrete(self) :
        return ""
    
    def gen_parameters(self) :
        if self.ini_ctime == "" or self.ini_ctime.find("..") != -1 or self.ini_ctime.find("[") != -1 : 
            return self.CTIME
        else : return self.CTIME + " = " + self.ini_ctime

    def gen_parvalues(self) :
        if self.ini_ctime.find("[") != -1: 
            ct = self.ini_ctime.strip("[").strip("]")
        else : ct = self.ini_ctime
        return self.CTIME + " = " + ct


    def gen_init(self) :
        s = "    loc[{0}] = {1} &\n".format(self.get_automaton_name(), self.loc("idle"))
        s = s + "    {0} >= 0 &".format(self.CTIME)
        s = s + "    {0} = 0 &".format(self.urgent)
        s = s + "    {0} = 0 & \n".format(self.c_clock)
        return s

    def gen_automaton(self) :
        s = "automaton {0}\n".format(self.get_automaton_name())
        s = s + "synclabs : " + mklist([self.sync("arr_event"),
                                        self.sync("arr"),
                                        self.sync("dis"), 
                                        self.sync("pre"),
                                        self.sync("end"),
                                        self.sync("miss")]) + ";\n"
        
        s = s + self.wloc("idle", "True", "wait")
        s = s + self.wgrd("True", 
                          sync = self.sync("arr_event"),
                          act = ass(self.urgent, "0"),
                          target = "act_event")
        
        s = s + self.wloc("act_event", 
                          inv = " True", #self.urgent + " <= 0",
                          stop = "wait")
        s = s + self.wgrd("True", #expr(self.urgent, "=", "0"), 
                          sync = self.sync("arr"),
                          act = mklist([ass(self.c_clock, "0")]),
                          #act = mklist([ass(self.c_clock, "0"), ass(self.d_clock, "0")]),
                          target = "act")
        
        s = s + self.wloc("act", 
                          inv = expr(self.x_clock, "<=", self.DTIME), 
                          stop = self.c_clock)
        s = s + self.wgrd(cond = "True",
                          sync = self.sync("dis"),
                          act = "",
                          target = "exe")
        s = s + self.wgrd(cond = expr(self.x_clock, " >= ", self.DTIME),
                          sync = self.sync("miss"),
                          act = "",
                          target = "miss")
        s = s + self.wgrd(cond = "True",
                          sync = self.sync("arr_event"),
                          act = "",
                          target = "miss")
        
        s = s + self.wloc("exe", 
                          inv = mklist([expr(self.x_clock, "<=", self.DTIME), 
                                        expr(self.c_clock, "<=", self.CTIME)], "&"), 
                          stop = "wait")
        s = s + self.wgrd(cond = self.c_clock + "<" + self.CTIME,
                          sync = self.sync("pre"),
                          act = "",
                          target = "act")
        s = s + self.wgrd(cond = mklist([expr(self.x_clock, ">=", self.DTIME),
                                         expr(self.c_clock, "<", self.CTIME)], "&"),
                          sync=self.sync("miss"), 
                          act="",
                          target="miss")
        s = s + self.wgrd(cond = "True",
                          sync = self.sync("arr_event"),
                          act = "", 
                          target="miss")
        s = s + self.wgrd(cond="True",
                          sync = self.sync("arr_event"),
                          act="",
                          target="miss")
        s = s + self.wgrd(cond=expr(self.c_clock, "=", self.CTIME),
                          sync = self.sync("end"),
                          act="",
                          target="idle")
                
        s = s + self.wloc("miss", "True", "wait")

        s = s + "end\n\n"
        return s


class miss_automaton(base_generator) :
    def __init__(self, name, tlist) :
        base_generator.__init__(self, "OBS", name) 
        self.tlist = tlist

    def gen_init(self) :
        return "    loc[{0}] = {1} &\n".format(self.get_automaton_name(),
                                               self.loc("nomiss"))

    def gen_automaton(self) :
        s = "automaton {0}\n".format(self.get_automaton_name())
        s = s + "synclabs : "
        ts = [self.gsync(t, "miss") for t in self.tlist]
        s = s + mklist(ts) + ";\n"

        s = s + self.wloc("nomiss", "True", "wait")
        for t in self.tlist :
            s = s + self.wgrd("True", 
                              sync = self.gsync(t, "miss"),
                              act = "",
                              target = "miss")

        s = s + self.wloc("miss", "True", "wait")

        s = s + "end\n"
        return s
                          
