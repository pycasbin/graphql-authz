import functools
import os
from unittest import TestCase

import casbin
from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    graphql_sync,
)

from authz.middleware import enforcer_middleware


def get_examples(path):
    examples_path = os.path.split(os.path.realpath(__file__))[0] + "/../examples/"
    return os.path.abspath(examples_path + path)


def sub_test(param_list):
    """Decorates a test case to run it as a set of subtests."""

    def decorator(f):
        @functools.wraps(f)
        def wrapped(self):
            for param in param_list:
                with self.subTest(**param):
                    f(self, **param)

        return wrapped

    return decorator


class TestConfig(TestCase):
    def given_a_graphql_schema(self) -> GraphQLSchema:
        ticket_type = GraphQLObjectType(
            name="TicketType",
            fields={
                "id": GraphQLField(GraphQLInt),
                "message": GraphQLField(GraphQLString),
            },
        )
        member_type = GraphQLObjectType(
            name="MemberType",
            fields={
                "id": GraphQLField(GraphQLInt),
                "name": GraphQLField(GraphQLString),
                "tickets": GraphQLField(
                    GraphQLList(ticket_type),
                    resolve=lambda member, _info: [
                        {"id": 1, "message": f"Member {member['id']}, Ticket: 1"},
                        {"id": 2, "message": f"Member {member['id']}, Ticket: 2"},
                        {"id": 3, "message": f"Member {member['id']}, Ticket: 3"},
                        {"id": 4, "message": f"Member {member['id']}, Ticket: 4"},
                    ],
                ),
            },
        )
        project_type = GraphQLObjectType(
            name="ProjectType",
            fields={
                "id": GraphQLNonNull(GraphQLInt),
                "name": GraphQLField(GraphQLString),
                "members": GraphQLField(
                    GraphQLList(member_type),
                    resolve=lambda project, _info: [
                        {"id": 1, "name": f"Project {project['id']}, Member: 1"},
                        {"id": 2, "name": f"Project {project['id']}, Member: 2"},
                    ],
                ),
            },
        )
        query_type = GraphQLObjectType(
            name="Query",
            fields={
                "project": GraphQLField(
                    project_type,
                    args={"id": GraphQLArgument(GraphQLInt)},
                    resolve=lambda _source, _info, id: {
                        "id": id,
                        "name": f"Project {id}",
                    },
                ),
                "projects": GraphQLField(
                    GraphQLList(project_type),
                    resolve=lambda _source, _info, id: [
                        {"id": 1, "name": "Project 1"},
                        {"id": 2, "name": "Project 2"},
                    ],
                ),
            },
        )
        return GraphQLSchema(query_type)

    def given_an_enforcer(self):
        return casbin.Enforcer(get_examples("model.conf"), get_examples("policy.csv"))

    def test_graphql_middleware(self):
        schema = self.given_a_graphql_schema()
        enforcer = self.given_an_enforcer()

        query = """{
            project(id: 2) {
                id name members {
                    id name tickets {
                        id message
                    }
                }
            }
        }"""
        casbin_middleware = enforcer_middleware(enforcer)

        response = graphql_sync(
            schema,
            query,
            middleware=[casbin_middleware],
            context_value={"role": "user"},
        )

        self.assertEqual(
            response.errors[0].formatted,
            {
                "message": "user can not query project.name",
                "path": ["project", "name"],
                "locations": [{"line": 3, "column": 20}],
            },
        )

        self.assertEqual(
            response.errors[1].formatted,
            {
                "message": "user can not query project.members.tickets.message",
                "path": ["project", "members", 0, "tickets", 0, "message"],
                "locations": [{"line": 5, "column": 28}],
            },
        )

        self.assertEqual(
            response.errors[2].formatted,
            {
                "message": "user can not query project.members.tickets.message",
                "path": ["project", "members", 0, "tickets", 1, "message"],
                "locations": [{"line": 5, "column": 28}],
            },
        )

        self.assertEqual(
            response.errors[3].formatted,
            {
                "message": "user can not query project.members.tickets.message",
                "path": ["project", "members", 0, "tickets", 2, "message"],
                "locations": [{"line": 5, "column": 28}],
            },
        )

        self.assertEqual(
            response.errors[4].formatted,
            {
                "message": "user can not query project.members.tickets.message",
                "path": ["project", "members", 0, "tickets", 3, "message"],
                "locations": [{"line": 5, "column": 28}],
            },
        )

        self.assertEqual(
            response.errors[5].formatted,
            {
                "message": "user can not query project.members.tickets.message",
                "path": ["project", "members", 1, "tickets", 0, "message"],
                "locations": [{"line": 5, "column": 28}],
            },
        )

        self.assertEqual(
            response.errors[6].formatted,
            {
                "message": "user can not query project.members.tickets.message",
                "path": ["project", "members", 1, "tickets", 1, "message"],
                "locations": [{"line": 5, "column": 28}],
            },
        )

        self.assertEqual(
            response.errors[7].formatted,
            {
                "message": "user can not query project.members.tickets.message",
                "path": ["project", "members", 1, "tickets", 2, "message"],
                "locations": [{"line": 5, "column": 28}],
            },
        )

        self.assertEqual(
            response.errors[8].formatted,
            {
                "message": "user can not query project.members.tickets.message",
                "path": ["project", "members", 1, "tickets", 3, "message"],
                "locations": [{"line": 5, "column": 28}],
            },
        )

        self.assertEqual(
            response.data,
            {
                "project": {
                    "id": 2,
                    "name": None,
                    "members": [
                        {
                            "id": 1,
                            "name": "Project 2, Member: 1",
                            "tickets": [
                                {"id": 1, "message": None},
                                {"id": 2, "message": None},
                                {"id": 3, "message": None},
                                {"id": 4, "message": None},
                            ],
                        },
                        {
                            "id": 2,
                            "name": "Project 2, Member: 2",
                            "tickets": [
                                {"id": 1, "message": None},
                                {"id": 2, "message": None},
                                {"id": 3, "message": None},
                                {"id": 4, "message": None},
                            ],
                        },
                    ],
                }
            },
        )

    @sub_test([dict(context={"role": "*"}), dict(context={})])
    def test_graphql_middleware_as_anonymous(self, context):
        schema = self.given_a_graphql_schema()
        enforcer = self.given_an_enforcer()

        query = """{
            project(id: 2) {
                id name
            }
        }"""
        casbin_middleware = enforcer_middleware(enforcer)

        response = graphql_sync(
            schema, query, middleware=[casbin_middleware], context_value=context
        )

        self.assertEqual(
            response.errors[0].formatted,
            {
                "message": "anonymous can not query project.name",
                "path": ["project", "name"],
                "locations": [{"line": 3, "column": 20}],
            },
        )
        self.assertEqual(response.data, {"project": {"id": 2, "name": None}})

    def test_graphql_middleware_unauthorized_querying_non_nullable_fields(self):
        schema = self.given_a_graphql_schema()
        enforcer = casbin.Enforcer(
            get_examples("model.conf"),
            get_examples("policy_with_project_id_restricted.csv"),
        )

        query = """{
            project(id: 2) {
                id name
            }
        }"""
        casbin_middleware = enforcer_middleware(enforcer)

        response = graphql_sync(
            schema,
            query,
            middleware=[casbin_middleware],
            context_value={"role": "unathorized_user"},
        )

        self.assertEqual(
            response.errors[0].formatted,
            {
                "message": "unathorized_user can not query project.id",
                "path": ["project", "id"],
                "locations": [{"line": 3, "column": 17}],
            },
        )
        self.assertEqual(response.data, {"project": None})
