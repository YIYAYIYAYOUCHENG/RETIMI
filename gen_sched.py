import copy
from gen_base import *
import StringIO
import sys

#  TBD: it is possible to extend this in several directions: 
#
#  1) Non preemptive scheduling: this is easy, it only suffices to
#  change the transitions
#
#  2) Adding an external signal for suspending/activating the
#  scheduler (for hierarchical scheduling)
#
#  3) Adding a parameter for context switch duration (for robustness
#  due to change of context)

class sched_automaton(base_generator) : 
    """Generates the scheduler automaton.  It takes as input the output
    stream, and a list of indexes.

    Task are in decreasing order of priority, task indexes[0] has the
    highest priority.
    
    There is only one clock for urgent locations, it is used to implement the 
    context switch.

    If parameter stop_idle = True, then the scheduler will stop at the
    first idle-time and will not accept any other arrival. 
    """
    def __init__(self, nm, indexes, stop_idle = False) :
        base_generator.__init__(self, "Sched", name = nm)
        self.ntasks = len(indexes)
        self.ids = indexes
        if self.ids == None :
            self.ids = map(lambda x : "t" + str(x), range(1, ntasks+1))

        self.loc_name = self.name + "_loc_"
        self.clock = self.prefix("urgent")
        self.stop_idle = stop_idle

    def gen_clocks(self) :
        return "" #self.clock

    def gen_discrete(self) :
        return ""

    def gen_init(self) :
        s = "    loc[sched_{0}] = {1} &\n".format(self.name, self.loc_name)
        s = s #+ "    {0} = 0 &\n".format(self.clock)
        return s

    def gen_automaton(self) :
        self.out = StringIO.StringIO()
        self.out.write("automaton sched_{0}\n".format(self.name))
        self.out.write("synclabs : ")
        for i in range(0, self.ntasks) :
            if i > 0 : self.out.write(", ")
            self.out.write(self.gsync(self.ids[i], "arr") + ", ")
            self.out.write(self.gsync(self.ids[i], "dis") + ", ")
            self.out.write(self.gsync(self.ids[i], "pre") + ", ")
            self.out.write(self.gsync(self.ids[i], "end"))
        self.out.write(";\n")
        
        state_list = self.generate_state_list(self.ntasks); 

        for state in state_list :
            self.out.write(
                self.wloc(self.build_state(state), "True", "wait"))
            arr_states = self.generate_arrival_edges(state)
            
            # the end label
            ending = self.find_first(state)
            if ending != 0 :
                endstate = self.loc_name + self.build_ending_state(state);
                self.out.write("    when True sync {0} do {{  }} goto {1};\n".format(self.gsync(self.ids[ending-1], "end"), endstate, self.clock))

            # the end location
            if ending != 0:
                self.generate_ending_location(state, endstate)

            self.generate_arrival_locations(arr_states)
        self.out.write("loc {0} : while True wait {{}}\n".format(self.loc("stop")))
        self.out.write("end\n\n")

        return self.out.getvalue()


    #
    # HELPER FUNCTIONS (NOT TO BE CALLED DIRECTLY)
    #


    def generate_state_list(self, ntasks) :
        """
        Generates all possible combination of ntasks. Each task can be
        "active" (1) or idle (0).  This function generates a list of
        2^ntasks lists of 0 or 1 (one for each task)
        """
        if ntasks == 1 : 
            return [ [0], [1] ] 
        else :
            l = self.generate_state_list(ntasks - 1)
            l2 = []
            for x in l :
                y = copy.copy(x)
                x.append(0)
                y.append(1)
                l2.append(x)
                l2.append(y)
            return l2

    def build_state(self,l) :
        """
        returns the name of the state which is R + taskId if running, or W
        + taskId if waiting
        """
        state = ""
        flag = True
        for i, e in enumerate(l) :
            if e == 1 :
                if flag == True :
                    state = state + "R" + str(self.ids[i]) 
                    flag = False
                else :
                    state = state + "W" + str(self.ids[i])
        return state

    def new_arrivals_list(self,l) :
        """ 
        Given a list of (0 or 1), returns the list of indexes of non active tasks
        (the one with zero).
        """
        sl = []
        for i, e in enumerate(l): 
            if e == 0 :
                sl.append(i)

        return sl

    def set_arrival(self, l, i) :
        """
        Set the i-th bit to 1
        """
        l2 = copy.copy(l)
        l2[i] = 1
        return l2

    def build_arrival_state(self, l, k) :
        """
        returns the name of the state which is R + taskId if running, or W
        + taskId if waiting, and for the k-th task, it is A + taskId.
        """
        state = ""
        flag = True
        for i, e in enumerate(l) :
            if i == k : state = state + "A" + str(self.ids[k])
            elif e == 1 :
                if flag == True :
                    state = state + "R" + str(self.ids[i]) 
                    flag = False
                else :
                    state = state + "W" + str(self.ids[i])
        return state

    def build_ending_state(self, l) :
        """ 
        returns a string which contains a E + taskId for the first active task
        and a W + taskId for every other active task
        """
        state = ""
        flag = True
        for i, e in enumerate(l) :
            if e == 1 :
                if flag == True :
                    state = state + "E" + str(self.ids[i]) 
                    flag = False
                else :
                    state = state + "W" + str(self.ids[i])
        return state

    def find_first(self, l) :
        """
        Returns the index of the first active task
        """
        for i, e in enumerate(l) :
            if e == 1 :
                return i+1
        return 0

    def check_preemption(self, state, a) :
        if self.find_first(state) > a+1 :
            return True
        else :
            return False


    def generate_arrival_edges(self, state) :
        arr_list = self.new_arrivals_list(state)
        arr_states = []
        # the arrival label
        for a in arr_list :
            if self.find_first(state) == 0 or self.check_preemption(state, a) :
                newstate = self.loc_name + self.build_arrival_state(state, a)
                arr_states.append((a,copy.copy(state)))
            else :
                newstate = self.loc_name + self.build_state(self.set_arrival(state, a))
            self.out.write("    when True sync {0} do {{}} goto {1};\n".format(self.gsync(self.ids[a], "arr"), newstate, self.clock))
        return arr_states

    def generate_ending_location(self, state, endstate) :
        self.out.write("urgent loc {0} : while True wait\n".format(endstate, self.clock))
        s = self.remove_first(state)
        x = self.find_first(s)
        if (x != 0) :
            slab = "sync {0}".format(self.gsync(self.ids[x-1],"dis"))
            newstate = self.loc_name + self.build_state(s)
            action = ""
        else :
            slab = ""
            if self.stop_idle : 
                newstate = self.loc("stop")
                action = ""
            else :
                newstate = self.loc_name
                action = ""
        self.out.write("    when True {0} {3} goto {1};\n".format(slab, newstate, self.clock, 
                                                                     action)) 

    def build_preempt_state(self, l) :
        """
        returns the name of the state which is W + taskId for all tasks, and A + taskId 
        for all remaining tasks
        """
        state = ""
        flag = True
        for i, e in enumerate(l) :
            if e == 1 :
                if flag == True : 
                    state = state + "A" + str(self.ids[i])
                    flag = False
                else : 
                    state = state + "W" + str(self.ids[i])
        return state

    def generate_arrival_locations(self, arr_states) :
        for a, s in arr_states : 
            f = self.find_first(s)
            ars = self.loc_name + self.build_arrival_state(s, a)
            s2 = self.loc_name + self.build_state(self.set_arrival(s,a))
            if f != 0 :
                ars = self.loc_name + self.build_arrival_state(s, a)
                s1 = self.loc_name + self.build_preempt_state(self.set_arrival(s,a))
                self.out.write("urgent loc {0} : while True wait\n".format(ars,self.clock))
                self.out.write("    when True sync {0} goto {1};\n".format(self.gsync(self.ids[f-1], "pre"),s1,self.clock))
                self.out.write("urgent loc {0} : while True wait\n".format(s1,self.clock))
                self.out.write("    when True sync {0} goto {1};\n".format(self.gsync(self.ids[a],"dis"),s2,self.clock))
            else :
                self.out.write("urgent loc {0} : while True wait\n".format(ars,self.clock))
                self.out.write("    when True sync {0} goto {1};\n".format(self.gsync(self.ids[a],"dis"),s2,self.clock))

        self.out.write("\n")

    def remove_first(self, l) :
        """ 
        Removes the first 1
        """
        l2 = copy.copy(l)
        for i, e in enumerate(l2) :
            if e == 1 :
                l2[i] = 0
                return l2
        return l2




def main(args) :
    if len(args) < 3 :
        print "Usage: gen_sched.py name <list of task indexes>"
        sys.exit(-1)
    task_list = args[2:]

    s = sched_automaton(args[1], task_list)

    # print "(** DECLARATIONS **)"
    # print s.gen_base()

    print "(** CLOCKS **)"
    print s.gen_clocks()

    print "(** DISCRETE **)"
    print s.gen_discrete()

    print "(** AUTOMATON **)"
    print s.gen_automaton()

    print "(** INITIALIZATION **)"
    print s.gen_init()
    

if __name__ == "__main__" :
    main(sys.argv)
