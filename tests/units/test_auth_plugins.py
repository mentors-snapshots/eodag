# -*- coding: utf-8 -*-
# Copyright 2018, CS GROUP - France, https://www.csgroup.eu/
#
# This file is part of EODAG project
#     https://www.github.com/CS-SI/EODAG
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from unittest import mock

import responses
from requests import Request
from requests.auth import AuthBase
from requests.exceptions import RequestException

from eodag.config import override_config_from_mapping
from tests.context import (
    HTTP_REQ_TIMEOUT,
    USER_AGENT,
    AuthenticationError,
    MisconfiguredError,
    PluginManager,
)


class BaseAuthPluginTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(BaseAuthPluginTest, cls).setUpClass()
        cls.providers_config = {}
        cls.plugins_manager = PluginManager(cls.providers_config)

    def tearDown(self):
        super(BaseAuthPluginTest, self).tearDown()
        # remove credentials set during tests
        for provider in self.providers_config:
            self.get_auth_plugin(provider).config.__dict__.pop("credentials", None)

    def get_auth_plugin(self, provider):
        return self.plugins_manager.get_auth_plugin(provider)


class TestAuthPluginTokenAuth(BaseAuthPluginTest):
    @classmethod
    def setUpClass(cls):
        super(TestAuthPluginTokenAuth, cls).setUpClass()
        override_config_from_mapping(
            cls.providers_config,
            {
                "provider_text_token_simple_url": {
                    "products": {"foo_product": {}},
                    "auth": {
                        "type": "TokenAuth",
                        "auth_uri": "http://foo.bar",
                    },
                },
                "provider_text_token_format_url": {
                    "products": {"foo_product": {}},
                    "auth": {
                        "type": "TokenAuth",
                        "auth_uri": "http://foo.bar?username={username}",
                    },
                },
                "provider_text_token_header": {
                    "products": {"foo_product": {}},
                    "auth": {
                        "type": "TokenAuth",
                        "auth_uri": "http://foo.bar",
                        "headers": {
                            "Content-Type": "application/json;charset=UTF-8",
                            "Accept": "application/json",
                            "foo": "{foo}",
                        },
                    },
                },
                "provider_json_token_simple_url": {
                    "products": {"foo_product": {}},
                    "auth": {
                        "type": "TokenAuth",
                        "auth_uri": "http://foo.bar",
                        "token_type": "json",
                        "token_key": "token_is_here",
                    },
                },
            },
        )
        cls.plugins_manager = PluginManager(cls.providers_config)

    def test_plugins_auth_tokenauth_validate_credentials_empty(self):
        """TokenAuth.validate_credentials must raise an error on empty credentials"""
        auth_plugin = self.get_auth_plugin("provider_text_token_simple_url")
        self.assertRaises(
            MisconfiguredError,
            auth_plugin.validate_config_credentials,
        )

    def test_plugins_auth_tokenauth_validate_credentials_ok(self):
        """TokenAuth.validate_credentials must be ok on non-empty credentials"""
        auth_plugin = self.get_auth_plugin("provider_text_token_simple_url")

        auth_plugin.config.credentials = {"foo": "bar"}
        auth_plugin.validate_config_credentials()

    def test_plugins_auth_tokenauth_validate_credentials_format_url_missing(self):
        """TokenAuth.validate_credentials must raise an error if cannot format url"""
        auth_plugin = self.get_auth_plugin("provider_text_token_format_url")

        auth_plugin.config.credentials = {"foo": "bar"}
        self.assertRaises(
            MisconfiguredError,
            auth_plugin.validate_config_credentials,
        )

    def test_plugins_auth_tokenauth_validate_credentials_format_url_ok(self):
        """TokenAuth.validate_credentials must be ok if it can format url"""
        auth_plugin = self.get_auth_plugin("provider_text_token_format_url")

        auth_plugin.config.credentials = {"foo": "bar", "username": "john"}
        auth_plugin.validate_config_credentials()

    @mock.patch(
        "eodag.plugins.authentication.token.requests.Session.request", autospec=True
    )
    def test_plugins_auth_tokenauth_text_token_authenticate(self, mock_requests_post):
        """TokenAuth.authenticate must return a RequestsTokenAuth object using text token"""
        auth_plugin = self.get_auth_plugin("provider_text_token_header")

        auth_plugin.config.credentials = {"foo": "bar"}

        # mock token post request response
        mock_requests_post.return_value = mock.Mock()
        mock_requests_post.return_value.text = "this_is_test_token"

        # check if returned auth object is an instance of requests.AuthBase
        auth = auth_plugin.authenticate()
        assert isinstance(auth, AuthBase)

        # check token post request call arguments
        args, kwargs = mock_requests_post.call_args
        assert kwargs["url"] == auth_plugin.config.auth_uri
        assert kwargs["data"] == auth_plugin.config.credentials
        assert kwargs["headers"] == dict(auth_plugin.config.headers, **USER_AGENT)

        # check if token is integrated to the request
        req = mock.Mock(headers={})
        auth(req)
        assert req.headers["Authorization"] == "Bearer this_is_test_token"
        assert req.headers["foo"] == "bar"

    @mock.patch(
        "eodag.plugins.authentication.token.requests.Session.request", autospec=True
    )
    def test_plugins_auth_tokenauth_json_token_authenticate(self, mock_requests_post):
        """TokenAuth.authenticate must return a RequestsTokenAuth object using json token"""
        auth_plugin = self.get_auth_plugin("provider_json_token_simple_url")

        auth_plugin.config.credentials = {"foo": "bar"}

        # mock token post request response
        mock_requests_post.return_value = mock.Mock()
        mock_requests_post.return_value.json.return_value = {
            "not_token": "this_is_not_test_token",
            "token_is_here": "this_is_test_token",
        }

        # check if returned auth object is an instance of requests.AuthBase
        auth = auth_plugin.authenticate()
        assert isinstance(auth, AuthBase)

        # check if token is integrated to the request
        req = mock.Mock(headers={})
        auth(req)
        assert req.headers["Authorization"] == "Bearer this_is_test_token"

    @mock.patch(
        "eodag.plugins.authentication.token.requests.Session.post", autospec=True
    )
    def test_plugins_auth_tokenauth_request_error(self, mock_requests_post):
        """TokenAuth.authenticate must raise an AuthenticationError if a request error occurs"""
        auth_plugin = self.get_auth_plugin("provider_json_token_simple_url")

        auth_plugin.config.credentials = {"foo": "bar"}

        # mock token post request response
        mock_requests_post.side_effect = RequestException

        self.assertRaises(
            AuthenticationError,
            auth_plugin.authenticate,
        )


