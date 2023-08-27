# graphql-authz


GraphQL-Authz is a Python3.6+ port of [GraphQL-Authz](https://github.com/node-casbin/graphql-authz), the
[Casbin](https://casbin.org/) authorization middleware implementation in [Node.js](https://nodejs.org/en/).

[![build](https://github.com/pycasbin/graphql-authz/actions/workflows/build.yml/badge.svg)](https://github.com/pycasbin/graphql-authz/actions/workflows/build.yml)
[![Coverage Status](https://coveralls.io/repos/github/pycasbin/graphql-authz/badge.svg)](https://coveralls.io/github/pycasbin/graphql-authz)
[![Version](https://img.shields.io/pypi/v/casbin-graphql-authz.svg)](https://pypi.org/project/casbin-graphql-authz/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/casbin-graphql-authz.svg)](https://pypi.org/project/casbin-graphql-authz/)
[![Download](https://img.shields.io/pypi/dm/casbin-graphql-authz.svg)](https://pypi.org/project/casbin-graphql-authz/)
[![Discord](https://img.shields.io/discord/1022748306096537660?logo=discord&label=discord&color=5865F2)](https://discord.gg/S5UjpzGZjN)

This package should be used with [GraphQL-core 3](https://github.com/graphql-python/graphql-core), providing the
capability to limit access to each GraphQL resource with the authorization middleware.

## Installation

Install the package using pip.

```shell
pip install casbin-graphql-authz
```

Get Started
--------

Limit the access to each GraphQL resource with a policy. For example,
given this policy for an [RBAC](https://casbin.org/docs/rbac/) model:

```csv
p, authorized_user, hello, query
```

Authorization can be enforced using:

```python3
import casbin
from authz.middleware import enforcer_middleware

from graphql import (
    graphql_sync,
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLString,
)


schema = GraphQLSchema(
    query=GraphQLObjectType(
        name="RootQueryType",
        fields={
            "hello": GraphQLField(
                GraphQLString,
                resolve=lambda obj, info: "world")
        }))

enforcer = casbin.Enforcer("model_file.conf", "policy_file.csv")
authorization_middleware = enforcer_middleware(enforcer)

query = """{ hello }"""

# Authorized user ("authorized_user") has access to data
response = graphql_sync(
    schema,
    query,
    middleware=[authorization_middleware],
    context_value={"role": "authorized_user"}
)
assert response.data == {"hello": "world"}

# Unauthorized users ("unauthorized_user") are rejected
response = graphql_sync(
    schema,
    query,
    middleware=[authorization_middleware],
    context_value={"role": "unauthorized_user"}
)
assert response.errors[0].message == "unauthorized_user can not query hello"
```

For more interesting scenarios see `tests` folder.

## Credits

Implementation was heavily inspired by the [Node.js](https://nodejs.org/en/) middleware [GraphQL-Authz](https://github.com/node-casbin/graphql-authz).

Authorization enforcement is based on [Casbin](https://casbin.org/) authorization library.
