from unittest import mock

from django.test import Client, RequestFactory, TestCase

from .apimodels import Error, PROTerm, SearchParameter
from .renders import PlainTextRenderer, TsvRenderer
from .serializers import ErrorSerializer, PAFSerialzier, PROTermSerializer
from .sparql import SparqlSearch
from .views import getSearchParameter


def make_search_parameter(**overrides):
    """Build a SearchParameter with overridden attributes."""
    sp = SearchParameter()
    for key, value in overrides.items():
        setattr(sp, key, value)
    return sp


class SearchParameterTests(TestCase):

    def test_defaults(self):
        sp = SearchParameter()
        self.assertEqual(sp.searchField, 'AllFields')
        self.assertEqual(sp.searchValue, '')
        self.assertTrue(sp.showAltID)
        self.assertTrue(sp.showParent)
        self.assertFalse(sp.showAnnotation)
        self.assertEqual(sp.offset, '0')
        self.assertEqual(sp.limit, '50')

    def test_prom_term_defaults(self):
        pt = PROTerm()
        self.assertEqual(pt.id, '')
        self.assertEqual(pt.annotation, [])
        self.assertEqual(pt.parent, [])


class SerializerTests(TestCase):

    def test_error_serializer(self):
        err = Error()
        err.code = 200
        err.message = 'OK'
        data = ErrorSerializer(err).data
        self.assertEqual(data['code'], '200')
        self.assertEqual(data['message'], 'OK')

    def test_proterm_serializer_filters_empty_fields(self):
        pt = PROTerm()
        pt.id = 'PR:000000001'
        data = PROTermSerializer(pt).data
        self.assertIn('id', data)
        self.assertEqual(data['id'], 'PR:000000001')
        self.assertNotIn('name', data)
        self.assertNotIn('annotation', data)


class RendererTests(TestCase):

    def test_plain_text_renderer_passthrough(self):
        renderer = PlainTextRenderer()
        self.assertEqual(renderer.render('hello'), 'hello')

    def test_tsv_renderer_header_and_rows(self):
        renderer = TsvRenderer()
        fields = list(PAFSerialzier.Meta.fields)
        row = dict.fromkeys(fields, '')
        row['PRO_ID'] = 'PR:000000001'
        row['Object_term'] = 'kinase'
        output = renderer.render([row])
        lines = output.split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], '\t'.join(fields))
        self.assertEqual(lines[1].split('\t'), list(row.values()))
        self.assertEqual(lines[1].split('\t')[0], 'PR:000000001')
        self.assertEqual(lines[1].split('\t')[1], 'kinase')

    def test_tsv_renderer_multiple_rows(self):
        renderer = TsvRenderer()
        fields = list(PAFSerialzier.Meta.fields)
        rows = [dict.fromkeys(fields, '') for _ in range(3)]
        rows[1]['PRO_ID'] = 'PR:000000002'
        output = renderer.render(rows)
        lines = output.split('\n')
        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[1], '\t'.join('' for _ in fields))
        self.assertEqual(lines[2].split('\t')[0], 'PR:000000002')