class TestAuthPluginHttpQueryStringAuth(BaseAuthPluginTest):
    @classmethod
    def setUpClass(cls):
        super(TestAuthPluginHttpQueryStringAuth, cls).setUpClass()
        override_config_from_mapping(
            cls.providers_config,
            {
                "foo_provider": {
                    "products": {"foo_product": {}},
                    "auth": {
                        "type": "HttpQueryStringAuth",
                        "auth_uri": "http://foo.bar",
                    },
                },
            },
        )
        cls.plugins_manager = PluginManager(cls.providers_config)

    def test_plugins_auth_qsauth_validate_credentials_empty(self):
        """HttpQueryStringAuth.validate_credentials must raise an error on empty credentials"""
        auth_plugin = self.get_auth_plugin("foo_provider")
        self.assertRaises(
            MisconfiguredError,
            auth_plugin.validate_config_credentials,
        )

    def test_plugins_auth_qsauth_validate_credentials_ok(self):
        """HttpQueryStringAuth.validate_credentials must be ok on non-empty credentials"""
        auth_plugin = self.get_auth_plugin("foo_provider")

        auth_plugin.config.credentials = {"foo": "bar"}
        auth_plugin.validate_config_credentials()

    @mock.patch("eodag.plugins.authentication.qsauth.requests.get", autospec=True)
    def test_plugins_auth_qsauth_authenticate(self, mock_requests_get):
        """HttpQueryStringAuth.authenticate must return a QueryStringAuth object using query string"""
        auth_plugin = self.get_auth_plugin("foo_provider")

        auth_plugin.config.credentials = {"foo": "bar"}

        # check if returned auth object is an instance of requests.AuthBase
        auth = auth_plugin.authenticate()
        self.assertIsInstance(auth, AuthBase)

        # check if requests.get has been sent with right parameters
        mock_requests_get.assert_called_once_with(
            auth_plugin.config.auth_uri,
            timeout=HTTP_REQ_TIMEOUT,
            headers=USER_AGENT,
            auth=auth,
            verify=True,
        )

        # check auth query string
        self.assertEqual(auth.parse_args, auth_plugin.config.credentials)

        # check if query string is integrated to the request
        req = Request("GET", "https://httpbin.org/get").prepare()
        auth(req)
        self.assertEqual(req.url, "https://httpbin.org/get?foo=bar")

        another_req = Request("GET", "https://httpbin.org/get?baz=qux").prepare()
        auth(another_req)
        self.assertEqual(another_req.url, "https://httpbin.org/get?baz=qux&foo=bar")

    @mock.patch("eodag.plugins.authentication.qsauth.requests.get", autospec=True)
    def test_plugins_auth_qsauth_request_error(self, mock_requests_get):
        """HttpQueryStringAuth.authenticate must raise an AuthenticationError if a request error occurs"""
        auth_plugin = self.get_auth_plugin("foo_provider")

        auth_plugin.config.credentials = {"foo": "bar"}

        # mock auth get request response
        mock_requests_get.side_effect = RequestException

        self.assertRaises(
            AuthenticationError,
            auth_plugin.authenticate,
        )


