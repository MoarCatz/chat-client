import unittest
from request_handler import RequestHandler
from json_pack import ClientCodes, ServerCodes

cc = ClientCodes
sc = ServerCodes

class RHTest(unittest.TestCase):
    rh = RequestHandler()

    def test_unpack_req(self):
        req1 = self.rh.set_image_code + ',"1","2","3",'.encode() + b'4'
        act1 = self.rh.unpack_req(req1)
        exp1 = (cc.set_image.value, ['1', '2', '3', b'4'])
        self.assertTupleEqual(act1, exp1)

        req2 = b'0,"1",["2","3","4",[]]'
        act2 = self.rh.unpack_req(req2)
        exp2 = (0, ['1', ['2', '3', '4', []]])
        self.assertTupleEqual(act2, exp2)

    def test_unpack_resp(self):
        resp1 = self.rh.profile_info_code + b',"1","2",3,"4",img'
        act1 = self.rh.unpack_resp(resp1)
        exp1 = (sc.profile_info.value, ['1', '2', 3, '4', b'img'])
        self.assertTupleEqual(act1, exp1)

        resp2 = b'0,"1",["2","3","4",[]]'
        act2 = self.rh.unpack_resp(resp2)
        exp2 = (0, ['1', ['2', '3', '4', []]])
        self.assertTupleEqual(act2, exp2)

if __name__ == '__main__':
    unittest.main()
