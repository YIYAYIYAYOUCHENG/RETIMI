from gen_base import *
import StringIO
import sys

class periodic_automaton(base_generator) :
    def __init__(self, name, tname, period = "") :
        base_generator.__init__(self, "Periodic", name)
        self.PER = self.prefix("P")
        self.ini_period = str(period)
        self.x_clock = self.prefix("x")
        self.tname = tname
        
    def gen_clocks(self) :
        return self.x_clock

    def gen_parameters(self) : 
        if self.ini_period == "" or self.ini_period.find("..") != -1 or self.ini_period.find("[") != -1 : 
            return self.PER
        else : return self.PER + " = " + self.ini_period
 
    def gen_parvalues(self) :
        # if self.ini_period.find("[") != -1 : 
        #     self.ini_period = self.ini_period.strip("[").strip("]")
        return self.PER + " = " + stripsq(self.ini_period)

    def gen_init(self) :
        return "    loc[{0}] = {1} & {2} = {3} &\n".format(self.get_automaton_name(), 
                                                           self.loc("arr"), 
                                                           self.x_clock,
                                                           self.PER)
    def gen_init_param(self):
        if self.ini_period == "" or self.ini_period.find("..") != -1 or self.ini_period.find("[") != -1 : 
            per = self.ini_period.strip('[').strip(']')
            lper = per.split("..")
            return "    {1} <= {0} & {0} <= {2} & \n".format(self.PER, lper[0], lper[1])
        else : return ""

    
    def gen_automaton(self) :
        self.out = StringIO.StringIO()
        self.out.write("automaton {0}\n".format(self.get_automaton_name()))
        self.out.write("synclabs : " + self.gsync(self.tname, "arr_event") + ";\n")

        self.out.write(self.wloc("arr", 
                                 inv = self.x_clock + "<=" + self.PER,
                                 stop = "wait"))
        self.out.write(self.wgrd(cond = self.x_clock + "=" + self.PER,
                                 sync = self.gsync(self.tname, "arr_event"),
                                 act = self.x_clock + "'= 0",
                                 target = "arr"))
        
        self.out.write("end\n")

        return self.out.getvalue()

class sporadic_automaton(periodic_automaton) :
    def __init__(self, name, tname, period="") :
        periodic_automaton.__init__(self, name, tname, period)

    def gen_automaton(self) :
        self.out = StringIO.StringIO()
        self.out.write("automaton {0}\n".format(self.get_automaton_name()))
        self.out.write("synclabs : " + self.gsync(self.tname, "arr_event") + ";\n")

        self.out.write(self.wloc("arr", 
                                 inv = self.x_clock + "<=" + self.PER,
                                 stop = "wait"))
        self.out.write(self.wgrd(cond = self.x_clock + ">=" + self.PER,
                                 sync = self.gsync(self.tname, "arr_event"),
                                 act = self.x_clock + "'= 0",
                                 target = "arr"))
        
        self.out.write("end\n")

        return self.out.getvalue()    


                       
class merge_automaton(base_generator) :
    def __init__(self, name, ilist, tname) :
        base_generator.__init__(self, "Merge", name)
        self.urgent = self.prefix('urgent')
        self.ilist = [self.gsync(x, "arr_event") for x in ilist]
        self.tname = self.gsync(tname, "arr_event")

    def gen_clocks(self) :
        return self.urgent

    def gen_init(self) :
        return "    loc[{0}] = {1} & \n".format(self.get_automaton_name(),
                                                        self.loc("idle"))

    def gen_automaton(self) :
        self.out = StringIO.StringIO()
        self.out.write(self.write_header())
        self.out.write("synclabs : " + mklist(self.ilist))
        self.out.write(", " + self.tname + ";\n")

        self.out.write(self.wloc("idle",
                                 inv = "True",
                                 stop = "wait"))
        
        for x in self.ilist :
            self.out.write(self.wgrd(
                cond = "True",
                sync = x,
                act = "", #ass(self.urgent, "0"),
                target = "act"))

        self.out.write(self.wloc("act",
                                 inv = "", #self.urgent + "<=0",
                                 stop = "wait"))
        self.out.write(self.wgrd(cond = "", #self.urgent + "= 0",
                                 sync = self.tname,
                                 act = "",
                                 target = "idle"))

        self.out.write("end\n\n")

        return self.out.getvalue()

class arrival_curve_automaton(base_generator) :
    def __init__(self, name, tname, bmax, period) :
        base_generator.__init__(self, "ArrCurve", name)
        self.bmax = int(bmax)
        self.PER = self.prefix('P')
        self.ini_period = period
        self.clock = self.prefix('x')
        self.tname = self.gsync(tname, "arr_event")

    def gen_clocks(self) :
        return self.clock

    def gen_parameters(self) : 
        if self.ini_period == "" or self.ini_period.find("..") != -1 or self.ini_period.find("[") != -1 : 
            return self.PER
        else : return self.PER + " = " + self.ini_period
 
    def gen_parvalues(self) :
        return self.PER + " = " + stripsq(self.ini_period)

    def gen_init(self) :
        return "    loc[{0}] = {1} & {2} = {3} &\n".format(self.get_automaton_name(), 
                                                           self.loc("start"), 
                                                           self.clock,
                                                           '0')
    def gen_automaton(self) :
        self.out = StringIO.StringIO()
        self.out.write(self.write_header())
        self.out.write("synclabs : {0};\n".format(self.tname))
        
        for i in range(0, self.bmax) :
            if i == 0 :
                loc = 'start'
            else :
                loc = 'start' + str(i)
            self.out.write(self.wloc(loc,
                                     inv = self.clock + '<=0',
                                     stop = 'wait'))
            if i == self.bmax - 1 :
                tg = 'periodic'
            else:
                tg = 'start' + str(i+1)
            self.out.write(self.wgrd(cond = self.clock + '=0',
                                     sync = self.tname,
                                     act = '',
                                     target = tg))

        self.out.write(self.wloc("periodic",
                                 inv = self.clock + '<=' + self.PER,
                                 stop = 'wait'))
        self.out.write(self.wgrd(cond = self.clock + '=' + self.PER,
                                 sync = self.tname,
                                 act = ass(self.clock, '0'),
                                 target = 'periodic'))
        self.out.write('end\n\n')
        return self.out.getvalue()