class TestAuthPluginSASAuth(BaseAuthPluginTest):
    @classmethod
    def setUpClass(cls):
        super(TestAuthPluginSASAuth, cls).setUpClass()
        override_config_from_mapping(
            cls.providers_config,
            {
                "foo_provider": {
                    "products": {"foo_product": {}},
                    "auth": {
                        "type": "SASAuth",
                        "auth_uri": "http://foo.bar?href={url}",
                        "signed_url_key": "href",
                        "headers": {
                            "Ocp-Apim-Subscription-Key": "{apikey}",
                        },
                    },
                },
            },
        )
        cls.plugins_manager = PluginManager(cls.providers_config)

    def test_plugins_auth_sasauth_validate_credentials_ok(self):
        """SASAuth.validate_credentials must be ok on empty or non-empty credentials"""
        auth_plugin = self.get_auth_plugin("foo_provider")

        auth_plugin.config.credentials = {}
        auth_plugin.validate_config_credentials()
        auth_plugin.config.credentials = {"apikey": "foo"}
        auth_plugin.validate_config_credentials()

    @mock.patch("eodag.plugins.authentication.sas_auth.requests.get", autospec=True)
    def test_plugins_auth_sasauth_text_token_authenticate_with_credentials(
        self, mock_requests_get
    ):
        """When a user has credentials, SASAuth.authenticate must return
        a RequestsSASAuth object with his subscription key in its headers
        """
        auth_plugin = self.get_auth_plugin("foo_provider")

        auth_plugin.config.credentials = {"apikey": "foo"}

        # mock full signed url get request response
        mock_requests_get.return_value = mock.Mock()
        mock_requests_get.return_value.json.return_value = {
            "msft:expiry": "this_is_test_key_expiration_date",
            "href": "this_is_test_full_signed_url",
        }

        # check if returned auth object is an instance of requests.AuthBase
        auth = auth_plugin.authenticate()
        assert isinstance(auth, AuthBase)

        # check if the full signed url and the subscription key are integrated to the request
        url = "url"
        req = mock.Mock(headers={}, url=url)
        auth(req)
        assert req.url == "this_is_test_full_signed_url"
        assert req.headers["Ocp-Apim-Subscription-Key"] == "foo"

        # check SAS get request call arguments
        args, kwargs = mock_requests_get.call_args
        assert args[0] == auth_plugin.config.auth_uri.format(url=url)
        auth_plugin_headers = {"Ocp-Apim-Subscription-Key": "foo"}
        self.assertDictEqual(kwargs["headers"], dict(auth_plugin_headers, **USER_AGENT))

    @mock.patch("eodag.plugins.authentication.sas_auth.requests.get", autospec=True)
    def test_plugins_auth_sasauth_text_token_authenticate_without_credentials(
        self, mock_requests_get
    ):
        """When a user does not have credentials, SASAuth.authenticate must return
        a RequestsSASAuth object without his subscription key in its headers
        """
        auth_plugin = self.get_auth_plugin("foo_provider")

        auth_plugin.config.credentials = {}

        # mock full signed url get request response
        mock_requests_get.return_value = mock.Mock()
        mock_requests_get.return_value.json.return_value = {
            "msft:expiry": "this_is_test_key_expiration_date",
            "href": "this_is_test_full_signed_url",
        }

        # check if returned auth object is an instance of requests.AuthBase
        auth = auth_plugin.authenticate()
        assert isinstance(auth, AuthBase)

        # check if only the full signed url is integrated to the request
        url = "url"
        req = mock.Mock(headers={}, url=url)
        auth(req)
        assert req.url == "this_is_test_full_signed_url"

        # check SAS get request call arguments
        args, kwargs = mock_requests_get.call_args
        assert args[0] == auth_plugin.config.auth_uri.format(url=url)
        # check if headers only has the user agent as a request call argument
        assert kwargs["headers"] == USER_AGENT

    @mock.patch("eodag.plugins.authentication.sas_auth.requests.get", autospec=True)
    def test_plugins_auth_sasauth_request_error(self, mock_requests_get):
        """SASAuth.authenticate must raise an AuthenticationError if an error occurs"""
        auth_plugin = self.get_auth_plugin("foo_provider")

        auth_plugin.config.credentials = {"apikey": "foo"}

        # mock SAS get request response
        mock_requests_get.side_effect = RequestException()

        # check if returned auth object is an instance of requests.AuthBase
        auth = auth_plugin.authenticate()
        assert isinstance(auth, AuthBase)

        req = mock.Mock(headers={}, url="url")
        with self.assertRaises(AuthenticationError):
            auth(req)


