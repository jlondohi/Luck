#from openai import OpenAI
OpenAI = None
#=============================================
#Creating functions related to AI in general
#=============================================
def aiQueryAnalizer(self):
    #Saving the session
    self.actualSession.saveSession(self.tab_info)
    #Taking the query
    query = self.identifyQuery()
    if query == "":
        print("No se ha encontrado ningún query para analizar.")
        return None
    
    #Setting the message to send to the API
    messages = [
        {"role": "system", "content": "Eres un asistente experto en SQL, enlazado con un programa que supervisa un editor de SQL. Dame answers codificadas: para errores de sintaxis usa el formato “SE-línea-columna-error”, donde debes reemplazar línea, columna y error por su correspondiente valor. Respuestas cortas para el error."},
        {"role": "user", "content": f"Por favor, analiza este query SQL y encuentra posibles errores de sintaxis:\n\n{query}"}
    ]
    
    #Instantiating OpenAI
    self.clientAI = OpenAI(
        organization = "org-pnNIcGdbAZh8GzlPrNoZKTYf",
        api_key = str( open("noFunctional\\Luck_AI.txt", mode="r").read() )
    )

    #Sending the message
    try:
        response = self.clientAI.chat.completions.create(model = "gpt-4o-mini",
                                                        messages = [{"role": "user", "content": "Hello world"}])
        #Getting the answer
        ai_message = response['choices'][0]['message']['content']
        #Printing or processing the response
        print(f"Respuesta de la IA:\n{ai_message}")
        return ai_message
    except Exception as e:
        print(f"Error al analizar el query con la IA: {e}")
        return None

def sqlfluffAnalizer(self):
    #Saving the session
    self.actualSession.saveSession(self.tab_info)
    #Setting query
    self.fluffAnalizer.query = self.identifyQuery()
    #Starting analyzer
    self.fluffAnalizer.start()


