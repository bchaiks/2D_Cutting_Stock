import json
import numpy as np
def stock_cutting(request):
    data = request.get_json()
    pieces = data['dimensions']
    '''
    ** Nearly Pure Python ** Implementation of the 
    Extreme-point BFD-Heuristic for 2D-Cutting Stock Problem:
    Based on "Extreme Point-Based Heuristics for 
    Three-Dimensional Bin Packing" INFORMS Journal 
    on Computing (2008)  Teodor Gabriel Crainic, Guido Perboli, 
    Roberto Tadei,
    Maybe translate it into Julia as an exercise and so that it's faster...
    '''

    ##################################################################
    #######   Preliminary Functions
    ##################################################################


    ## NEED TO IMPLEMENT THIS!!! AND TRY RANDOMIZING THE 
    ## ORDER AND KEEPING TRACK OF THE "USABLE WASTE"...
    def order(x,vals):
        '''
        idea is to apply this to the pieces, with different
        vectors for vals depending on the ordering rule 
        (probably start with non-increasing volume)
        '''
        x = [i for _,i in sorted(zip(vals,x), reverse = True)]
        return x


    def Feas(Dims, EP, Bin_Size, Curr_items, Curr_EP):
        '''
        Returns True if a piece of dimension 
        Dims = WxD is feasible in a bin with leftmost corner at EP 
        
        Bin_Size = 1x2 dimensions of bin
        Dims = 1x2
        EP = 1x2 -- coordinates of the chosen spot
        For all items in Curr_items placed at Curr_Ep
        have to make sure that EP[0] + d[OR[0]] doesn't 
        poke through... item[j][0] -- item[j][0] + Curr_Ep[j][0]	
        '''
        BS = Bin_Size
        D = Dims
        CI = Curr_items
        CE = Curr_EP
        check = True	
        for i in range(2):
            # Bin limits
            if D[i] + EP[i] > BS[i]:
                check = False
                
        for j in range(len(CI)):
            # checking intersections with other items
            
            ####################################################
            #### DOUBLE CHECK THIS FOR CORRECTNESS!!!!
            ####################################################
            for k in range(2):
                a = (k + 1)%2
                
                if overlap(D,EP,CI[j],CE[j],k,a,): 
                    check = False
        return check
        
    def overlap(d1,c1, d2,c2, k,x):
        '''
        returns True if two 3-d boxes with dimensions d1 d2
        and lower left corners c1, c2 overlap on the x dim...
        '''	
        ov = True
        if c1[x] >= c2[x] + d2[x]:
            ov = False
        if c2[x] >= c1[x] + d1[x]:
            ov = False
            
        if c1[k] >= c2[k] + d2[k]:
            ov = False
        if c2[k] >= c1[k] + d1[k]:
            ov = False
        return ov
    '''
    Compute Merit function for given placement of a piece 
    '''
    def Merit_Res(Dims, EP, Rs, Bin_Size):
        '''
        not gonna bother checking feasibility...
        assume that this calc comes AFTER feasibility check...
            
        --Maybe weight the dimensions differently to 
        make the different orientations different?
        '''
        D = Dims 
        BS = Bin_Size
        '''
        this does NOT take account of the orientation
        so the orientation is basically just for feasibility...
        '''
        # The "extra" EP[0] + Dims[0] is supposed to penalize "high" positions...
        return sum(Rs) - sum(Dims) + EP[0] + Dims[0]


    def Merit_WD(Dims, EP, curr_items, curr_eps):
        '''
        Selects position that minimizes the bounding 
        box in the WxD dimension
        
        curr_items = items in crate
        curr_eps = position of items 
        EP = candidate position 
        OR = candidate orientation
        '''
        D = Dims
        CI = curr_items
        CE = curr_eps
        ''' 
        start out with the box bounds as the new guy
        '''
        X = EP[0] + D[0]
        Y =  EP[1] + D[1]
        for i in range(len(CI)):
            if CE[i][0] + CI[i][0] > X:
                X = CE[i][0] + CI[i][0]
            if CE[i][1] + CI[i][1] > Y:
                Y = CE[i][1] + CI[i][1]
        val = X*Y  + X
        return(val)
        
    #### Work with people to determine best/better merit functions.

    #### CODE UP THE BOUNDING BOX ONES TOO!! THESE SEEM LIKELY 
    #### CANDIDATES FOR US...

    '''
    Update Extreme point list
    '''
    def proj(d1,e1,d2,e2, proj_dir):
        '''
        d1, e1 -- dim of new piece, placed at point e1
        d2, e2 -- cycle these through the other pieces
        
        ep_dir is the coordinate "pushed out" by the piece dimension in 
        the candidate extreme point
        proj_dir is the one to shrink... (number 0,1,2 corresponding to x, y, z)
        These are NEVER the same...
        '''

        pd = proj_dir
        # remaining dimension???	
        od = 1-pd
        check = True

        if d2[pd] + e2[pd] > e1[pd] :
            #i.e. piece is further from axis in projection direction 
            check = False

        if  e2[od] > e1[od]:
            #i.e. piece too far
            check = False
        if e2[od] + d2[od] < e1[od] :
            # i.e. piece not far enough
            check = False
        return check

    def Update_EP(Dims, EP, Curr_EPs, Curr_Items):
        '''
        Dims = 1x2 WxD of current piece placed 
            (in orienation OR* decided by Feas and Merit...)
        EP = 1x2 coordinates of lower left corner of current piece
        Curr_EPs = list of current extreme points where Curr_Items
            are located 
        Curr_Items = list of dimensions of current items 
        
        idea is you take current EP and push it out in the 
        three dimensions of the current piece, then project
        each of these towards the two other axes...
        
        e.g. [ep[0],ep[1] + Dims[1], ep[2]] projected in 
        x and z directions... 
        
        - Six possible new ones (possibly duplicated...)
        - each of the three 
        New_Eps[0], [1] are x_y and x_z projections of (ep[0]+dim[0],ep[1],ep[2])
        by shrinking the y and z coordinates, respectively... 
        '''
        D = Dims
        CI = Curr_Items
        CE = Curr_EPs
        New_Eps = [[EP[0]+D[0],EP[1]],
                    [EP[0],EP[1]+D[1]]]
        
        Max_bounds = -1*np.ones(2)
        
        for i in range(len(CI)):
            # shrinking y coordinate
            if proj(D, EP, CI[i], CE[i],1) and CE[i][1] + CI[i][1] > Max_bounds[1]:
                New_Eps[0] = [EP[0] + D[0], CE[i][1] + CI[i][1]]
                Max_bounds[0] = CE[i][1] + CI[i][1]
                
        
            # shrinking x coordinate
            if proj(D, EP, CI[i], CE[i],0) and CE[i][0] + CI[i][0] > Max_bounds[0]:
                New_Eps[1] = [CE[i][0] + CI[i][0], EP[1] + D[1]]
                Max_bounds[1] = CE[i][0] + CI[i][0]	
                
        # remove duplicates
        New_Eps = np.unique(New_Eps, axis = 0)
        return New_Eps

    def Init_RS(NE, Bin_Dims):
        '''
        Input is a list of new EPs
        Initializes the residual space in each axis
        This may be updated by the Update_RS function'''
        BD = Bin_Dims
        RS = []
        for i in range(len(NE)):
            RS_i = [BD[0] - NE[i][0], BD[1] - NE[i][1]]
            RS.append(RS_i)
        
        return RS

    def Update_RS(Dims, EP, All_EPs, RS_list):
        '''
        This updates the EXISTING RS's to account for 
        the new item in the Bin. 
        
        DOES NOT update the initialized RS to account for 
        the other items already in the bin -- would have to 
        include the current items to do that...
        
        Dims = **re-ordered** dimensions of the newly added piece
        EP = extreme point PLACEMENT location of the new piece
            -- this guy is no longer in the list...
            -- the initial res of the 
        All_Eps = list of all other extreme points
        RS_list = current residuals list (each entry a 3-tuple)  
        '''
        EPL = All_EPs
        D = Dims
        RL = RS_list
        for i in range(len(EPL)):
            if EPL[i][0] >= EP[0] and EPL[i][0] < EP[0] + D[0]:
                if EPL[i][1] <= EP[1]:
                    RL[i][1] = min([RL[i][1], EP[1] - EPL[i][1]])
                    
            if EPL[i][1] >= EP[1] and EPL[i][1] < EP[1] + D[1]:
                if EPL[i][0] <= EP[0]:
                    RL[i][0] = min([RL[i][0], EP[0] - EPL[i][0]]) 
        
        return RL	 

    #############
    #### Trying to maximize "useable waste"
    #############
    """
    def U_W(Dims, EP, Curr_items, Curr_EPs):
        '''
        for each sheet, compute the useable waste
        ABOVE some threshold return the useable
        
        COULD use this as an alternative way to 
        force creation of a new bin (i.e. an additional)
        feasibility check
        
        maximum contiguous rectangle (at top or far right 
        of the sheet)
        '''
        
        
        useable_waste = ...
        return(useable_waste)
        
    def randomize(parts):
        '''
        randomize the order of the parts and 
        try the packing...
        '''
        
        rand_part
        return(rand_part)
    """
    ##################################################################
    #######   INPUT STAGE
    ##################################################################

    Sheet_dim = [96.0,48.0]


    ## part label, width, depth
    PARTS = pieces
            
    labels = list(PARTS.keys())
    parts = []
    for i in range(len(labels)):
        parts.append([labels[i], PARTS[labels[i]], i])
        
    areas = [PARTS[labels[i]][0]* PARTS[labels[i]][1] for i in range(len(labels))]
    ptp = [parts[i] for i in range(len(labels))]
    ptp = order(ptp,areas)

            
    parts 

    ##################################################################
    #######  Packing Stage
    ##################################################################


    #### Instantiate first Sheet with first EP at [0,0,0]...

    # List of open EP's in open Crates
    SH = [[[0,0,0]]]
    ## when create a new crate, give it one of the size bounds 
    ## from Crate_Dims and initialize the Crate_RS_Lists with these

    ## Stores Residuals for each EP in each Crate (ORDERING HAS TO BE THE SAME)
    Cr_RS = [[Sheet_dim]]

    # Stores a list of the dimensions of items currently in each crate
    Cr_Item=[[]]  

    # Stores a list of the EPs where the current items 
    # were placed -- need this to compute intersections
    Cr_EPs =[[]] 



    ## List of the locations and orientations of packed pieces
    Packings = []
    Bin_size = Sheet_dim

    for p in range(len(ptp)):
        '''
        try the piece in EACH existing crate, pick best spot 
        according to the merit function.
        If NO possible packing THEN Crates.append([[0,0,0]]) and 
        pack it in this one...
        
        For bounding box merit function, maybe also start a new 
        crate if the BEST Merit value is too bad...
        '''
        # update this with the crate it's packed in... 
        packed_in = None
        Dims = ptp[p][1]
        
        Best_Merit = 2 * Sheet_dim[0] * Sheet_dim[1]
        e_cand = None
        
        for c in range(len(SH)):

            EPL = SH[c]
            Curr_Items = Cr_Item[c]
            Curr_EP = Cr_EPs[c]
            RS_List = Cr_RS[c]
            Ordered_RS = []
            Ordered_EPL = []
            
            for e in range(len(EPL)):

                    #if Feas(Dims, EPL[e], Bin_size, Curr_Items, Curr_EP) and Merit_Res(Dims, EPL[e], RS_List[e], Bin_size) < Best_Merit:
                    if Feas(Dims, EPL[e], Bin_size, Curr_Items, Curr_EP) and Merit_WD(Dims, EPL[e], Curr_Items, Curr_EP) < Best_Merit:
                        #Best_Merit = Merit_Res(Dims, EPL[e], RS_List[e], Bin_size)
                        Best_Merit = Merit_WD(Dims, EPL[e], Curr_Items, Curr_EP)
                        e_cand = e
                        packed_in = c
                        
        if packed_in is not None:
            
            k = packed_in
            EPL = SH[k]
            Curr_Items = Cr_Item[k]
            #Curr_EP = Cr_EPs[k]
            RS_List = Cr_RS[k]
            
            
            NE = Update_EP(Dims, EPL[e_cand], Curr_EP, Curr_Items)
            
            
            Cr_Item[k].append(Dims)
            Cr_EPs[k].append(EPL[e_cand])
            L = len(Cr_EPs[k])
            del RS_List[e_cand]
            del EPL[e_cand]

            for i in range(len(NE)): 
                EPL.append(NE[i])
            
            N_RS = Init_RS(NE, Bin_size)
            
            for i in range(len(N_RS)):
                RS_List.append(N_RS[i])
                
            RS_List = Update_RS(Dims, Cr_EPs[k][L-1], EPL, RS_List)
            
            # Sort the EPs by lowest z, y, x respectively...
            # might want to change this, depending on how things go...
            
            for i in range(2):
                # the [2-i] means it sorts the 0 index last -- i.e. really ordered 
                # by smallest height... wherever height is in the list... 
                order_i = [np.argsort(EPL,0)[r][1-i] for r in range(len(EPL))]
                
                #### Seems to be ok to do this in place like this...
                RS_List = [RS_List[order_i[j]] for j in range(len(order_i))]
                EPL = [EPL[order_i[j]] for j in range(len(order_i))]
                
                
            #print('EPL:',EPL)
            #print('RSList:', RS_List)			
            
            '''
            WILL NEED TO CHANGE THIS so that it returns the format that Kyle wants
            need to make a dictionary mapping the orientation chosen in the loop 
            to the relevant orientation in the "XY 90 degree" language... 
            ''' 
            
            #Result = [ptp[p][2], {'part': ptp[p][0], 'sheet': packed_in,
            #'x': Cr_EPs[k][L-1][0] , 'y': Cr_EPs[k][L-1][1] + (5+Bin_size[1])*packed_in}]
            Result = [ptp[p][2], {'part': ptp[p][0], 'x': Cr_EPs[k][L-1][0] , 'y': Cr_EPs[k][L-1][1] + (5+Bin_size[1])*packed_in}]
            
            
            #orientation HxWxD = {Dims}, bottom left at {Cr_EPs[k][L-1]} in Crate {packed_in}.
            Packings.append(Result)
            
            SH[k] = EPL 
            #Cr_Item[k] = Curr_Items  
            #Cr_EPs[k] = Curr_EP  
            Cr_RS[k] = RS_List  	
                
        if packed_in is None:
            SH.append([[0,0,0]])
            Cr_RS.append([Bin_size])
            Cr_Item.append([])  
            Cr_EPs.append([]) 
            
            c = len(SH)-1
            packed_in = c
            EPL = SH[c]
            Curr_Items = Cr_Item[c]
            Curr_EP = Cr_EPs[c]
            RS_List = Cr_RS[c]
            e_cand = 0
                    
            NE = Update_EP(Dims, EPL[e_cand], Curr_EP, Curr_Items)
            
            
            Curr_Items.append(Dims)
            Curr_EP.append(EPL[e_cand])
            L = len(Curr_EP)
            del RS_List[e_cand]
            del EPL[e_cand]
            
            for i in range(len(NE)): 
                EPL.append(NE[i])
                
                # Sort the EPs by lowest height, width, and depth respectively...
                # might want to change this, depending on how things go...	
                                                    
            N_RS = Init_RS(NE, Bin_size)
            for i in range(len(N_RS)):
                RS_List.append(N_RS[i])
                
            RS_List = Update_RS(Dims, Curr_EP[L-1], EPL, RS_List)
            
            for i in range(2):
                order_i = [np.argsort(EPL,0)[r][1-i] for r in range(len(EPL))]
                RS_List = [RS_List[order_i[j]] for j in range(len(order_i))]
                EPL = [EPL[order_i[j]] for j in range(len(order_i))]
                

            #Result = [ptp[p][2],{'part': ptp[p][0], 'sheet': packed_in,
            #'x': Cr_EPs[c][L-1][0] , 'y': Cr_EPs[c][L-1][1] + (5+ Bin_size[1])*packed_in}]
            Result = [ptp[p][2],{'part': ptp[p][0], 'x': Cr_EPs[c][L-1][0] , 'y': Cr_EPs[c][L-1][1] + (5+ Bin_size[1])*packed_in}]
            Packings.append(Result)
            SH[c] = EPL
            Cr_Item[c] = Curr_Items 
            Cr_EPs[c] = Curr_EP 
            Cr_RS[c] = RS_List

    ################################################################################
    ######## OUTPUT
    ################################################################################

    Sheet_coord = []
    for i in range(len(SH)):
        y = (5+ Bin_size[1])*i
        x = 0
        entry = {'sheet': i, 'x': x, 'y':y}
        Sheet_coord.append(entry)
    print(Sheet_coord)


    # re_order packing
    output = []
    for i in range(len(parts)):
        for j in range(len(parts)):
            if Packings[j][0] == i:
                output.append(Packings[j][1])

    '''for i in range(len(PARTS)):
        print(output[i])'''
        
    OUTPUT = json.dumps({"results":{'parts': output,
                'sheets': Sheet_coord}})
    return OUTPUT