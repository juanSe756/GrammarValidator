import graphviz
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir cualquier origen. Cambia esto para mayor seguridad.
    allow_credentials=True,
    allow_methods=["*"],  # Permitir cualquier método. Cambia esto si es necesario.
    allow_headers=["*"],  # Permitir cualquier encabezado. Cambia esto si es necesario.
)


# Definimos la estructura para la gramática, que será ingresada por el usuario
class Grammar(BaseModel):
    terminals: List[str]
    non_terminals: List[str]
    start_symbol: str
    productions: Dict[str, List[str]]

# Modelo para la palabra a validar
class WordValidationRequest(BaseModel):
    word: str

# Aquí almacenamos temporalmente la gramática
current_grammar = None
used_productions = None

@app.post("/grammar/")
async def define_grammar(grammar: Grammar):
    global current_grammar
    current_grammar = grammar
    return {"message": "Gramática ingresada correctamente", "grammar": current_grammar}


@app.post("/word/")
async def check_word(word_request: WordValidationRequest):
    if not current_grammar:
        return {"error": "Primero debes ingresar la gramática"}

    word = word_request.word

    # Lógica de verificación de pertenencia de la palabra
    belongs = verify_word(word, current_grammar)

    # Generación de árboles de derivación
    derivation_tree_particular = generate_derivation_tree_particular()
    derivation_tree_general = generate_derivation_tree_general(current_grammar)
    return {
        "word": word,
        "belongs": belongs,
        "derivation_tree_particular": derivation_tree_particular,
        "derivation_tree_general": derivation_tree_general
    }


# Función de verificación de palabra (actualizada)
def verify_word(word: str, grammar: Grammar) -> bool:
    global used_productions
    used_productions = [] # Reiniciar la lista
    used_production = ""  # Variable temporal para almacenar la producción utilizada
    def dfs(stack, word_index):
        # Si se ha consumido toda la palabra
        if word_index == len(word) and not stack:
            return True

        if not stack:  # Si el stack está vacío pero la palabra no ha sido consumida
            return False

        top = stack.pop()
        print(f"Stack: {stack}, Top: {top}, Word Index: {word_index}, Current Word: {word[word_index:]}")

        # Si es un terminal, lo comparamos con la palabra en el índice actual
        if top in grammar.terminals:
            if word_index < len(word) and word[word_index] == top:
                return dfs(stack, word_index + 1)  # Avanza el índice de la palabra
            else:
                return False  # Terminal no coincide

        # Si es un no terminal, probamos cada producción
        elif top in grammar.non_terminals:
            for production in grammar.productions[top]:
                # Descomponer la producción en símbolos
                symbols = production.split()
                # Crear un nuevo stack con los símbolos de la producción en orden inverso
                new_stack = stack.copy()  # Copiar el stack actual
                new_stack.extend(symbols[::-1])  # Agregar los nuevos símbolos

                # Almacenar la producción utilizada temporalmente
                used_production = f"{top} -> {' '.join(symbols)}"

                if dfs(new_stack, word_index):  # Llamar recursivamente
                    used_productions.append(used_production)  # Solo agregar si es exitoso
                    return True

        return False  # Símbolo no reconocido o no se pudo validar

    # Iniciar la búsqueda
    result = dfs([grammar.start_symbol], 0)
    print("----")
    print("Resultado:", result)  # Verificar si la palabra pertenece a la gramática
    # used_productions.append(used_production)
    print("Producciones utilizadas:", used_productions)  # Ver las producciones utilizadas
    return result  # Devolver el resultado final


def generate_derivation_tree_particular():
    # Inicializamos un diccionario para almacenar las conexiones
    conexiones = {}

    # Recorremos cada regla en el array
    for regla in used_productions:
        # Separamos la regla por '->' para obtener los símbolos
        partes = regla.split(' -> ')
        # Si el primer símbolo no está en las conexiones, lo agregamos
        if partes[0] not in conexiones:
            conexiones[partes[0]] = partes[1]

    # Generamos la cadena final siguiendo las conexiones
    grafo = "digraph {\n    "
    simbolo_actual = 'S'  # Empezamos por 'S' (símbolo inicial)

    while simbolo_actual in conexiones:
        grafo += simbolo_actual + " -> "
        simbolo_actual = conexiones[simbolo_actual]

    grafo += simbolo_actual + "\n"
    grafo += "}"

    return grafo

def generate_derivation_tree_general(grammar: Grammar):
    # Inicializamos la cadena del grafo
    grafo = "digraph {\n"

    # Recorremos cada clave y lista de valores en el diccionario
    for clave, valores in grammar.productions.items():
        for valor in valores:
            grafo += f"    {clave} -> {valor}\n"

    # Cerramos el grafo
    grafo += "}"

    return grafo