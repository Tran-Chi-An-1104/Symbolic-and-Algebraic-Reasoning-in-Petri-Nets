import xml.etree.ElementTree as ET
import queue

# PNML namespace
PNML_NS = "{http://www.pnml.org/version-2009/grammar/pnml}"

#==============================================FUNCTION TO PARSE PNML FILE====================================#
def parse_pnml(filename):
    tree = ET.parse(filename)
    root = tree.getroot()               #root is <pnml>

    # Internal data structures
    places = {}          # place_id -> initial tokens
    transitions = set()  # set of transition ids
    arcs = []            # list of (source, target)

    # Parse PLACES
    for p in root.findall(".//" + PNML_NS + "place"):
        pid = p.attrib["id"]

        # Reading token
        marking_node = p.find(".//" + PNML_NS + "initialMarking/" + PNML_NS + "text")      
        marking = int(marking_node.text) if marking_node is not None else 0
        places[pid] = marking

    # Parse TRANSITIONS
    for t in root.findall(".//" + PNML_NS + "transition"):
        tid = t.attrib["id"]
        transitions.add(tid)

    # Parse ARCS
    for a in root.findall(".//" + PNML_NS + "arc"):
        src = a.attrib["source"]
        tgt = a.attrib["target"]
        arcs.append((src, tgt))
    

    return places, transitions, arcs
#=========================================END OF PNML PARSE====================================#








#========================================BREADTH FIRST SEARCH=================================

#Convert arc into pre and post input/output form
def Transition_Input_Output(places, transitions, arcs):
    #pre = { "T1": [], "T2": [], "T3": [], ... }    -    Get input of arcs
    pre = {}
    for transition_id in transitions:
        pre[transition_id] = []

    #post = { "T1": [], "T2": [], "T3": [], ... }   -    Get output of arcs
    post = {}
    for transition_id in transitions:
        post[transition_id] = []


    for arc in arcs:
        source = arc[0]
        target = arc[1]

        #If arc is: place -> transition
        if (source in places) and (target in transitions):
            pre[target].append(source)
        #If arc is: transition -> place
        elif (source in transitions) and (target in places):
            post[source].append(target)


    return pre, post


#Check if all input of transition contain 1 token
def is_enabled_to_fire (transition, marking, pre):
    for place in pre[transition]:
        if marking[place] == 0:                     #Token = 0
            return False
        
    return True


#Fire from a transition, produce new marking token
def fire_transition (transition, marking, pre, post):
    new_marking = marking.copy()

    #remove token from old Place
    for p in pre[transition]:
        new_marking[p] = 0

    #add token to new Place
    for p in post[transition]:
        new_marking[p] = 1

    return new_marking



#BFS To find all reachable marking
def bfs_reachable_markings(places, transitions, arcs):

    pre, post = Transition_Input_Output(places, transitions, arcs)

    #Ordered list of place 
    place_id_list = []
    for place_id in places:
        place_id_list.append(place_id)

    place_id_list.sort()     


    #Intial marking token
    initial_marking_list = []
    for place_id in place_id_list:
        initial_marking_list.append(places[place_id])
    
    initial_marking_tuple = tuple(initial_marking_list)      #Inital token is: (P1: 0, P2: 0, P3: 0, P4: 0, P5: 1, P6: 0)



    #Initialize visited and queue
    visited = set()
    visited.add(initial_marking_tuple)

    reachable = []
    reachable.append(initial_marking_tuple)

    bfs_queue = queue.Queue()
    bfs_queue.put(initial_marking_tuple)

    #BFS
    while not bfs_queue.empty():
        current_marking_tuple = bfs_queue.get() 

        current_marking_dict = {}
        index_value = 0

        for place_id in place_id_list:
            current_marking_dict[place_id] = current_marking_tuple[index_value]
            index_value += 1


        #Check all transition
        for transition in transitions:
            #Check if transition is enabled to fire token
            transition_enabled = is_enabled_to_fire(transition, current_marking_dict, pre)
            
            if transition_enabled is False:
                continue

            #Fire transition to get new marking token
            new_marking_dict = fire_transition(transition, current_marking_dict, pre, post)


            new_marking_list = []
            for place_id in place_id_list:
                new_marking_list.append(new_marking_dict[place_id])
            
            new_marking_tuple = tuple(new_marking_list)

            if new_marking_tuple not in visited:
                visited.add(new_marking_tuple)
                reachable.append(new_marking_tuple)
                bfs_queue.put(new_marking_tuple)

    return reachable, place_id_list


#============================END OF BREADTH FIRST SEARCH=============================#
        


places, transitions, arcs = parse_pnml("PetriNetSample.pnml")

print("\nPLACES:")
for p, m in places.items():
    print(f"  {p}: {m} token")

print("\nTRANSITIONS:")
for t in transitions:
    print("  ", t)

print("\nARCS:")
for s, t in arcs:
    print(f"  {s} -> {t}")



# Places: Dict -> {(place_id: token), ...}
# Transistion: Set -> (T1, T2, ...)
# Arc: List -> [(source, target), ...]

print("\n==================Check reachable===================")

reachable, order = bfs_reachable_markings(places, transitions, arcs)


reachable_places = set()
for marking_tuple in reachable:

    index_value = 0
    for place_id in order:

        token_value = marking_tuple[index_value]

        # If this place has a token in this marking, mark it as reachable
        if token_value == 1:
            reachable_places.add(place_id)

        index_value = index_value + 1


# Print reachable places
print("\nReachable Places:")
for place_id in sorted(reachable_places):
    print(" ", place_id)