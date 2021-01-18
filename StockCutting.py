"""
Cutting Stock Solver
"""
import json
# import Solver

def StockCutting(request):
    data = request.get_json()
    pieces = data['dimensions']
	Result = Solution(pieces).Output
	return(Result)