class TestAuthPluginKeycloakOIDCPasswordAuth(BaseAuthPluginTest):
    @classmethod
    def setUpClass(cls):
        super(TestAuthPluginKeycloakOIDCPasswordAuth, cls).setUpClass()
        override_config_from_mapping(
            cls.providers_config,
            {
                "foo_provider": {
                    "products": {"foo_product": {}},
                    "auth": {
                        "type": "KeycloakOIDCPasswordAuth",
                        "auth_base_uri": "http://foo.bar",
                        "client_id": "baz",
                        "realm": "qux",
                        "client_secret": "1234",
                        "token_provision": "qs",
                        "token_qs_key": "totoken",
                    },
                },
            },
        )
        cls.plugins_manager = PluginManager(cls.providers_config)

    def test_plugins_auth_keycloak_validate_credentials(self):
        """KeycloakOIDCPasswordAuth.validate_credentials must raise exception if not well configured"""
        auth_plugin = self.get_auth_plugin("foo_provider")

        # credentials missing
        self.assertRaises(MisconfiguredError, auth_plugin.validate_config_credentials)

        auth_plugin.config.credentials = {"username": "john"}

        # no error
        auth_plugin.validate_config_credentials()

        # auth_base_uri missing
        auth_base_uri = auth_plugin.config.__dict__.pop("auth_base_uri")
        self.assertRaises(MisconfiguredError, auth_plugin.validate_config_credentials)
        auth_plugin.config.auth_base_uri = auth_base_uri
        # client_id missing
        client_id = auth_plugin.config.__dict__.pop("client_id")
        self.assertRaises(MisconfiguredError, auth_plugin.validate_config_credentials)
        auth_plugin.config.client_id = client_id
        # client_secret missing
        client_secret = auth_plugin.config.__dict__.pop("client_secret")
        self.assertRaises(MisconfiguredError, auth_plugin.validate_config_credentials)
        auth_plugin.config.client_secret = client_secret
        # token_provision missing
        token_provision = auth_plugin.config.__dict__.pop("token_provision")
        self.assertRaises(MisconfiguredError, auth_plugin.validate_config_credentials)
        auth_plugin.config.token_provision = token_provision

        # no error
        auth_plugin.validate_config_credentials()

    def test_plugins_auth_keycloak_authenticate(self):
        """KeycloakOIDCPasswordAuth.authenticate must query and store the token as expected"""
        auth_plugin = self.get_auth_plugin("foo_provider")
        auth_plugin.config.credentials = {"username": "john"}

        with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
            url = "http://foo.bar/realms/qux/protocol/openid-connect/token"
            req_kwargs = {
                "client_id": "baz",
                "client_secret": "1234",
                "grant_type": "password",
                "username": "john",
            }
            rsps.add(
                responses.POST,
                url,
                status=200,
                json={"access_token": "obtained-token", "expires_in": 0},
                match=[responses.matchers.urlencoded_params_matcher(req_kwargs)],
            )

            # check if returned auth object is an instance of requests.AuthBase
            auth = auth_plugin.authenticate()
            assert isinstance(auth, AuthBase)
            self.assertEqual(auth.key, "totoken")
            self.assertEqual(auth.token, "obtained-token")
            self.assertEqual(auth.where, "qs")

        # check that token has been stored
        self.assertEqual(auth_plugin.retrieved_token, "obtained-token")

        # check that stored token is used if new auth request fails
        with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
            url = "http://foo.bar/realms/qux/protocol/openid-connect/token"
            req_kwargs = {
                "client_id": "baz",
                "client_secret": "1234",
                "grant_type": "password",
                "username": "john",
            }
            rsps.add(
                responses.POST,
                url,
                status=401,
                json={"error": "not allowed"},
                match=[responses.matchers.urlencoded_params_matcher(req_kwargs)],
            )

            # check if returned auth object is an instance of requests.AuthBase
            auth = auth_plugin.authenticate()
            assert isinstance(auth, AuthBase)
            self.assertEqual(auth.key, "totoken")
            self.assertEqual(auth.token, "obtained-token")
            self.assertEqual(auth.where, "qs")

    def test_plugins_auth_keycloak_authenticate_qs(self):
        """KeycloakOIDCPasswordAuth.authenticate must return a AuthBase object that will inject the token in a query-string"""  # noqa
        auth_plugin = self.get_auth_plugin("foo_provider")
        auth_plugin.config.credentials = {"username": "john"}

        with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
            url = "http://foo.bar/realms/qux/protocol/openid-connect/token"
            rsps.add(
                responses.POST,
                url,
                status=200,
                json={"access_token": "obtained-token", "expires_in": 0},
            )

            # check if returned auth object is an instance of requests.AuthBase
            auth = auth_plugin.authenticate()
            assert isinstance(auth, AuthBase)

            # check if query string is integrated to the request
            req = Request("GET", "https://httpbin.org/get").prepare()
            auth(req)
            self.assertEqual(req.url, "https://httpbin.org/get?totoken=obtained-token")

            another_req = Request("GET", "https://httpbin.org/get?baz=qux").prepare()
            auth(another_req)
            self.assertEqual(
                another_req.url,
                "https://httpbin.org/get?baz=qux&totoken=obtained-token",
            )

    def test_plugins_auth_keycloak_authenticate_header(self):
        """KeycloakOIDCPasswordAuth.authenticate must return a AuthBase object that will inject the token in the header"""  # noqa
        auth_plugin = self.get_auth_plugin("foo_provider")
        auth_plugin.config.credentials = {"username": "john"}

        # backup token_provision and change it to header mode
        token_provision_qs = auth_plugin.config.token_provision
        auth_plugin.config.token_provision = "header"

        with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
            url = "http://foo.bar/realms/qux/protocol/openid-connect/token"
            rsps.add(
                responses.POST,
                url,
                status=200,
                json={"access_token": "obtained-token", "expires_in": 0},
            )

            # check if returned auth object is an instance of requests.AuthBase
            auth = auth_plugin.authenticate()
            assert isinstance(auth, AuthBase)

            # check if token header is integrated to the request
            req = Request("GET", "https://httpbin.org/get").prepare()
            auth(req)
            self.assertEqual(req.url, "https://httpbin.org/get")
            self.assertEqual(req.headers, {"Authorization": "Bearer obtained-token"})

            another_req = Request(
                "GET", "https://httpbin.org/get", headers={"existing-header": "value"}
            ).prepare()
            auth(another_req)
            self.assertEqual(
                another_req.headers,
                {"Authorization": "Bearer obtained-token", "existing-header": "value"},
            )

        auth_plugin.config.token_provision = token_provision_qs

    def test_plugins_auth_keycloak_authenticate_use_refresh_token(self):
        """KeycloakOIDCPasswordAuth.authenticate must query and store the token as expected"""
        auth_plugin = self.get_auth_plugin("foo_provider")
        auth_plugin.config.credentials = {"username": "john"}

        with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
            url = "http://foo.bar/realms/qux/protocol/openid-connect/token"
            req_kwargs = {
                "client_id": "baz",
                "client_secret": "1234",
                "grant_type": "password",
                "username": "john",
            }
            rsps.add(
                responses.POST,
                url,
                status=200,
                json={
                    "access_token": "obtained-token",
                    "expires_in": 0,
                    "refresh_expires_in": 1000,
                    "refresh_token": "abc",
                },
                match=[responses.matchers.urlencoded_params_matcher(req_kwargs)],
            )

            # check if returned auth object is an instance of requests.AuthBase
            auth = auth_plugin.authenticate()
            assert isinstance(auth, AuthBase)
            self.assertEqual(auth.key, "totoken")
            self.assertEqual(auth.token, "obtained-token")
            self.assertEqual(auth.where, "qs")

        # check that token and refresh token have been stored
        self.assertEqual(auth_plugin.retrieved_token, "obtained-token")
        assert auth_plugin.token_info
        self.assertEqual("abc", auth_plugin.token_info["refresh_token"])

        # check that stored token is used if new auth request fails
        with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
            url = "http://foo.bar/realms/qux/protocol/openid-connect/token"
            req_kwargs = {
                "client_id": "baz",
                "client_secret": "1234",
                "grant_type": "refresh_token",
                "refresh_token": "abc",
            }
            rsps.add(
                responses.POST,
                url,
                status=200,
                json={
                    "access_token": "new-token",
                    "expires_in": 0,
                    "refresh_expires_in": 1000,
                    "refresh_token": "abcd",
                },
                match=[responses.matchers.urlencoded_params_matcher(req_kwargs)],
            )

            # check if returned auth object is an instance of requests.AuthBase
            auth = auth_plugin.authenticate()
            assert isinstance(auth, AuthBase)
            self.assertEqual(auth.key, "totoken")
            self.assertEqual(auth.token, "new-token")
            self.assertEqual(auth.where, "qs")
