from flask_restplus import Namespace, Resource
from flask_restplus import fields
from flask_restplus import inputs
import sqlalchemy
from utils import sql_query_generator
from model.models import db

api = Namespace('pair', description='Operations to perform queries on key-value metadata pairs')

query = api.model('Pair', {
    'key': fields.String(attribute='column_name', required=True, description='Field name '),
    # 'info': fields.Nested(info, required=False, description='Info', skip_none=True),
})

parser = api.parser()
parser.add_argument('body', type="json", help='json ', location='json')
parser.add_argument('q', type=str)


@api.route('/keys')
@api.response(404, 'Item not found')  # TODO correct
class Key(Resource):
    @api.doc('get_keys')
    @api.expect(parser)
    def post(self):
        '''Retrieves all keys based on a input keyword'''
        args = parser.parse_args()
        key = args['q']

        payload = api.payload

        filter_in = payload.get("gcm")
        type = payload.get("type")
        pairs = payload.get("kv")
        sub_query = sql_query_generator(filter_in, type, pairs, field_selected='platform', return_type='item_id',
                                        limit=None, offset=None)
        where_start = sub_query.find("WHERE")
        from_start = sub_query.find("FROM")

        from_sub = sub_query[from_start:where_start]
        where_sub = sub_query[where_start:]

        # print(from_sub)
        # print(where_sub)
        query = f"select up.key as key, up.is_gcm as is_gcm, count(distinct up.value) as count " + from_sub + \
                " join unified_pair up on it.item_id = up.item_id" \
                    f" " + where_sub + f" and lower(up.key) like '%{key.lower()}%' " \
                    f" group by up.key, up.is_gcm"

        print("Query start")
        print(query)
        res = db.engine.execute(sqlalchemy.text(query)).fetchall()
        results_gcm = []
        results_pairs = []

        for r in res:
            print(r.is_gcm)
            if r.is_gcm:
                q = f"select up.value as value " + from_sub + \
                    " join unified_pair up on it.item_id = up.item_id " + where_sub + \
                    f" and lower(up.key) like lower('%{key}%')"
                print(q)
                res2 = db.engine.execute(sqlalchemy.text(q)).fetchall()
                values = [r2.value for r2 in res2]
                results_gcm.append({'key': r.key, 'count_values': r.count, 'values': list(set(values[:10]))})
            else:
                results_pairs.append({'key': r.key, 'count_values': r.count})

        results = {'gcm': results_gcm, 'pairs': results_pairs}

        return results


value_parser = api.parser()
value_parser.add_argument('body', type="json", help='json ', location='json')
value_parser.add_argument('is_gcm', type=inputs.boolean, default=True)


@api.route('/<key>/values')
@api.response(404, 'Item not found')  # TODO correct
class Key(Resource):
    @api.doc('get_values_for_key')
    @api.expect(value_parser)
    def post(self, key):
        '''For a specific key, it lists all possible values'''
        args = value_parser.parse_args()
        is_gcm = args['is_gcm']

        payload = api.payload
        filter_in = payload.get("gcm")
        type = payload.get("type")
        pairs = payload.get("kv")

        sub_query = sql_query_generator(filter_in, type, pairs, field_selected='platform', return_type='item_id',
                                        limit=None, offset=None)

        where_start = sub_query.find("WHERE")
        from_start = sub_query.find("FROM")

        from_sub = sub_query[from_start:where_start]
        where_sub = sub_query[where_start:]

        # print(from_sub)
        # print(where_sub)
        query = f"select up.value as value, count(up.item_id) as count " + from_sub + \
                " join unified_pair up on it.item_id = up.item_id " + where_sub + \
                f" and lower(up.key) like '%{key.lower()}%' and up.is_gcm = {is_gcm}" \
                f" group by up.value"

        print(query)
        res = db.engine.execute(sqlalchemy.text(query)).fetchall()

        result = []

        for r in res:
            result.append({'value': r.value, 'count': r.count})

        return result


@api.route('/values')
@api.response(404, 'Item not found')  # TODO correct
class Key(Resource):
    @api.doc('get_values')
    @api.expect(parser)
    def post(self):
        '''Retrieves all values based on a input keyword'''
        args = parser.parse_args()
        value = args['q']

        payload = api.payload

        filter_in = payload.get("gcm")
        type = payload.get("type")
        pairs = payload.get("kv")

        sub_query = sql_query_generator(filter_in, type, pairs, field_selected='platform', return_type='item_id',
                                        limit=None, offset=None)

        where_start = sub_query.find("WHERE")
        from_start = sub_query.find("FROM")

        from_sub = sub_query[from_start:where_start]
        where_sub = sub_query[where_start:]

        query = f"select up.key, up.value, up.is_gcm, count(up.item_id) as count " + from_sub + \
                f" join unified_pair up on it.item_id = up.item_id " + where_sub + \
                f" and lower(up.value) like lower('%{value}%') " \
                f" group by up.key, up.value, up.is_gcm"

        print("Query start")
        res = db.engine.execute(sqlalchemy.text(query)).fetchall()
        print(query)
        results_gcm = []
        results_pairs = []
        for r in res:
            if r['is_gcm']:
                results_gcm.append({'key': r.key, 'value': r.value, 'count': r.count})
            else:
                results_pairs.append({'key': r.key, 'value': r.value, 'count': r.count})
        results = {'gcm': results_gcm, 'pairs': results_pairs}
        return results
