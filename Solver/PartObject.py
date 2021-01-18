"""
Piece object

Stores: 
- dimensions
- name 
- position in the ORIGINAL list of parts given
- sheet number 
- coordinate of lower left corner

"""

class Part:
	def __init__(dimension, name, positionInList):
		self.Dim = dimension
		self.Name = name
		self.Index = positionInList
		# these get instantiated during the algorithm
		self.Sheet = None
		self.LLCoord = None