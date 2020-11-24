''' ** Nearly Pure Python ** Implementation of the 
Extreme-point BFD-Heuristic for 2D-Cutting Stock Problem:

Based on "Extreme Point-Based Heuristics for 
Three-Dimensional Bin Packing" INFORMS Journal 
on Computing (2008)  Teodor Gabriel Crainic, Guido Perboli, 
Roberto Tadei,
'''


import json

def stock_cutting(request):
    data = request.get_json()
    pieces = data['dimensions']


	##################################################################
	#######   Preliminary Functions
	##################################################################


	## NEED TO IMPLEMENT THIS!!! AND TRY RANDOMIZING THE 
	## ORDER AND KEEPING TRACK OF THE "USABLE WASTE"...
	
	def order(x,vals):
		x = [i for _,i in sorted(zip(vals,x), reverse = True)]
		return x
	
	def index_sort(array,index):
		# sort a multi_dim array by index
		# MAKE SURE TO SORT BY MOST IMPORTANT INDEX LAST...
		a = array
		ind = index
		L = len(a)
		for i in range(L):
			temp = a[i]
			flag = 0
			j = 0
			while j < i and flag == 0:
				if temp[ind] < a[j][ind]:
					a[j+1] = a[j]
					a[j] = temp
					j += 1
				else:
					flag = 1
		return(a)
		
	def unq(a):
		# return unique values of an array
		u_a = []
		L = len(a)
		for i in range(L):
			if a[i] in u_a:
				continue
			else:
				u_a.append(a[i])
		return(u_a)

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
	
	#### Work with people to determine other merit functions.

	'''
	Update Extreme point list
	'''
	def proj(d1,e1,d2,e2, proj_dir):
		'''
		d1, e1 -- dim of new piece, placed at point e1
		d2, e2 -- cycle these through the other pieces
	
		ep_dir is the coordinate "pushed out" by the piece dimension in 
		the candidate extreme point
		proj_dir is the one to shrink... (number 0,1 corresponding to x, y)
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

	def Update_EP(Dims, EP, Curr_EPs, Curr_Items, piece_margin):
		'''
		Dims = 1x2 WxD of current piece placed 
			(in orienation OR* decided by Feas and Merit...)
		EP = 1x2 coordinates of lower left corner of current piece
		Curr_EPs = list of current extreme points where Curr_Items
			are located 
		Curr_Items = list of dimensions of current items 
	
		idea is you take current EP and push it out in the 
		two dimensions of the current piece, then project
		each of these towards the other axes, ending up 
		on the closest current piece it "runs into"

		'''
		p_m = piece_margin
		D = Dims
		CI = Curr_Items
		CE = Curr_EPs
		New_Eps = [[EP[0]+D[0] + p_m,EP[1]],
					[EP[0],EP[1]+D[1] + p_m]]
	
		Max_bounds = [-1., -1. ]
	
		for i in range(len(CI)):
			# shrinking y coordinate
			if proj(D, EP, CI[i], CE[i],1) and CE[i][1] + CI[i][1] + p_m > Max_bounds[1]:
				New_Eps[0] = [EP[0] + D[0] + p_m, CE[i][1] + CI[i][1] + p_m]
				Max_bounds[0] = CE[i][1] + CI[i][1] + p_m
			
	
			# shrinking x coordinate
			if proj(D, EP, CI[i], CE[i],0) and CE[i][0] + CI[i][0] + p_m > Max_bounds[0]:
				New_Eps[1] = [CE[i][0] + CI[i][0] + p_m, EP[1] + D[1] + p_m]
				Max_bounds[1] = CE[i][0] + CI[i][0] + p_m	
			
		# remove duplicates
		#New_Eps = unq(New_Eps)
		return (unq(New_Eps))



	#############
	#### Further ideas:
	#############
	'''
	Ideas for actually optimizing...
	There is SOME ordering for which this approach 
	returns the actual optimal solution, 
	so could try randomizing the ordering 
	OR branching through the orderings in a clever 
	way -- i.e. is there a way to prune 
	a partial ordering??  
	'''
	##################################################################
	#######   INPUT STAGE
	##################################################################

	## Dimension of the stock sheets
	Actual_dim = [96.0,48.0]
	## Include a margin around the OUTSIDE of the sheet
	margin = 1.0
	Sheet_dim = [Actual_dim[0] - 2*margin, Actual_dim[1] - 2*margin]

	## Margin for space between pieces (in both x and y coordinates)
	Piece_Margin = 1.0

	## part label, width, depth
	PARTS = pieces
	
	labels = list(PARTS.keys())
	parts = []
	for i in range(len(labels)):
		parts.append([labels[i], PARTS[labels[i]], i])
	
	areas = [PARTS[labels[i]][0]* PARTS[labels[i]][1] for i in range(len(labels))]
	ptp = [parts[i] for i in range(len(labels))]
	ptp = order(ptp,areas)

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
			#Ordered_RS = []
			#Ordered_EPL = []
		
			for e in range(len(EPL)):

					if Feas(Dims, EPL[e], Bin_size, Curr_Items, Curr_EP) and Merit_WD(Dims, EPL[e], Curr_Items, Curr_EP) < Best_Merit:
						Best_Merit = Merit_WD(Dims, EPL[e], Curr_Items, Curr_EP)
						e_cand = e
						packed_in = c
					 
		if packed_in is not None:
		
			k = packed_in
			EPL = SH[k]
			Curr_Items = Cr_Item[k]
			# The next line was missing before...
			Curr_EP = Cr_EPs[k]
		
		
			NE = Update_EP(Dims, EPL[e_cand], Curr_EP, Curr_Items, Piece_Margin)
		
		
			Cr_Item[k].append(Dims)
			Cr_EPs[k].append(EPL[e_cand])
			L = len(Cr_EPs[k])
			del EPL[e_cand]

			for i in range(len(NE)): 
				EPL.append(NE[i])
		
			#Sort (non-decreasing) EPs by y coordinate, then x coordinate 
			for i in range(2):
				EPL = index_sort(EPL, 1-i)
				
			# added in the margin on the outside of the sheet to the x and y 
			# i.e. shift things by (1,1) to give the location on the original sheet 
			Result = [ptp[p][2], {'part': ptp[p][0], 'x': Cr_EPs[k][L-1][0] + margin , 'y': Cr_EPs[k][L-1][1]+ margin + (5+Actual_dim[1])*packed_in}]
		
			Packings.append(Result)
		
			SH[k] = EPL 	
			
		if packed_in is None:
			SH.append([[0,0,0]])
			Cr_Item.append([])  
			Cr_EPs.append([]) 
		
			c = len(SH)-1
			packed_in = c
			EPL = SH[c]
			Curr_Items = Cr_Item[c]
			Curr_EP = Cr_EPs[c]
			e_cand = 0
				
			NE = Update_EP(Dims, EPL[e_cand], Curr_EP, Curr_Items, Piece_Margin)
		
		
			Curr_Items.append(Dims)
			Curr_EP.append(EPL[e_cand])
			L = len(Curr_EP)

			del EPL[e_cand]
		
			for i in range(len(NE)): 
				EPL.append(NE[i])
			
			#Sort (non-decreasing) EPs by y coordinate, then x coordinate 	
			for i in range(2):
				EPL = index_sort(EPL, 1-i)
				
			# added in the margin on the outside of the sheet to the x and y 
			# i.e. shift things by (1,1) to give the location on the original sheet 
			Result = [ptp[p][2],{'part': ptp[p][0], 'x': Cr_EPs[c][L-1][0]+margin , 'y': Cr_EPs[c][L-1][1]+ margin + (5+ Actual_dim[1])*packed_in}]
			Packings.append(Result)
			SH[c] = EPL
			Cr_Item[c] = Curr_Items 
			Cr_EPs[c] = Curr_EP 
		
	################################################################################
	######## OUTPUT
	################################################################################

	Sheet_coord = []

	for i in range(len(SH)):
		y = (5+ Actual_dimD[1])*i
		x = 0
		entry = {'sheet': i, 'x': x, 'y':y}
		Sheet_coord.append(entry)


	# re_order packing
	output = []
	for i in range(len(parts)):
		for j in range(len(parts)):
			if Packings[j][0] == i:
				output.append(Packings[j][1])

    OUTPUT = json.dumps({"results":{'parts': output,
                'sheets': Sheet_coord}})
    return OUTPUT
