

class Route:
    # A prefix is in form 
    neighbor = ""  # The router that send this router - will be a.b.c.d
    prefix = ""    # The IP address portion of a prefix - will be a.b.c.d
    prefix_len = 0 # The length portion of a prefix - will be an integer
    path = []      # the AS path - list of integers

    def __init__(self, neigh, p, plen, path):
        self.neighbor = neigh
        self.prefix = p
        self.prefix_len = plen
        self.path = path 

    # convert Route to a String    
    def __str__(self):
        return self.prefix+"/"+str(self.prefix_len)+"- ASPATH: " + str(self.path)+", neigh: "+self.neighbor

    # Get the prefix in the a.b.c.d/x format
    def pfx_str(self):
        return self.prefix+"/"+str(self.prefix_len)


# The following functions:
#  update - the router received a route advertisement (which can be a new one, or an update
#         - the function needs to store the route in the RIB
#  withdraw - the router received a route withdraw message
#          - the function needs to delete the route in the RIB
#  nexthop - given ipaddr in a.b.c.d format as a string (e.g., "10.1.2.3"), perform a longest prefix match in the RIB
#          - Select the best route among multiple routes for that prefix by path length.  
#          - if same length, return either

class Router:
 
    rib = {} 

    # If you use the same data structure for the rib, this will print it
    def printRIB(self):
        for pfx in self.rib.keys():
            for route in self.rib[pfx]:
                print(route) 


    def update(self, rt):

        prefix = rt.pfx_str()
        if prefix not in self.rib:
            self.rib[prefix] = [rt]
        else:
            # Check if the new route has a shorter path length
            for existing_rt in self.rib[prefix]:
                if rt.path < existing_rt.path:
                    self.rib[prefix].remove(existing_rt)
                    self.rib[prefix].append(rt)
                    break

        return



    def withdraw(self, rt):

        prefix = rt.pfx_str()
        if prefix in self.rib:
            self.rib[prefix].remove(rt)
            if not self.rib[prefix]:
                del self.rib[prefix]

        return 
    
    def convertToBinaryString(self, ip):
        vals = ip.split(".")
        a = format(int(vals[0]), 'b').rjust(8, '0')
        b = format(int(vals[1]), 'b').rjust(8, '0')
        c = format(int(vals[2]), 'b').rjust(8, '0')
        d = format(int(vals[3]), 'b').rjust(8, '0')
        return a+b+c+d



    # ipaddr in a.b.c.d format
    # find longest prefix that matches
    # then find shortest path of routes for that prefix
    def next_hop(self, ipaddr):
        retval = None

     
        binary_ip = self.convertToBinaryString(ipaddr)
        best_route = None
        for prefix, routes in self.rib.items():
            prefix_len = int(prefix.split("/")[-1])
            prefix_binary = self.convertToBinaryString(prefix.split("/")[0])
            if binary_ip.startswith(prefix_binary) and (best_route is None or prefix_len > best_route.prefix_len):
                best_route = min(routes, key=lambda r: len(r.path))
        return best_route.neighbor if best_route else None

        return retval




def test_cases():
    rtr = Router()

    #Test that withdrawing a non-existant route works
    rtr.withdraw (Route("1.1.1.1", "10.0.0.0", 24, [3,4,5]))

    #Test updates work - same prefix, two neighbors
    rtr.update (Route("1.1.1.1", "10.0.0.0", 24, [3,4,5]))
    rtr.update (Route("2.2.2.2", "10.0.0.0", 24, [1,2]))

    # print("RIB")
    # rtr.printRIB()

    #Test updates work - overwriting an existing route from a neighbor
    rtr.update (Route("2.2.2.2", "10.0.0.0", 24, [1, 22, 33, 44]))

    # print("RIB")
    # rtr.printRIB()

    #Test updates work - an overlapping prefix (this case, a shorter prefix)
    rtr.update (Route("2.2.2.2", "10.0.0.0", 22, [4,5,7,8]))

    #Test updates work - completely different prefix
    rtr.update (Route("2.2.2.2", "12.0.0.0", 16, [4,5]))
    rtr.update (Route("1.1.1.1", "12.0.0.0", 16, [1, 2, 30]))

    # print("RIB")
    # rtr.printRIB()

    # Should not return an ip
    nh = rtr.next_hop("10.2.0.13")
    assert nh == None

    # Should return an ip
    nh = rtr.next_hop("10.0.0.13")
    assert nh == "1.1.1.1"

    # Test withdraw - withdraw the route from 1.1.1.1 that we just matched
    rtr.withdraw (Route("1.1.1.1", "10.0.0.0", 24, [3,4,5]))

    # Should match something different
    nh = rtr.next_hop("10.0.0.13")
    assert nh == "2.2.2.2"

    # Re-announce - so, 1.1.1.1 would now be best route
    rtr.withdraw (Route("1.1.1.1", "10.0.0.0", 24, [3,4,5]))

    
    rtr.update (Route("2.2.2.2", "10.0.0.0", 22, [4,5,7,8]))
    # Should match 10.0.0.0/22 (next hop 2.2.2.2) but not 10.0.0.0/24 (next hop 1.1.1.1)
    nh = rtr.next_hop("10.0.1.77")
    assert nh == "2.2.2.2"

    # Test a different prefix
    nh = rtr.next_hop("12.0.12.0")
    assert nh == "2.2.2.2"

    rtr.update (Route("1.1.1.1", "20.0.0.0", 16, [4,5,7,8]))
    rtr.update (Route("2.2.2.2", "20.0.0.0", 16, [44,55]))
    nh = rtr.next_hop("20.0.12.0")
    assert nh == "2.2.2.2"

    rtr.update (Route("1.1.1.1", "20.0.12.0", 24, [44,55,66,77,88]))
    nh = rtr.next_hop("20.0.12.0")
    assert nh == "1.1.1.1"


    rtr.withdraw(Route("1.1.1.1", "20.0.12.0", 24, [44,55,66,77,88]))
    nh = rtr.next_hop("20.0.12.0")
    assert nh == "2.2.2.2"








if __name__ == "__main__":
    test_cases()
    