class SparqlSearchQueryTests(TestCase):
    """Unit tests for SPARQL query construction (no network access)."""

    def setUp(self):
        self.ss = SparqlSearch()

    def test_get_display_field_keys_defaults(self):
        keys = self.ss.getDisplayFieldKeys(SearchParameter())
        self.assertIn('ID', keys)
        self.assertIn('DB_ID', keys)
        self.assertIn('ALT_ID', keys)
        self.assertNotIn('ANNOTATION', keys)
        self.assertNotIn('ANCESTOR', keys)
        self.assertNotIn('TAXON_ID', keys)

    def test_get_display_field_keys_flags(self):
        sp = make_search_parameter(showAnnotation=True, showAncestor=True)
        keys = self.ss.getDisplayFieldKeys(sp)
        self.assertIn('ANNOTATION', keys)
        self.assertIn('ANCESTOR', keys)
        self.assertIn('CATEGORY', keys)
        self.assertIn('PARENT', keys)

    def test_construct_filter_query_all_fields_with_value(self):
        sp = make_search_parameter(searchField='AllFields', searchValue='kinase')
        query, _ = self.ss.constructFilterQuery(sp)
        self.assertIn('?PRO_term  pr_extra:allFields ?fieldValue', query)
        self.assertIn('FILTER(CONTAINS(ucase(?fieldValue)', query)
        self.assertIn('KINASE', query)

    def test_construct_filter_query_all_fields_empty(self):
        sp = make_search_parameter(searchField='AllFields', searchValue='')
        query, _ = self.ss.constructFilterQuery(sp)
        self.assertIn('oboInOwl:id ?PRO_ID', query)
        self.assertIn("STRSTARTS(?PRO_ID, 'PR:')", query)

    def test_construct_filter_query_pro_id(self):
        sp = make_search_parameter(searchField='PRO_ID', searchValue='PR:000000001')
        query, _ = self.ss.constructFilterQuery(sp)
        self.assertIn('oboInOwl:id ?PRO_ID', query)
        self.assertIn('PR_000000001', query)

    def test_construct_filter_query_null_value(self):
        sp = make_search_parameter(searchField='TAXON_ID', searchValue='NOT NULL')
        query, _ = self.ss.constructFilterQuery(sp)
        self.assertIn('NCBITaxon_ID', query)

    def test_construct_uniprotkbid_filter_query_not_null(self):
        query, updated = self.ss.constructUniProtKBIDFilterQuery(
            '{\n', SearchParameter(), 'NOT NULL')
        self.assertTrue(updated.showUniProtKBID)
        self.assertIn('UNIPROTKB_ID', query)

    def test_construct_uniprotkbid_filter_query_value(self):
        query, _ = self.ss.constructUniProtKBIDFilterQuery(
            '{\n', SearchParameter(), 'P12345')
        self.assertIn('STRSTARTS', query)
        self.assertIn('P12345', query)

    def test_construct_pro_ids_query(self):
        query, _ = self.ss.constructProIDsQuery(SearchParameter(), 'PRO_ID')
        self.assertIn('SELECT', query)
        self.assertIn('WHERE', query)
        self.assertIn('ORDER BY DESC(?PRO_ID)', query)
        self.assertIn('OFFSET 0', query)
        self.assertIn('LIMIT 50', query)

    def test_get_values_statement(self):
        pt = PROTerm()
        pt.id = '"PR:000000001"'
        statement = self.ss.getValuesStatement([pt])
        self.assertIn('VALUES ?PRO_term {', statement)
        self.assertIn('obo:PR_000000001', statement)

    def test_get_pro_term(self):
        pt = PROTerm()
        pt.id = 'PR:000000001'
        self.assertIsNone(self.ss.getProTerm([], 'PR:000000001'))
        self.assertIs(self.ss.getProTerm([pt], 'PR:000000001'), pt)

    def test_merge_dicts(self):
        merged = self.ss.mergeDicts({'a': '1'}, {'b': '2'})
        self.assertEqual(merged, {'a': '1', 'b': '2'})

    def test_merge_dicts_preserves_existing(self):
        merged = self.ss.mergeDicts({'a': '1'}, {'a': '1'})
        self.assertEqual(merged, {'a': '1'})

    def test_create_obo_stanza(self):
        stanza = self.ss.createOBOStanza({
            'id': 'PR:000000001',
            'name': 'test protein',
        })
        self.assertIn('[Term]', stanza)
        self.assertIn('id: PR:000000001', stanza)
        self.assertIn('name: test protein', stanza)


class ExecuteQueryTests(TestCase):
    """Unit tests for executeQuery() with a mocked HTTP transport."""

    def setUp(self):
        self.ss = SparqlSearch()

    @mock.patch('api_v1.sparql.requests.post')
    def test_execute_query_ok(self, mock_post):
        response = mock.Mock()
        response.status_code = 200
        response.text = '?id\t?name\n"PR:000000001"\t"test"\n'
        mock_post.return_value = response

        result, error = self.ss.executeQuery('SELECT ...')

        self.assertIsNone(error)
        self.assertEqual(result, [{'id': 'PR:000000001', 'name': 'test'}])

    @mock.patch('api_v1.sparql.requests.post')
    def test_execute_query_error(self, mock_post):
        response = mock.Mock()
        response.status_code = 500
        response.text = 'server error'
        mock_post.return_value = response

        result, error = self.ss.executeQuery('SELECT ...')

        self.assertIsInstance(error, Error)
        self.assertEqual(error.code, 500)
        self.assertEqual(error.message, 'server error')
        self.assertEqual(result, [])


class GetSearchParameterTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_defaults_when_no_params(self):
        sp = getSearchParameter(self.factory.get('/pros/'))
        self.assertEqual(sp.searchField, 'AllFields')
        self.assertEqual(sp.searchValue, '')
        self.assertTrue(sp.showAltID)
        self.assertTrue(sp.showParent)
        self.assertFalse(sp.showAnnotation)
        self.assertEqual(sp.offset, '0')
        self.assertEqual(sp.limit, '50')

    def test_parses_query_params(self):
        request = self.factory.get('/pros/', {
            'searchField': 'PRO_ID',
            'searchValue': 'PR:000000001',
            'showParent': 'true',
            'showAnnotation': 'true',
            'Offset': '10',
            'Limit': '25',
        })
        sp = getSearchParameter(request)
        self.assertEqual(sp.searchField, 'PRO_ID')
        self.assertEqual(sp.searchValue, 'PR:000000001')
        self.assertTrue(sp.showParent)
        self.assertTrue(sp.showAnnotation)
        self.assertEqual(sp.offset, '10')
        self.assertEqual(sp.limit, '25')

    def test_show_annotation_enabled_for_ontology_id(self):
        request = self.factory.get('/pros/', {'searchField': 'Ontology_ID'})
        sp = getSearchParameter(request)
        self.assertTrue(sp.showAnnotation)


class SearchViewTests(TestCase):
    """Tests for the API views with a mocked SparqlSearch (no network)."""

    @mock.patch('api_v1.views.SparqlSearch')
    def test_pro_search_ok(self, MockSparqlSearch):
        mock_search = MockSparqlSearch.return_value
        mock_search.proSearch.return_value = ([], None)

        resp = Client().get('/pros/?searchField=PRO_ID&searchValue=PR:000000001')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])
        MockSparqlSearch.assert_called_once()
        searchParameter, restriction = mock_search.proSearch.call_args.args
        self.assertEqual(restriction, 'PRO_ID')
        self.assertEqual(searchParameter.searchValue, 'PR:000000001')

    @mock.patch('api_v1.views.SparqlSearch')
    def test_pro_search_error(self, MockSparqlSearch):
        err = Error()
        err.code = 500
        err.message = 'boom'
        mock_search = MockSparqlSearch.return_value
        mock_search.proSearch.return_value = ([], err)

        resp = Client().get('/pros/?searchField=PRO_ID&searchValue=X')

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['code'], '500')
        self.assertEqual(data['message'], 'boom')

    @mock.patch('api_v1.views.SparqlSearch')
    def test_obo_endpoint(self, MockSparqlSearch):
        mock_search = MockSparqlSearch.return_value
        mock_search.oboSearch.return_value = ('stanza text', None)

        resp = Client().get('/obo/PR_000000001/')

        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/plain', resp['Content-Type'])
        self.assertContains(resp, 'stanza text')

    @mock.patch('api_v1.views.SparqlSearch')
    def test_paf_endpoint(self, MockSparqlSearch):
        mock_search = MockSparqlSearch.return_value
        mock_search.pafSearch.return_value = ([], None)

        resp = Client().get('/paf/PR:000000001/')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    @mock.patch('api_v1.views.SparqlSearch')
    def test_parent_endpoint(self, MockSparqlSearch):
        mock_search = MockSparqlSearch.return_value
        mock_search.proParent.return_value = ([], None)

        resp = Client().get('/dag/parent/PR:000000001/')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])


class SparqlSearchIntegrationTests(TestCase):
    """Integration tests against the live SPARQL endpoint.

    These require network access and are skipped when the endpoint is
    unreachable.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ss = SparqlSearch()
        try:
            result, error = ss.executeQuery('SELECT * WHERE {?s ?p ?o .} LIMIT 1')
            cls.endpoint_available = error is None
        except Exception:
            cls.endpoint_available = False

    def test_sparql_query_ok(self):
        if not self.endpoint_available:
            self.skipTest('SPARQL endpoint not reachable')
        ss = SparqlSearch()
        query = "select ?s, ?p, ?o where {?s ?p ?o .} limit 2"
        result, error = ss.executeQuery(query)
        self.assertIsNone(error)
        self.assertIsInstance(result, list)

    def test_sparql_query_notok(self):
        if not self.endpoint_available:
            self.skipTest('SPARQL endpoint not reachable')
        ss = SparqlSearch()
        query = "select ?s, ?p, ?o here {?s ?p ?o .} limit 2"
        result, error = ss.executeQuery(query)
        self.assertNotEqual(error.code, 200)
