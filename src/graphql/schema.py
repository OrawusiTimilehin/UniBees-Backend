import strawberry
from src.graphql.queries import Query
from src.graphql.mutations import Mutation

# This connects our Queries and Mutations into the final Schema object
# used by main.py
schema = strawberry.Schema(query=Query, mutation=Mutation)