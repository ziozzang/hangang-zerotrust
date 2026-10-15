import pathlib
import unittest
import bootstrap

class ConfigTests(unittest.TestCase):
    def test_h4_config_fixed_before_first_start(self):
        scope={'service':'orders','audience':'orders-api','application':'app','route':'owned-route','route_revision':11,'destination_sha256':'12'*32,'header_revision':13,'headers':[],'reserved_headers':['x-owned-secret'],'maximum_entity_bytes':16777216}
        tls={'ca':'/private/ca','certificate':'/private/cert','key':'/private/key','server_name':'localhost'}
        cfg=bootstrap.hop_config(pathlib.Path('/private/hop'),dict(portal='127.0.0.1:1',gateway='127.0.0.1:2',grpc='127.0.0.1:3'),tls,'http://127.0.0.1:4',[scope],'https://127.0.0.1:5','public-key')
        self.assertEqual(cfg['receipt_issuer']['human_receipts']['scopes'],[scope])
        self.assertEqual(cfg['projection_receiver']['authority']['address'],'https://127.0.0.1:5')
        self.assertEqual(cfg['projection_receiver']['human_observed_scopes'],[dict(service='orders',audience='orders-api',application='app',route='owned-route')])
        self.assertEqual(cfg['credential_projection']['plans'][0]['minimum_aal'],1)
        self.assertNotIn('authentication_gateway',cfg)
        self.assertNotIn('OWNED_SIGNING',str(cfg))
        scope['route']='mutated'
        self.assertEqual(cfg['receipt_issuer']['human_receipts']['scopes'][0]['route'],'owned-route')

    def test_no_cross_application_implicit_mapping(self):
        with self.assertRaisesRegex(RuntimeError,'hop_application'):
            bootstrap.hop_config(pathlib.Path('/private'),dict(portal='a',gateway='b',grpc='c'),{},'issuer',[{'application':'a'},{'application':'b'}],'pum','key')

if __name__=='__main__':unittest.main()
