import re

#==============================================================================
### Class Helper (jul_helper)
#==============================================================================    
class JulHelper():
    def __init__(self):
        super().__init__()

    #Creating a query without comments to be executed. Remember that
    #comments are those that begin with --or /**/
    def cleanQ(queries, params={}):
        #Removing block comments
        queries=re.sub(r'/\*(.*?)\*/', ' ', queries, flags=re.DOTALL)
        #Removing comment from a line
        queries=re.sub(r'\s*\-\-.*', '', queries)
        #Removing double spaces
        queries=re.sub(r'\s+',' ',queries)
        #Adding the parameters, if you have them.
        if len(params)>0:
            for par in params:
                #Replacing each of the parameters
                queries=queries.replace(par, str(params[par]))
        #Generating output
        return(queries)