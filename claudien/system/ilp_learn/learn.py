class LearningProblem(object):
    """Generic learning problem."""
    
    def __init__(self):
        pass

    def init(self):
        raise NotImplementedError()
        
    def next(self, iteration=None):
        raise NotImplementedError()
        
    def update(self, update):
        # Returns a list of new learning problems
        raise NotImplementedError()
        
    def get_model(self):
        """Extract the model."""
        raise NotImplementedError()
                
    def solve(self):
        iteration = 0
        self.init()
        lps = [self]
        while lps:
            lp = lps.pop(0)
            h = lp.next(iteration)
            iteration += 1
            lps += lp.update(h)
        return self
