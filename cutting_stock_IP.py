'''
Sketches for IP model for cutting stock -- 

DEPENDS ON: 
Pyomo (optmization modeling framework), 
GLPK (linear/integer programming solver),
Numpy.

-- LOOK into how to adjust solver settings, 
for larger problems probably want to include 
some cutting planes, and also maybe look at 
tightening up the formulation ourselves.

-- NEED to adjust the objective function 
to penalize positions that aren't densely packed
(e.g. one piece on a sheet, but placed in 
the middle instead of edge -- could just add 
-1*(max_L + max_H) for each sheet, this should 
be enough to push things towards the origin)



As always, still to make sure nothing weird is going on...

Maybe try translating to Julia? 
'''
import numpy as np
from pyomo.environ import *

# dimension of sheet (x,y)
Sheet_dim = [96.0,48.0]

'''
SEEMS like parts have to be labeled numerically, BUT 
should look into this, cuz it doesn't seem quite right...

In any case, could write 
a line to convert back and forth...
the dict  for now is: 
{(Part) i: [length, height]}
'''
#PARTS = {1: [72.0, 36.0], 
#		2:[24.,48.0], 
#		3:[60., 36.0],}

PARTS = { 1: [39.54, 9.37], 
		2: [39.54, 9.37], 
		3: [39.54, 9.37], 
		4: [39.54, 9.37], 
		5: [39.54, 9.37], 
		6: [39.54, 9.37], 
		7: [39.54, 9.37] }

### Initialize indices for 
N = [i for i in range(len(PARTS))]

''' 
Define big M's for the disjunctive constraints:
Never more than (dim[0],dim[1]) units from the origin, so this 
should suffice to switch the constraints on and off...
'''
M_L = Sheet_dim[0]
M_H = Sheet_dim[1]

