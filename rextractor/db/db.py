""" Module containing GraphDatabase class. """
__author__ = 'Maciej Suchecki'

from rdflib import Graph, Literal, BNode
from rdflib.namespace import OWL, XSD, RDF, RDFS
from rextractor.db.namespace import RO
from rextractor.model.recipe import AttributesDict


class GraphDatabase:
    """ Class responsible for importing Recipes into the database and exporting it to a file. """

    graph = None
    attributes_dict = None

    def __init__(self):
        self.graph = Graph()
        ontology_attributes = [RO.description, RO.serves, RO.cooking_time, RO.preparation_time]
        self.attributes_dict = dict(zip(AttributesDict._keys, ontology_attributes))

    def import_recipes(self, recipes):
        """ Imports ProcessedRecipes into the database using defined ontology.
        :param recipes: list of PreprocessedRecipes
        """
        for recipe in recipes:
            self.__import_recipe__(recipe)

    def __import_recipe__(self, recipe):
        recipe_node = BNode()
        self.graph.add((recipe_node, OWL.Class, RO.Recipe))
        self.graph.add((recipe_node, RO.url, Literal(recipe.url, datatype=XSD.string)))
        self.graph.add((recipe_node, RO.name, Literal(recipe.name, datatype=XSD.string)))

        # add ingredients
        added_ingredients = {}
        for ingredient in recipe.ingredients:
            ingredient_node = BNode()
            self.graph.add((recipe_node, RO.ingredient, ingredient_node))
            self.graph.add((ingredient_node, RO.quantity, Literal(ingredient.amount.value, datatype=XSD.decimal)))
            self.graph.add((ingredient_node, RO.unit, Literal(ingredient.amount.unit, datatype=XSD.string)))
            food_node = self.__get_or_create_food_object__(ingredient.name)
            self.graph.add((ingredient_node, RO.food, food_node))
            added_ingredients[ingredient.name] = ingredient_node

        # add preparation
        method_node = BNode()
        self.graph.add((method_node, OWL.Class, RO.Method))
        self.graph.add((recipe_node, RO.method, method_node))
        index = 1
        for step in recipe.preparation:
            step_node = BNode()
            self.graph.add((step_node, OWL.Class, RO.Step))
            self.graph.add((step_node, RO.instruction, Literal(step.text, datatype=XSD.string)))
            self.graph.add((method_node, RDF.first, Literal(index, datatype=XSD.integer)))
            self.graph.add((method_node, RDF.rest, step_node))
            index += 1
            # connect step with all of the ingredients used in it
            for ingredient in step.ingredients:
                for key, value in added_ingredients.items():
                    if key == ingredient.name:
                        self.graph.add((step_node, RO.step_ingredient, value))

        # add additional attributes
        for key, value in recipe.additional_attributes.items():
            self.graph.add((recipe_node, self.attributes_dict[key], Literal(value, datatype=XSD.string)))

    def __get_or_create_food_object__(self, food_name):
        # check if Food object with provided name already exists
        for food_object in self.graph.subjects(OWL.Class, RO.Food):
            name = str(self.graph.value(food_object, RO.food_name))
            if name == food_name:
                return food_object

        food_object = BNode()
        self.graph.add((food_object, OWL.Class, RO.Food))
        self.graph.add((food_object, RO.food_name, Literal(food_name, datatype=XSD.string)))
        return food_object

    def export_to_file(self, filename):
        """ Exports the graph database along with all of the collected Recipes to a file. """
        self.graph.bind('ro', RO)
        self.graph.bind('owl', OWL)
        self.graph.bind('xsd', XSD)
        self.graph.bind('rdf', RDF)
        self.graph.bind('rdfs', RDFS)
        self.graph.serialize(filename, format='turtle')