def Model(parts):
	'''
	Build the integer programming model for
	any given input parts list.
	
	Mathematical Formulation: 
	
	N = # of pieces
	B = possible bins (at most N)
	
	Variables:
	y_ib = {0 or 1} for piece i and bin b (is i in b or not)
	0 <= x_ij <= 1 for pieces i and j (are i and j in same bin)
	0 <= v_b <= 1, for bin b (is bin b used or not)
	r_ij = {0 or 1} for pieces i and j (i to the right of j)
	l_ij = {0 or 1} for pieces i and j (i to the left of j)
	a_ij = {0 or 1} for pieces i and j (i above j)
	b_ij = {0 or 1} for pieces i and j (i below j)
	0 <= L_i <= 8 for piece i (Length coordinate of lwr left corner)
	0 <= H_i <= 8 for piece i (Height coordinate of lwr left corner)
	
	minimize  (v_1 + v_2 + ... + v_N) + (1/(2*10* # PARTS)) * (L_1+..L_N + H_1+..+H_N) 
	
	
		subject to: 
	v_b >= y_ib						for all i = 1..N ,  b = 1..B
	y_i1 + y_i2 +.. + y_iB = 1		for all i = 1..N (each piece assigned once)
	y_ib = 0						for i = 1..(N-1), b>i (breaks symmetry of potential solutions)
	L_i + LDim_i <= LDim_Bin		for all i = 1..N
	H_i + HDim_i <= HDim_Bin		for all i = 1..N
	r_ij + l_ij + a_ij + b_ij = 1	for all 1 <= i < j <= N
	x_ij - y_ib - y_jb >=  - 1		for all b = 1..B, 1<= i < j <= N 	
	L_j+LDim_j-(2 -x_ij -r_ij)*8 <= L_i  	for 1 <= i < j <= N
	L_i+LDim_i-(2 -x_ij -l_ij)*8 <= L_j		for 1 <= i < j <= N
	H_j+HDim_j-(2 -x_ij -a_ij)*4 <= L_i		for 1 <= i < j <= N
	H_i+HDim_i-(2 -x_ij -b_ij)*4 <= L_j		for 1 <= i < j <= N

	'''
	model = ConcreteModel()
	
	model.PIECES = Set(initialize = list(parts.keys()))
	
	## for indexing the symmetry breaking constraints - 
	## there isn't one for the last piece
	model.PC_min_1 = Set(initialize = parts.keys(),filter = lambda model, i: i < len(parts))
	model.BINS = Set(initialize = N)
	
	## only need to consider UNORDERED pairs of distinct parts
	model.PAIRS = Set(initialize = model.PIECES * model.PIECES, dimen = 2, 
						filter = lambda model, i, j: i < j)	
	# Length
	model.LENGTH = Param(model.PIECES, initialize = lambda model, j: parts[model.PIECES[j]][0])
	model.HEIGHT = Param(model.PIECES, initialize = lambda model, j: parts[model.PIECES[j]][1])
	
	# variable assigning each part to a bin 
	model.y = Var(model.PIECES, model.BINS, domain = Binary)
	
	# keep track of whether a bin is chosen
	model.v = Var(model.BINS, bounds = (0,1))
	
	# variable that is forced to 1 if both in same bin
	model.x = Var(model.PAIRS, bounds = (0,1))
	
	# for each pair, one is to the right, and one is above
	model.right = Var(model.PAIRS, domain = Binary)
	model.above = Var(model.PAIRS, domain = Binary)
	model.left = Var(model.PAIRS, domain = Binary)
	model.below = Var(model.PAIRS, domain = Binary)
	
	# variable for Length coordinate of lower left corner 
	model.L = Var(model.PIECES, bounds = (0,Sheet_dim[0]))
	
	# Height coordinate 
	model.H = Var(model.PIECES, bounds = (0,Sheet_dim[1]))
	
	'''
	Still need to add a term that penalizes the 
	"space between pieces, and between pieces and the 
	sides"
	'''
	model.obj = Objective(expr = sum(model.v[j] for j in model.BINS) + 
	(1/(2*(Sheet_dim[0] + Sheet_dim[1])*len(PARTS)))* (sum(model.L[i] for i in model.PIECES)+ sum(model.H[i] for i in model.PIECES)), sense = minimize)
	
	model.v_cons = Constraint(model.PIECES, model.BINS, rule = lambda model, i, j: model.y[i,j] <= model.v[j])
	
	## make sure each piece is assigned
	model.assign = Constraint(model.PIECES, rule = lambda model, i: sum(model.y[i,j] for j in model.BINS) == 1)
	
	### symmetry breaking --  piece i is never assigned to a bin greater than i
	model.sym = Constraint(model.PC_min_1, rule = lambda model, i : sum(model.y[i,j] for j in range(i ,len(PARTS)) ) == 0)
	
	## making sure that no piece goes outside the borders of the sheet
	model.BIN_L = Constraint(model.PIECES, rule = lambda model,j: model.LENGTH[j] + model.L[j] <= Sheet_dim[0])
	model.BIN_H = Constraint(model.PIECES, rule = lambda model,j: model.HEIGHT[j] + model.H[j] <= Sheet_dim[1])
	
	## keep track of when a pair is in the same bin
	model.BIN_PAIRS = Constraint(model.PAIRS, model.BINS, rule = lambda model, i, j,b: model.x[i,j] >= model.y[i,b] + model.y[j,b] - 1)
	
	##### making sure that pieces in the same bin do not overlap #####
	## at least one separating line
	model.sides = Constraint(model.PAIRS, rule = lambda model, i, j: model.right[i,j] + model.left[i,j] + model.above[i,j] + model.below[i,j] == 1)
	
	## enforces the chosen separating line
	model.OVRLP_1 = Constraint(model.PAIRS, rule = lambda model, i,j: model.L[i] >= model.L[j] + model.LENGTH[j] - (1- model.x[i,j] + 1-model.right[i,j]) * M_L)
	model.OVRLP_2 = Constraint(model.PAIRS, rule = lambda model, i,j: model.H[i] >= model.H[j] + model.HEIGHT[j] - (1- model.x[i,j] + 1-model.above[i,j]) * M_H)
	model.OVRLP_3 = Constraint(model.PAIRS, rule = lambda model, i,j: model.L[j] >= model.L[i] + model.LENGTH[i] - (1-model.x[i,j] + 1 - model.left[i,j]) * M_L)
	model.OVRLP_4 = Constraint(model.PAIRS, rule = lambda model, i,j: model.H[j] >= model.H[i] + model.HEIGHT[i] - (1-model.x[i,j] + 1- model.below[i,j]) * M_H)

	return model

	
def Solve(model):
	'''
	Solve the model:
	
	Can reformat the output however you want...
	'''
	## look into how to add options, I think it will be in this step...
	SolverFactory('glpk').solve(model)
	
	## format output
	results = []
	results1 = []
	for i in range(1,len(PARTS)+1):
		B_results = [value(model.y[i,j]) for j in range(len(PARTS))]
		## only ONE **should* be 1, the rest 0, so this 
		## **should** pick out the sheet where part i is placed
		sheet_i = np.argmax(B_results)
		results.append({'part': i,'x': value(model.L[i]) , 'y':value(model.H[i]) + 50*sheet_i})
		results1.append({'part': i, 'sheet': sheet_i, 'x': value(model.L[i]), 'y':value(model.H[i])})
	
	num_sheets = sum(value(model.v[i])  for i in model.BINS)
	#loc_results = [{'part': i, 'sheet': sheetzz[i], 'x': value(model.L[i]), 'y':value(model.H[i])} for i in model.PIECES]
	print('new',results)
	#print('old',results1)
	print('Sheets needed:',num_sheets)
	
	
def Cutting_stock(parts):
	'''
	combine both
	
	So to solve, simply run the script and then 
	do Cutting_stock(given_parts_list) for any 
	parts list (in the appropriate format -- 
	OR add a formatting step in this function to turn it 
	into the appropriate format...)
	
	Could (should?) also include sheet size (and big M's)
	as inputs here...
	'''
	
	
	return Solve(Model(parts))	

